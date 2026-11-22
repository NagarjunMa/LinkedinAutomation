"""Project current evidence onto the focus areas of a single career target."""

from collections.abc import Iterable

from app.application.evidence_terms import CONTRIBUTION_CATEGORIES, applied_skill, normalized_phrase
from app.schemas.career.evidence import CareerEvidenceItem, EvidenceRevisionRef
from app.schemas.career.sources import CareerTarget
from app.schemas.career.target_coverage import (
    TargetCoverageReason, TargetCoverageState, TargetFocusCoverage, TargetRoleCoverage,
)

_STATES: dict[TargetCoverageReason, TargetCoverageState] = {
    "confirmed_application": "supported",
    "application_scope_unclear": "evidence_gap",
    "skill_without_application": "evidence_gap",
    "learning_only": "knowledge_gap",
    "no_matching_confirmed_evidence": "experience_gap",
}
_REASON_ORDER = {reason: index for index, reason in enumerate(_STATES)}


def project_target_coverage(target: CareerTarget, evidence: Iterable[CareerEvidenceItem]) -> TargetRoleCoverage:
    labels: dict[str, str] = {}
    for label in target.desired_work:
        if normalized := normalized_phrase(label):
            labels.setdefault(normalized, label)

    matches: dict[str, tuple[TargetCoverageReason, CareerEvidenceItem]] = {}
    for item in evidence:
        if item.owner_id != target.owner_id or item.lifecycle != "confirmed" or item.is_private:
            continue
        signal = _evidence_signal(item)
        if signal is None:
            continue
        capability, reason = signal
        if capability not in labels:
            continue
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
    )


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
