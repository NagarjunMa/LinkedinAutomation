"""Project current evidence onto the focus areas of a single career target."""

from collections.abc import Iterable
from itertools import chain

from app.application.evidence_terms import CONTRIBUTION_CATEGORIES, applied_skill, normalized_phrase
from app.schemas.career.evidence import CareerEvidenceItem, EvidenceRevisionRef
from app.schemas.career.sources import CareerTarget
from app.schemas.career.target_coverage import (
    ResumeCoverageFinding, TargetCoverageReason, TargetCoverageState, TargetFocusCoverage, TargetResumeCoverage,
    TargetRoleCoverage,
)
from app.schemas.resume_v2 import ResumeDocumentJSON

_STATES: dict[TargetCoverageReason, TargetCoverageState] = {
    "confirmed_application": "supported",
    "application_scope_unclear": "evidence_gap",
    "skill_without_application": "evidence_gap",
    "learning_only": "knowledge_gap",
    "no_matching_confirmed_evidence": "experience_gap",
}
_REASON_ORDER = {reason: index for index, reason in enumerate(_STATES)}


def project_target_coverage(target: CareerTarget, evidence: Iterable[CareerEvidenceItem]) -> TargetRoleCoverage:
    coverage, _ = _project(target, evidence)
    return coverage


def project_target_resume_coverage(
    target: CareerTarget, evidence: Iterable[CareerEvidenceItem],
    resume_document_id: str, resume: ResumeDocumentJSON | None,
) -> TargetResumeCoverage:
    # shortcut: match whole parsed action bullets until reliable claim-to-document links exist.
    displayed_claims = {
        text
        for entry in chain(resume.experience, resume.projects)
        for bullet in entry.bullets
        if (text := normalized_phrase(bullet.text)) and any(character.isalpha() for character in text)
    } if resume else set()
    coverage, displayed_focus = _project(target, evidence, displayed_claims)
    if displayed_claims:
        findings = [
            ResumeCoverageFinding(
                kind="communication_gap", reason_code="confirmed_application_not_found_in_resume",
                focus_label=focus.label, evidence=focus.evidence,
                explanation="The cited claim did not appear as an exact match in the parsed experience or project bullets.",
            )
            for focus in coverage.focus
            if focus.state == "supported" and normalized_phrase(focus.label) not in displayed_focus
        ]
    else:
        findings = [ResumeCoverageFinding(
            kind="document_limit", reason_code="resume_comparable_bullets_unavailable",
            focus_label=None, evidence=None,
            explanation="No comparable experience or project bullets are available in this parsed résumé.",
        )]
    return TargetResumeCoverage(
        schema_version=1, resume_document_id=resume_document_id, coverage=coverage, findings=findings,
    )


def _project(
    target: CareerTarget, evidence: Iterable[CareerEvidenceItem], displayed_claims: set[str] | None = None,
) -> tuple[TargetRoleCoverage, set[str]]:
    labels: dict[str, str] = {}
    for label in target.desired_work:
        if normalized := normalized_phrase(label):
            labels.setdefault(normalized, label)

    matches: dict[str, tuple[TargetCoverageReason, CareerEvidenceItem]] = {}
    displayed_focus: set[str] = set()
    for item in evidence:
        if item.owner_id != target.owner_id or item.lifecycle != "confirmed" or item.is_private:
            continue
        signal = _evidence_signal(item)
        if signal is None:
            continue
        capability, reason = signal
        if capability not in labels:
            continue
        if displayed_claims and reason == "confirmed_application" and normalized_phrase(item.claim) in displayed_claims:
            displayed_focus.add(capability)
        current = matches.get(capability)
        if current is None or _order(reason, item) < _order(*current):
            matches[capability] = (reason, item)

    coverage = []
    for capability, label in labels.items():
        match = matches.get(capability)
        reason = match[0] if match else "no_matching_confirmed_evidence"
        item = match[1] if match else None
        coverage.append(TargetFocusCoverage(
            label=label, state=_STATES[reason], reason_code=reason,
            evidence=EvidenceRevisionRef(evidence_id=item.evidence_id, revision=item.revision) if item else None,
            evidence_support=item.support if item else None,
        ))
    return TargetRoleCoverage(
        schema_version=1, target_id=target.target_id, policy_version="target-coverage-v1",
        focus=coverage, positioning_reason=None if labels else "target_focus_missing",
    ), displayed_focus


def _evidence_signal(item: CareerEvidenceItem) -> tuple[str, TargetCoverageReason] | None:
    if item.category in CONTRIBUTION_CATEGORIES and (capability := applied_skill(item.claim)):
        attributed = item.ownership == "individual" or (
            item.ownership in {"team", "shared"} and normalized_phrase(item.claim).startswith("i used ")
        )
        return capability, "confirmed_application" if attributed else "application_scope_unclear"
    claim = normalized_phrase(item.claim)
    # Editing and reconfirming a claim preserves its original category.
    for prefix in ("i am learning ", "i am studying "):
        if claim.startswith(prefix):
            return claim.removeprefix(prefix), "learning_only"
    if item.category == "skill":
        return claim, "skill_without_application"
    return None


def _order(reason: TargetCoverageReason, item: CareerEvidenceItem) -> tuple[int, str, int]:
    return _REASON_ORDER[reason], item.evidence_id, item.revision
