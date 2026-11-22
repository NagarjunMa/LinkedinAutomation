"""Deterministic findings and a fail-closed copy gate for uploaded LinkedIn exports."""

import re
from collections.abc import Iterable, Iterator
from itertools import takewhile

from sqlalchemy.orm import Session

from app.application.career_service import CareerApplicationService
from app.application.errors import InvalidOperationError, ResourceConflictError, ResourceNotFoundError
from app.application.evidence_service import EvidenceService
from app.application.evidence_terms import BULLET_PREFIX as _BULLET_PREFIX
from app.application.evidence_terms import CONTRIBUTION_CATEGORIES as _CONTRIBUTION_CATEGORIES
from app.application.evidence_terms import applied_skill, normalized_phrase as _phrase
from app.repositories.career_repository import CareerRepository
from app.schemas.career.common import SourceRef
from app.schemas.career.evidence import CareerEvidenceItem, EvidenceRevisionRef
from app.schemas.career.resume import ProposalRejection
from app.schemas.career.sources import (
    LINKEDIN_PDF_EXTRACTION_VERSION,
    CareerTarget,
    LinkedInDocument,
    LinkedInFinding,
    LinkedInRecommendation,
    LinkedInRecommendationSection,
    LinkedInRecommendationSelection,
    LinkedInReview,
    LinkedInReviewPreview,
    LinkedInSection,
    LinkedInTargetRequirement,
)
from app.schemas.resume_v2 import ResumeDocumentJSON
from app.services.linkedin_pdf import (
    CLAIM, EXPLICIT_HEADLINE_LOCATOR_SUFFIX, LINK, SIDEBAR_LOCATOR_SUFFIX,
)
from app.services.resume.parser import DATE_RANGE_RE

_PROFESSIONAL_SECTIONS = {"headline", "about", "experience", "projects", "skills"}
_PROMINENT_SECTIONS = {"headline", "about"}
_SECTION_LIMITS: dict[LinkedInRecommendationSection, int] = {
    "headline": 120, "about": 500, "experience": 500, "skills": 50,
}
_SKILL_LABEL = re.compile(r"[\w+#][\w.+# /-]*")
_OPTIONS_PER_SECTION = 3
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_NUMBER = re.compile(r"(?<!\w)\d+(?:[,.]\d+)*")
_ESTIMATE_PREFIX = re.compile(r"\b(?:estimated|approximately|roughly|about)\s+(?:[$€£]\s*)?$", re.I)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_DOMAIN = r"(?:[\w-]+\.)+(?:[^\W\d_]{2,}|xn--[a-z0-9-]+)(?::\d+)?"
_BARE_LINK = re.compile(rf"(?<![\w@]){_DOMAIN}[/?#][^\s<>]*", re.I)
_BARE_HOST = re.compile(_DOMAIN, re.I)
_IDNA_DOTS = str.maketrans("。．｡", "...")
_URL_WRAPPERS = " \t\r\n<>()[]{}.,;!?“”‘’«»‹›（）【】" + '"' + "'"
_PROFILE_METADATA = re.compile(
    r"^(?:location|contact|e-?mail|phone|name|date of birth|age|pronouns|gender|nationality|ethnicity|religion"
    r"|website|portfolio|profile(?: url)?|github|linkedin)\s*:",
    re.I,
)
_DATED_CLAIM = re.compile(r"^in (?:19|20)\d{2},?\s+", re.I)
_OWNED_CLAIM = re.compile(r"^(?:I\s+)?(?:owned|oversaw)\b", re.I)
_NO_CAPABILITY_PREFIX = re.compile(
    r"\b(?:without|never|not|no|learning|studying)\s+"
    r"(?:(?:use|using|used|experience|hands-on|working|worked|in|with|on|for|about|the|basics|of)\s+){0,6}$"
)
_NO_CAPABILITY_SUFFIX = re.compile(r"^\s+(?:(?:is|was)\s+)?(?:not|never)\s+(?:used|applied|needed)\b")


