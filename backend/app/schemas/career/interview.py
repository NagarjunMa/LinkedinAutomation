"""Interview state, coverage and untrusted turn proposals."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import CandidateStage, CareerContract, Count, Identifier, Label, Revision, Text
from .evidence import ContradictingSourceLink, EvidenceCategory, EvidenceRevisionRef, SupportingSourceLink


class EvidenceSlotCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"allOf": [
        {
            "if": {"properties": {"status": {"const": "confirmed"}}},
            "then": {"required": ["evidence_revisions"], "properties": {"evidence_revisions": {"minItems": 1}}},
        },
        {
            "if": {"properties": {"status": {"const": "missing"}}},
            "then": {"properties": {"evidence_revisions": {"maxItems": 0}}},
        },
    ]})

    slot: Identifier
    status: Literal["missing", "proposed", "confirmed", "private", "unavailable", "contradicted"]
    evidence_revisions: list[EvidenceRevisionRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_coverage(self) -> Self:
        if self.status == "confirmed" and not self.evidence_revisions:
            raise ValueError("confirmed coverage requires evidence revisions")
        if self.status == "missing" and self.evidence_revisions:
            raise ValueError("missing coverage cannot cite evidence revisions")
        return self


class CareerCoverage(CareerContract):
    session_id: Identifier
    slots: list[EvidenceSlotCoverage]

    @model_validator(mode="after")
    def validate_slots(self) -> Self:
        if len({slot.slot for slot in self.slots}) != len(self.slots):
            raise ValueError("coverage slots must be unique")
        return self


class CareerSessionState(CareerContract):
    session_id: Identifier
    owner_id: Identifier
    target_id: Identifier | None = None
    candidate_stage: CandidateStage | None = None
    mode: Literal["foundation", "target_calibration", "application_gap", "career_refresh"]
    status: Literal["active", "paused", "completed", "failed"]
    chapter: Identifier
    state_version: Revision
    prompt_version: Identifier
    turns_remaining: Count
    tokens_remaining: Count


class CareerEvidenceProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: Text
    category: EvidenceCategory
    qualifiers: list[Label] = Field(default_factory=list, max_length=20)
    sources: list[SupportingSourceLink] = Field(min_length=1, max_length=20)


class ContradictionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supports: SupportingSourceLink
    contradicts: ContradictingSourceLink

    @model_validator(mode="after")
    def validate_sides(self) -> Self:
        if (
            self.supports.source_id, self.supports.source_version, self.supports.locator
        ) == (
            self.contradicts.source_id, self.contradicts.source_version, self.contradicts.locator
        ):
            raise ValueError("contradiction candidates require distinct source locations")
        return self


class CareerTurnProposal(CareerContract):
    question: Label
    question_intent: Literal["probe", "clarify", "resolve_contradiction", "review"]
    target_evidence_slot: Identifier
    evidence_proposals: list[CareerEvidenceProposal] = Field(default_factory=list, max_length=10)
    contradiction_candidates: list[ContradictionCandidate] = Field(default_factory=list, max_length=10)
    recommended_action: Literal["continue", "clarify", "pause", "coverage_review", "complete", "fail"]
