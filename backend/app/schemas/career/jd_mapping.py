"""Read-only links between saved job requirements and confirmed career evidence."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import CareerContract, Count, Identifier, Sha256, SourceRef, Text
from .evidence import EvidenceRevisionRef


RequirementPriority = Literal["must_have", "preferred"]
RequirementState = Literal[
    "supported", "partial", "communication_gap", "evidence_gap",
    "experience_gap", "knowledge_gap", "unresolved",
]
RequirementReason = Literal[
    "confirmed_application", "additional_qualification_unverified",
    "confirmed_application_not_found_in_resume", "application_scope_unclear",
    "skill_without_application", "no_matching_confirmed_evidence", "learning_only",
    "requirement_not_grounded", "requirement_not_affirmative", "qualification_unresolved",
]


class JDRequirementRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: Identifier
    revision: Sha256
    source_start: Count | None = Field(description="Zero-based Unicode code-point offset in the saved job description.")
    source_end: Count | None = Field(description="Exclusive Unicode code-point end offset in the saved job description.")


class JDRequirementMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: JDRequirementRef
    priority: RequirementPriority
    kind: Literal["technical", "experience", "credential"]
    state: RequirementState
    reason_code: RequirementReason
    evidence: EvidenceRevisionRef | None
    follow_up: Text | None


class TargetJDMapping(CareerContract):
    policy_version: Literal["jd-mapping-v1"]
    target_id: Identifier
    jd_evaluation_id: Identifier
    jd_source: SourceRef | None
    jd_text_sha256: Sha256
    resume_document_id: Identifier
    resume_comparable: bool
    requirements: list[JDRequirementMapping]