class LinkedInReviewService:
    """Review an owner's uploaded export against one selected target."""

    def __init__(self, db: Session, owner: str):
        self.owner = owner
        self.career = CareerApplicationService(db, owner)
        self.sources = CareerRepository(db, owner)
        self.evidence = EvidenceService(db, owner)

    def review(
        self, document: SourceRef, target_id: str, *, evidence_snapshot_version: int,
        requirements: Iterable[LinkedInTargetRequirement] = (), resume_source: SourceRef | None = None,
    ) -> LinkedInReview:
        preview = self.preview(document, target_id, requirements=requirements, resume_source=resume_source)
        return LinkedInReview(**preview.model_dump(), evidence_snapshot_version=evidence_snapshot_version)

    def preview(
        self, document: SourceRef, target_id: str, *, requirements: Iterable[LinkedInTargetRequirement] = (),
        resume_source: SourceRef | None = None,
    ) -> LinkedInReviewPreview:
        target = self._active_target(target_id)
        parsed = self.sources.linkedin_document(self._pdf_source(document))
        if parsed.source != document:
            raise InvalidOperationError("LinkedIn source snapshot does not match the requested revision")

        criteria = sorted(requirements, key=lambda item: item.requirement_id)
        if len({item.requirement_id for item in criteria}) != len(criteria):
            raise InvalidOperationError("Target requirements must have unique IDs")
        items = [item for item in self.evidence.list_eligible() if _eligible(item, self.owner)]

        findings = list(_profile_findings(parsed, target, criteria, items))
        if resume_source is not None:
            resume = self._resume_snapshot(resume_source)
            if parsed.parse_status != "unreadable":
                findings.extend(_chronology_questions(parsed, resume_source, resume))
        return LinkedInReviewPreview(
            schema_version=1, document=document, target_id=target.target_id,
            parser_version=LINKEDIN_PDF_EXTRACTION_VERSION, findings=findings,
        )

    def recommendations(self, document: SourceRef, target_id: str) -> list[LinkedInRecommendation]:
        target = self._active_target(target_id)
        self._pdf_source(document)
        cues = (target.role_family, *target.desired_work)
        items = sorted(
            (item for item in self.evidence.list_eligible() if self._copy_eligible(item)),
            key=lambda item: (not any(_positive_capability(item.claim, cue) for cue in cues), item.evidence_id),
        )
        contributions = [item for item in items if _contribution(item)]
        skills = [item for item in items if _skill(item)]
        applications: dict[str, CareerEvidenceItem] = {}
        for contribution in contributions:
            if capability := applied_skill(contribution.claim):
                applications.setdefault(capability, contribution)
        suggestions = []
        for section in _SECTION_LIMITS:
            options: dict[str, LinkedInRecommendation] = {}
            candidates = skills if section == "skills" else contributions
            for item in candidates:
                if item.claim in options:
                    continue
                selected = [item]
                if section == "skills":
                    application = applications.get(_phrase(item.claim))
                    if application is None:
                        continue
                    selected.append(application)
                suggestion = _render_recommendation(section, selected)
                if suggestion is not None:
                    options[suggestion.text] = suggestion
                if len(options) == _OPTIONS_PER_SECTION:
                    break
            suggestions.extend(options.values())
        return suggestions

    def copy_recommendation(
        self, document: SourceRef, target_id: str, selection: LinkedInRecommendationSelection,
    ) -> LinkedInRecommendation:
        self._active_target(target_id)
        self._pdf_source(document)
        # Read the exact cited revisions together, including the application evidence for a skill.
        items = {
            (item.evidence_id, item.revision): item
            for item in self.evidence.list_eligible(references=selection.evidence_revisions)
            if self._copy_eligible(item)
        }
        ordered = []
        for ref in selection.evidence_revisions:
            item = items.get((ref.evidence_id, ref.revision))
            if item is None:
                raise ResourceConflictError("Recommendation changed. Refresh the review.")
            ordered.append(item)
        suggestion = _render_recommendation(selection.section, ordered)
        if suggestion is None:
            raise ResourceConflictError("Recommendation changed. Refresh the review.")
        return suggestion

    def recommendation_blocker(self, reference: EvidenceRevisionRef, text: str) -> ProposalRejection | None:
        # Recheck the exact current revision whenever a caller asks to use wording.
        item = self.evidence.eligible(reference)
        if item is None or not _eligible(item, self.owner) or _ref(item) != reference:
            return "evidence_not_confirmed"
        return _wording_blocker(item, text)

    def _copy_eligible(self, item: CareerEvidenceItem) -> bool:
        return _eligible(item, self.owner) and _wording_blocker(item, item.claim) is None

    def _active_target(self, target_id: str) -> CareerTarget:
        target = self.career.get_target(target_id)
        if target.owner_id != self.owner or target.status != "active":
            raise ResourceNotFoundError("Active target not found")
        return target

    def _pdf_source(self, document: SourceRef):
        source = self.sources.get_source(document)
        if source is None or source.kind != "linkedin_profile_pdf" or source.extraction_version != LINKEDIN_PDF_EXTRACTION_VERSION:
            raise ResourceNotFoundError("LinkedIn PDF not found")
        return source

    def _resume_snapshot(self, reference: SourceRef) -> ResumeDocumentJSON:
        source = self.sources.get_source(reference)
        if source is None or source.kind != "resume" or source.resume_document_id is None:
            raise ResourceNotFoundError("Résumé source not found")
        resume = self.sources.ready_resume(source.resume_document_id)
        if resume is None:
            raise ResourceNotFoundError("Résumé source not found")
        return ResumeDocumentJSON.model_validate(resume.parsed_json)


