"""Build interview preparation from the exact ledger revisions selected by the JD mapping."""

from app.schemas.career.defensibility import (
    ApplicationGuidance, DefensibilityRequirement, DefensibleClaim, EvidenceUnknown, TargetDefensibility,
)
from app.schemas.career.evidence import CareerEvidenceItem
from app.schemas.career.jd_mapping import JDRequirementMapping, TargetJDMapping


def project_target_defensibility(
    owner: str, mapping: TargetJDMapping, eligible: list[CareerEvidenceItem],
) -> TargetDefensibility:
    # In production these are the same current, source-checked records used to build the mapping.
    by_revision = {
        (item.evidence_id, item.revision): item for item in eligible
        if item.owner_id == owner and item.lifecycle == "confirmed" and not item.is_private
    }
    requirements = [
        _requirement(row, by_revision.get((row.evidence.evidence_id, row.evidence.revision)) if row.evidence else None)
        for row in mapping.requirements
    ]
    required = [row for row in requirements if row.priority == "must_have"]
    guidance: ApplicationGuidance
    if not required:
        guidance = "insufficient_requirements"
    elif any(row.state not in ("supported", "communication_gap") for row in required):
        guidance = "review_required_gaps"
    else:
        guidance = "prepare_with_evidence"
    return TargetDefensibility(
        schema_version=1, owner_id=owner, target_id=mapping.target_id,
        jd_evaluation_id=mapping.jd_evaluation_id, jd_text_sha256=mapping.jd_text_sha256,
        resume_comparable=mapping.resume_comparable, guidance=guidance, requirements=requirements,
    )


def _requirement(row: JDRequirementMapping, item: CareerEvidenceItem | None) -> DefensibilityRequirement:
    state = "unresolved" if row.evidence and item is None else row.state
    claim = None
    unknowns: list[EvidenceUnknown] = []
    questions: list[str] = []
    if item and row.evidence:
        claim = DefensibleClaim(
            evidence=row.evidence, text=item.claim, support=item.support, ownership=item.ownership,
            scope=item.scope, measurement=item.measurement, qualifiers=item.qualifiers,
        )
        if item.ownership == "unknown":
            unknowns.append("ownership")
        questions.append("What did you personally deliver, and who contributed to the rest?"
                         if item.ownership != "individual" else
                         "What did you personally deliver, and how did you validate it?")
        if item.measurement is None:
            unknowns.append("measurement")
            questions.append("What outcome can you substantiate, and how would you measure it?")
        else:
            questions.append("How did you measure the result, and what does the measurement cover?")
    else:
        unknowns.append("evidence")
    if row.reason_code in ("additional_qualification_unverified", "qualification_unresolved"):
        unknowns.append("qualification")
    if row.follow_up:
        questions.append(row.follow_up)
    elif claim is None:
        questions.append("What experience or source could clarify this requirement?")
    return DefensibilityRequirement(
        requirement=row.requirement, priority=row.priority, kind=row.kind, state=state,
        claim=claim, unknowns=unknowns, questions=questions,
    )
