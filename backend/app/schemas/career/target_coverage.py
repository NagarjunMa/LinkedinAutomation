"""Read-only target coverage and its exact evidence citations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import CareerContract, Count, Identifier, Label, Text
from .evidence import EvidenceRevisionRef, EvidenceSupport

TargetCoverageState = Literal["supported", "evidence_gap", "knowledge_gap", "experience_gap"]
TargetCoverageReason = Literal[
    "confirmed_application", "application_scope_unclear", "skill_without_application",
    "learning_only", "no_matching_confirmed_evidence",
]
TargetLevel = Literal["intern", "entry", "junior", "mid", "senior", "staff", "principal"]
CoverageScope = Literal["component", "team", "cross_team", "organization"]
SelectionCriterion = Literal["coverage_signal_priority", "scope_meets_requirement", "stable_id_tiebreak"]
SelectionReason = SelectionCriterion | Literal["only_matching_evidence", "no_matching_evidence"]


class TargetFocusCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: Label
    state: TargetCoverageState
    reason_code: TargetCoverageReason
    evidence: EvidenceRevisionRef | None
    evidence_support: EvidenceSupport | None


class TargetScopeAlignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["requirement_unspecified", "unavailable", "meets_requirement", "below_requirement"]
    observed_scope: CoverageScope | None


class TargetEvidenceAlternative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence: EvidenceRevisionRef
    reason_code: SelectionCriterion


class TargetEvidenceSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected: EvidenceRevisionRef | None
    reason_code: SelectionReason
    explanation: Text
    alternatives: list[TargetEvidenceAlternative]
    alternative_count: Count = Field(description="Total eligible alternatives, including any omitted from the displayed list.")


class TargetFocusExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: Label
    scope: TargetScopeAlignment
    selection: TargetEvidenceSelection


class TargetCoverageDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_level: TargetLevel | None = Field(description="Recognized saved target level. This does not describe the candidate's level.")
    required_scope: CoverageScope | None
    ordered_criteria: list[SelectionCriterion]
    focus: list[TargetFocusExplanation]


class TargetRoleCoverage(CareerContract):
    target_id: Identifier
    policy_version: Literal["target-coverage-v1", "target-coverage-v2"]
    focus: list[TargetFocusCoverage]
    positioning_reason: Literal["target_focus_missing"] | None
    details: TargetCoverageDetails | None = None


class ResumeCoverageFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["communication_gap", "document_limit"]
    reason_code: Literal["confirmed_application_not_found_in_resume", "resume_comparable_bullets_unavailable"]
    focus_label: Label | None
    evidence: EvidenceRevisionRef | None
    explanation: Text


class TargetResumeCoverage(CareerContract):
    resume_document_id: Identifier
    coverage: TargetRoleCoverage
    findings: list[ResumeCoverageFinding]