def _eligible(item: CareerEvidenceItem, owner: str) -> bool:
    return item.owner_id == owner and item.lifecycle == "confirmed" and not item.is_private


def _ref(item: CareerEvidenceItem) -> EvidenceRevisionRef:
    return EvidenceRevisionRef(evidence_id=item.evidence_id, revision=item.revision)


def _wording_blocker(item: CareerEvidenceItem, text: str) -> ProposalRejection | None:
    if text != item.claim:
        return "proposal_rejected"
    # Shared work needs an attribution-aware plan before it is safe to copy verbatim.
    if item.ownership != "individual":
        return "ownership_upgrade"
    if any(not _contains(text, qualifier) for qualifier in item.qualifiers):
        return "qualifier_removed"
    numbers = list(_NUMBER.finditer(text))
    if numbers and item.measurement is None:
        return "number_not_approved"
    if item.measurement and item.measurement.estimated and any(
        not _ESTIMATE_PREFIX.search(text[:number.start()]) for number in numbers
    ):
        return "qualifier_removed"
    return None


def _contribution(item: CareerEvidenceItem) -> bool:
    return (item.category in _CONTRIBUTION_CATEGORIES
            and (_action_claim(item.claim) or bool(applied_skill(item.claim))))


def _skill(item: CareerEvidenceItem) -> bool:
    return (item.category == "skill" and len(item.claim) <= _SECTION_LIMITS["skills"]
            and _SKILL_LABEL.fullmatch(item.claim) is not None)


def _render_recommendation(
    section: LinkedInRecommendationSection, items: list[CareerEvidenceItem],
) -> LinkedInRecommendation | None:
    item = items[0]
    if len(item.claim) > _SECTION_LIMITS[section]:
        return None
    if section == "skills":
        application = items[1]
        if not (_skill(item) and _contribution(application) and applied_skill(application.claim) == _phrase(item.claim)):
            return None
    elif not _contribution(item) or (section == "headline" and len(item.claim.splitlines()) != 1):
        return None
    return LinkedInRecommendation(section=section, text=item.claim, evidence_revisions=[_ref(entry) for entry in items])


def _term_matches(text: str, term: str) -> Iterator[re.Match[str]]:
    needle = _phrase(term)
    if not needle:
        return iter(())
    return re.finditer(r"(?<![\w+#.])" + re.escape(needle) + r"(?![\w+#]|\.[\w-])", _phrase(text))


