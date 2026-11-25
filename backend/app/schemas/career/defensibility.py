"""Candidate-facing proof and unknowns for a saved job analysis."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from .common import CareerContract, Identifier, Label, Ownership, Sha256, Text
from .evidence import EvidenceMeasurement, EvidenceRevisionRef, EvidenceSupport
from .jd_mapping import JDRequirementRef, RequirementPriority, RequirementState

EvidenceUnknown = Literal["evidence", "ownership", "measurement", "qualification"]
ApplicationGuidance = Literal["insufficient_requirements", "review_required_gaps", "prepare_with_evidence"]


class DefensibleClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence: EvidenceRevisionRef
    text: Text
    support: EvidenceSupport
    ownership: Ownership
    scope: Label | None
    measurement: EvidenceMeasurement | None
    qualifiers: list[Label]


class DefensibilityRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: JDRequirementRef
    priority: RequirementPriority
    kind: Literal["technical", "experience", "credential"]
    state: RequirementState
    claim: DefensibleClaim | None
    unknowns: list[EvidenceUnknown]
    questions: list[Text]


class TargetDefensibility(CareerContract):
    owner_id: Identifier
    target_id: Identifier
    jd_evaluation_id: Identifier
    jd_text_sha256: Sha256
    resume_comparable: bool
    guidance: ApplicationGuidance
    requirements: list[DefensibilityRequirement]
