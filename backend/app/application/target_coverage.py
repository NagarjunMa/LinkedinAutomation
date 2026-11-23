"""Project current evidence onto the focus areas of a single career target."""

from bisect import insort
from collections import Counter
from collections.abc import Iterable
from functools import partial
from itertools import chain
from typing import NamedTuple, get_args

from app.application.evidence_terms import CONTRIBUTION_CATEGORIES, applied_skill, normalized_phrase
from app.schemas.career.evidence import CareerEvidenceItem, EvidenceRevisionRef
from app.schemas.career.sources import CareerTarget
from app.schemas.career.target_coverage import (
    CoverageScope, ResumeCoverageFinding, SelectionCriterion, SelectionReason, TargetCoverageDetails,
    TargetCoverageReason, TargetCoverageState, TargetEvidenceAlternative, TargetEvidenceSelection,
    TargetFocusCoverage, TargetFocusExplanation, TargetLevel, TargetResumeCoverage, TargetRoleCoverage,
    TargetScopeAlignment,
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
_SCOPE_ORDER = {scope: index for index, scope in enumerate(get_args(CoverageScope))}
_SCOPE_LABELS = {scope.replace("_", " "): scope for scope in _SCOPE_ORDER}
_TARGET_LEVELS = {level: level for level in get_args(TargetLevel)} | {"entry level": "entry", "mid level": "mid"}
_MAX_ALTERNATIVES = 5
_SELECTION_EXPLANATIONS: dict[SelectionReason, str] = {
    "no_matching_evidence": "No eligible evidence matched this focus.",
    "only_matching_evidence": "This was the only eligible evidence that matched this focus.",
    "coverage_signal_priority": "The selected evidence provides a stronger coverage signal for this focus.",
    "scope_meets_requirement": "The selected evidence records scope that meets the requested requirement.",
    "stable_id_tiebreak": "The leading candidates tied on the applicable criteria. A stable identifier resolved the tie.",
}


class _Match(NamedTuple):
    reason: TargetCoverageReason
    item: CareerEvidenceItem
    scope: CoverageScope | None

    def reference(self) -> EvidenceRevisionRef:
        return EvidenceRevisionRef(evidence_id=self.item.evidence_id, revision=self.item.revision)


def project_target_coverage(
    target: CareerTarget, evidence: Iterable[CareerEvidenceItem], *,
    explain: bool = False, required_scope: CoverageScope | None = None,
) -> TargetRoleCoverage:
    coverage, _ = _project(target, evidence, explain=explain, required_scope=required_scope)
    return coverage


def project_target_resume_coverage(
    target: CareerTarget, evidence: Iterable[CareerEvidenceItem],
    resume_document_id: str, resume: ResumeDocumentJSON | None, *,
    explain: bool = False, required_scope: CoverageScope | None = None,
) -> TargetResumeCoverage:
    # shortcut: match whole parsed action bullets until reliable claim-to-document links exist.
    displayed_claims = {
        text
        for entry in chain(resume.experience, resume.projects)
        for bullet in entry.bullets
        if (text := normalized_phrase(bullet.text)) and any(character.isalpha() for character in text)
    } if resume else set()
    coverage, displayed_focus = _project(
        target, evidence, displayed_claims, explain=explain, required_scope=required_scope,
    )
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
    target: CareerTarget, evidence: Iterable[CareerEvidenceItem], displayed_claims: set[str] | None = None, *,
    explain: bool, required_scope: CoverageScope | None,
) -> tuple[TargetRoleCoverage, set[str]]:
    labels: dict[str, str] = {}
    for label in target.desired_work:
        if normalized := normalized_phrase(label):
            labels.setdefault(normalized, label)

    include_details = explain or required_scope is not None
    keep = _MAX_ALTERNATIVES + 1 if include_details else 1
    rank = partial(_order, required_scope=required_scope)
    matches: dict[str, list[_Match]] = {}
    match_counts: Counter[str] = Counter()
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
        scope = _SCOPE_LABELS.get(_label_key(item.scope)) if include_details and reason == "confirmed_application" else None
        candidates = matches.setdefault(capability, [])
        insort(candidates, _Match(reason, item, scope), key=rank)
        if len(candidates) > keep:
            candidates.pop()
        match_counts[capability] += 1

    coverage = []
    explanations = []
    for capability, label in labels.items():
        candidates = matches.get(capability, [])
        match = candidates[0] if candidates else None
        reason = match.reason if match else "no_matching_confirmed_evidence"
        coverage.append(TargetFocusCoverage(
            label=label, state=_STATES[reason], reason_code=reason,
            evidence=match.reference() if match else None,
            evidence_support=match.item.support if match else None,
        ))
        if include_details:
            explanations.append(_explain(label, candidates, match_counts[capability], required_scope))

    projection = TargetRoleCoverage(
        schema_version=1, target_id=target.target_id,
        policy_version="target-coverage-v2" if include_details else "target-coverage-v1",
        focus=coverage, positioning_reason=None if labels else "target_focus_missing",
    )
    if include_details:
        criteria: list[SelectionCriterion] = ["coverage_signal_priority"]
        if required_scope is not None:
            criteria.append("scope_meets_requirement")
        criteria.append("stable_id_tiebreak")
        projection.details = TargetCoverageDetails(
            target_level=_TARGET_LEVELS.get(_label_key(target.seniority)),
            required_scope=required_scope, ordered_criteria=criteria, focus=explanations,
        )
    return projection, displayed_focus


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