def _contains(text: str, term: str) -> bool:
    return next(_term_matches(text, term), None) is not None


def _action_claim(text: str) -> bool:
    statement = _DATED_CLAIM.sub("", _BULLET_PREFIX.sub("", text.strip()))
    return bool(CLAIM.match(statement) or _OWNED_CLAIM.match(statement))


def _professional_text(text: str) -> str:
    normalized = text.translate(_IDNA_DOTS)
    cleaned = _BARE_LINK.sub(" ", LINK.sub(" ", _EMAIL.sub(" ", normalized)))
    return cleaned if cleaned.strip(_URL_WRAPPERS) else ""


def _host_only(text: str) -> bool:
    return _BARE_HOST.fullmatch(text.strip(_URL_WRAPPERS)) is not None


def _positive_capability(text: str, term: str) -> bool:
    text = _professional_text(text)
    # A whole dotted label may be a skill, but a hostname cannot supply a partial match.
    if _host_only(text):
        return _phrase(text) == _phrase(term)
    return any(
        not _NO_CAPABILITY_PREFIX.search(match.string[:match.start()])
        and not _NO_CAPABILITY_SUFFIX.match(match.string[match.end():])
        for match in _term_matches(text, term)
    )


def _listed_skills(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,;•]", _professional_text(text)) if part.strip()]


def _section_has_capability(section: LinkedInSection, term: str) -> bool:
    if section.name == "skills":
        return any(_phrase(skill) == _phrase(term) for skill in _listed_skills(section.text))
    return _positive_capability(section.text, term)


