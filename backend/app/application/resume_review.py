"""Deterministic résumé findings over approved evidence and local file checks."""

from app.application.evidence_terms import normalized_phrase
from app.application.target_coverage import project_target_resume_coverage
from app.schemas.career.common import SourceRef
from app.schemas.career.evidence import CareerEvidenceItem
from app.schemas.career.resume import GroundedResumeReview, ResumePolicyProfile, ResumeRequirementFinding
from app.schemas.career.sources import CareerTarget
from app.schemas.resume_v2 import ResumeDocumentJSON
from app.services.resume.ats_simulator import ATSResult


_POLICY = ResumePolicyProfile(
    schema_version=1, profile_id="universal", policy_version="resume-review-v1",
    universal_rules_version="resume-review-v1", market_overlay="universal", page_limit=2,
)


def project_resume_review(
    document_id: str, resume: ResumeDocumentJSON, version_id: str | None, document_check: ATSResult,
    target: CareerTarget | None, evidence: list[CareerEvidenceItem], *, target_role: str | None = None,
) -> GroundedResumeReview:
    findings: list[ResumeRequirementFinding] = []
    source = SourceRef(source_id=document_id, source_version=1)
    version_locator = f"version:{version_id}" if version_id else "Original upload"

    def add(category, code, explanation, action, *, locator=None, evidence_ref=None, focus_label=None, severity="warning"):
        findings.append(ResumeRequirementFinding(
            schema_version=1, finding_id=f"{category}-{len(findings) + 1}",
            category=category, severity=severity, blocking=False, reason_code=code,
            policy_profile_id=_POLICY.profile_id, rule_version=_POLICY.policy_version,
            source=source if locator else None, source_locator=locator,
            focus_label=focus_label,
            evidence_revisions=[evidence_ref] if evidence_ref else [],
            explanation=explanation, next_action=action,
        ))

    if target and evidence:
        comparison = project_target_resume_coverage(target, evidence, document_id, resume)
        revisions = {(item.evidence_id, item.revision): item for item in evidence}
        missing = {item.focus_label for item in comparison.findings if item.kind == "communication_gap"}
        for focus in comparison.coverage.focus:
            ref = focus.evidence
            if ref is None:
                continue
            if focus.reason_code == "application_scope_unclear":
                add("defensibility", "ownership_needs_clarification",
                    "The cited evidence leaves your personal contribution unclear.",
                    "Record what you personally did and what the team delivered.",
                    evidence_ref=ref, focus_label=focus.label)
            if focus.state != "supported":
                continue
            add("evidence", "confirmed_application",
                "Confirmed evidence supports this target focus.",
                "Review the cited revision before using it in your résumé.",
                evidence_ref=ref, focus_label=focus.label, severity="info")
            if focus.label in missing:
                add("communication", "confirmed_application_not_found_in_resume",
                    "The cited claim had no exact match in the parsed experience or project bullets.",
                    "Check whether an existing bullet already conveys it or revise the relevant bullet.",
                    evidence_ref=ref, focus_label=focus.label)
            if revisions[(ref.evidence_id, ref.revision)].ownership != "individual":
                add("defensibility", "ownership_needs_clarification",
                    "The cited evidence does not establish sole ownership.",
                    "Describe your own contribution and keep any team outcome attributed to the team.",
                    evidence_ref=ref, focus_label=focus.label)

    mode = "evidence_grounded" if findings else "document_only"
    comparable = False
    for section, entries in (("Experience", resume.experience), ("Projects", resume.projects)):
        for entry_number, entry in enumerate(entries, 1):
            for bullet_number, bullet in enumerate(entry.bullets, 1):
                text = normalized_phrase(bullet.text)
                comparable |= any(character.isalpha() for character in text)
                if text.startswith(("responsible for ", "duties included ", "tasked with ")):
                    add("communication", "responsibility_only_bullet",
                        "This bullet opens with a responsibility. Show what you personally did earlier in the sentence.",
                        "Lead with a specific action from your experience and add a verifiable result if available.",
                        locator=f"{version_locator} / {section} entry {entry_number} / bullet {bullet_number}")
    if not comparable:
        add("document_limit", "document_limit", "No comparable experience or project bullets were parsed.",
            "Review the uploaded résumé or saved version before drawing conclusions about what it communicates.",
            locator=f"{version_locator} / experience and projects", severity="info")
    if not document_check.raw_text.strip():
        add("parseability", "parser_field_missing", "PrismPro could not extract readable text from the uploaded file.",
            "Upload a text-based PDF or DOCX and check its extracted text.", locator="Original upload")
    for issue in document_check.observed_format_issues:
        if issue.type == "multi_column":
            add("formatting", "reading_order_failed",
                "PrismPro extracted text from both columns on the same lines.",
                "Check the extracted text in order. Try a single-column layout if it mixes separate sections.",
                locator=f"Original upload / {issue.location}")
            continue
        explanation = (
            f"PrismPro extracted no text from this page, which contains {issue.type.replace('_', ' ')} layout."
            if issue.location.startswith("page ") else "Some table text did not appear in the local extraction."
        )
        add("formatting", "layout_check",
            explanation,
            "Check the original file against the extracted text. Simplify the layout if information is missing.",
            locator=f"Original upload / {issue.location}")
    if document_check.page_count is not None and document_check.page_count > _POLICY.page_limit:
        add("document_limit", "document_limit",
            f"The uploaded PDF has {document_check.page_count} pages, above this profile's {_POLICY.page_limit}-page guideline.",
            "Review length and readability for the role before removing relevant evidence.",
            locator="Original upload", severity="info")
    return GroundedResumeReview(
        schema_version=1, policy=_POLICY, mode=mode, target_id=target.target_id if target else None,
        target_role=target.role_family if target else (target_role or "").strip() or None,
        resume_version_id=version_id, findings=findings,
    )