def _label_key(value: str | None) -> str:
    return " ".join((value or "").casefold().replace("-", " ").replace("_", " ").split())


def _meets_scope(observed: CoverageScope | None, required: CoverageScope | None) -> bool:
    return observed is not None and required is not None and _SCOPE_ORDER[observed] >= _SCOPE_ORDER[required]


def _order(match: _Match, *, required_scope: CoverageScope | None) -> tuple[int, bool, str, int]:
    return (
        _REASON_ORDER[match.reason], not _meets_scope(match.scope, required_scope),
        match.item.evidence_id, match.item.revision,
    )


def _decisive_criterion(winner: _Match, other: _Match, required_scope: CoverageScope | None) -> SelectionCriterion:
    if winner.reason != other.reason:
        return "coverage_signal_priority"
    if _meets_scope(winner.scope, required_scope) != _meets_scope(other.scope, required_scope):
        return "scope_meets_requirement"
    return "stable_id_tiebreak"


def _explain(
    label: str, candidates: list[_Match], match_count: int, required_scope: CoverageScope | None,
) -> TargetFocusExplanation:
    winner = candidates[0] if candidates else None
    observed_scope = winner.scope if winner else None
    if required_scope is None:
        scope = TargetScopeAlignment(state="requirement_unspecified", observed_scope=observed_scope)
    elif observed_scope is None:
        scope = TargetScopeAlignment(state="unavailable", observed_scope=None)
    else:
        state = "meets_requirement" if _meets_scope(observed_scope, required_scope) else "below_requirement"
        scope = TargetScopeAlignment(state=state, observed_scope=observed_scope)

    alternatives = [
        TargetEvidenceAlternative(evidence=candidate.reference(),
                                  reason_code=_decisive_criterion(winner, candidate, required_scope))
        for candidate in candidates[1:]
    ] if winner else []
    reason: SelectionReason = "no_matching_evidence"
    if winner:
        reason = alternatives[0].reason_code if alternatives else "only_matching_evidence"
    return TargetFocusExplanation(
        label=label, scope=scope,
        selection=TargetEvidenceSelection(
            selected=winner.reference() if winner else None,
            reason_code=reason, explanation=_SELECTION_EXPLANATIONS[reason],
            alternatives=alternatives, alternative_count=max(0, match_count - 1),
        ),
    )