def _profile_findings(
    document: LinkedInDocument, target: CareerTarget,
    criteria: list[LinkedInTargetRequirement], evidence: list[CareerEvidenceItem],
) -> Iterator[LinkedInFinding]:
    # Old flattened sidebars lack proof of where the header ends and skills begin.
    preamble = list(takewhile(
        lambda section: section.page == 1 and section.name not in {"about", "experience", "projects", "education"},
        document.sections,
    ))
    ambiguous_preamble = (
        (any(section.name == "contact" for section in preamble) or document.raw_text.lstrip().casefold().startswith("contact\n"))
        and not any(section.locator.endswith(SIDEBAR_LOCATOR_SUFFIX) for section in preamble)
    )
    notice = (
        "The review omits the header and sidebar of this uploaded export because their boundary could not be established."
        if ambiguous_preamble else
        "This review checks identifiable statements in the uploaded export. It omits inferred headlines and may miss other wording."
    )
    yield LinkedInFinding(kind="document_limit", document_locator="export", explanation=notice)
    if document.parse_status == "unreadable":
        return

    suppressed = {section.locator for section in preamble} if ambiguous_preamble else set()
    sections = []
    has_headline = False
    for section in document.sections:
        if section.locator in suppressed:
            continue
        text = _professional_text(section.text).strip()
        if section.name not in _PROFESSIONAL_SECTIONS or not text:
            continue
        if _PROFILE_METADATA.match(text):
            continue
        if section.locator.endswith(SIDEBAR_LOCATOR_SUFFIX) and section.name != "skills":
            continue
        if section.name != "skills" and _host_only(text):
            continue
        if section.name in {"experience", "projects"} and not _action_claim(text):
            continue
        # Position alone does not distinguish an optional headline from a location.
        if section.name == "headline":
            if has_headline or not section.locator.endswith(EXPLICIT_HEADLINE_LOCATOR_SUFFIX):
                continue
            has_headline = True
        sections.append(section)
    prominent = [section for section in sections if section.name in _PROMINENT_SECTIONS]
    exact_claims: dict[str, list[CareerEvidenceItem]] = {}
    for item in evidence:
        exact_claims.setdefault(_phrase(item.claim), []).append(item)

    for section in sections:
        if section.name != "skills" and _action_claim(section.text):
            matches = exact_claims.get(_phrase(section.text), [])
            if not matches:
                yield LinkedInFinding(
                    kind="unsupported_claim", document_locator=section.locator,
                    explanation="No exact confirmed evidence matches this statement. Review its wording and details.",
                )
            elif all(item.ownership == "unknown" for item in matches):
                yield LinkedInFinding(
                    kind="ambiguous_claim", document_locator=section.locator, evidence_revisions=[_ref(i) for i in matches],
                    explanation="What was your specific contribution to the work described here?",
                )
        elif section.name == "skills":
            for skill in _listed_skills(section.text):
                matches = [item for item in evidence if _positive_capability(item.claim, skill)]
                if not matches or all(item.support == "candidate_statement" for item in matches):
                    yield LinkedInFinding(
                        kind="evidence_gap", document_locator=section.locator, evidence_revisions=[_ref(i) for i in matches],
                        explanation="A listed skill would benefit from a confirmed example or stronger supporting evidence.",
                    )
                    break

    for criterion in criteria:
        matches = [
            item for item in evidence if _positive_capability(item.claim, criterion.capability)
            and (not criterion.learning_only or _action_claim(item.claim))
        ]
        refs = [_ref(item) for item in matches]
        anchors = [section for section in sections if _section_has_capability(section, criterion.capability)]
        if not refs:
            yield LinkedInFinding(
                kind="knowledge_gap" if criterion.learning_only else "experience_gap",
                target_requirement_id=criterion.requirement_id,
                explanation="The selected capability has no matching confirmed experience in the evidence reviewed.",
            )
        elif not anchors:
            yield LinkedInFinding(
                kind="communication_gap", target_requirement_id=criterion.requirement_id, evidence_revisions=refs,
                explanation="Relevant confirmed evidence was not found in the comparable sections of the uploaded export.",
            )
        elif prominent and all(section.name not in _PROMINENT_SECTIONS for section in anchors):
            yield LinkedInFinding(
                kind="weak_prominence", document_locator=anchors[0].locator,
                target_requirement_id=criterion.requirement_id, evidence_revisions=refs,
                explanation="The selected capability appears in the export, but not in its available headline or About section.",
            )

    if prominent and not any(_positive_capability(section.text, target.role_family) for section in prominent):
        yield LinkedInFinding(
            kind="positioning_gap", document_locator=prominent[0].locator,
            explanation="Consider making the selected role clearer in the available headline or About section.",
        )


def _chronology_questions(
    document: LinkedInDocument, resume_source: SourceRef, resume: ResumeDocumentJSON,
) -> Iterator[LinkedInFinding]:
    for role in document.experience:
        if not role.company or not role.title:
            continue
        employer = _phrase(role.company)
        same_employer = [(i, job) for i, job in enumerate(resume.experience) if _phrase(job.company) == employer]
        # Multiple roles at one employer need a more reliable match than employer alone.
        if len(same_employer) != 1 or sum(_phrase(entry.company or "") == employer for entry in document.experience) != 1:
            continue
        index, position = same_employer[0]
        dates = DATE_RANGE_RE.fullmatch((position.dates or "").strip())
        pdf_period = (_year(role.start_date), _year(role.end_date))
        resume_period = (
            tuple(_year(part) for part in re.split(r"[-–—]", dates["dates"], maxsplit=1)) if dates else (None, None)
        )
        title_differs = bool(position.role.strip()) and _phrase(role.title) != _phrase(position.role)
        years_differ = any(a and b and a != b for a, b in zip(pdf_period, resume_period))
        if title_differs or years_differ:
            yield LinkedInFinding(
                kind="consistency_question", document_locator=role.locator,
                resume_source=resume_source, resume_locator=f"experience:{index}",
                explanation="Which role title and dates should we use for this employer?",
            )


def _year(value: str | None) -> str | None:
    if _phrase(value or "") in {"present", "current", "now"}:
        return "present"
    match = _YEAR.search(value or "")
    return match[0] if match else None
