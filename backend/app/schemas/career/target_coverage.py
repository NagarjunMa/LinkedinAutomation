"""Read-only target coverage and its exact evidence citations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from .common import CareerContract, Identifier, Label
from .evidence import EvidenceRevisionRef, EvidenceSupport

TargetCoverageState = Literal["supported", "evidence_gap", "knowledge_gap", "experience_gap"]
TargetCoverageReason = Literal[
    "confirmed_application", "application_scope_unclear", "skill_without_application",
    "learning_only", "no_matching_confirmed_evidence",
]


class TargetFocusCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: Label
    state: TargetCoverageState
    reason_code: TargetCoverageReason
    evidence: EvidenceRevisionRef | None
    evidence_support: EvidenceSupport | None


class TargetRoleCoverage(CareerContract):
    target_id: Identifier
    policy_version: Literal["target-coverage-v1"]
    focus: list[TargetFocusCoverage]
    positioning_reason: Literal["target_focus_missing"] | None
