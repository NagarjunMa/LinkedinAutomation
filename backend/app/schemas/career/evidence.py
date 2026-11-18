"""Evidence, provenance and candidate decision contracts."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from .common import CareerContract, Identifier, Label, Ownership, Revision, Sha256, SourceRef, Text, Timestamp


EvidenceCategory = Literal["problem", "requirement", "action", "decision", "validation", "outcome", "skill", "scope"]
EvidenceLifecycle = Literal["proposed", "confirmed", "rejected", "contradicted", "private", "unavailable"]
EvidenceSupport = Literal["candidate_statement", "document_backed", "artifact_linked", "independently_verified"]
EvidenceAction = Literal["confirm", "edit", "reject", "mark_private", "mark_unavailable", "resolve_contradiction"]


class EvidenceRevisionRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: Identifier
    revision: Revision


class EvidenceSourceLink(SourceRef):
    model_config = ConfigDict(json_schema_extra={"oneOf": [
        {"required": ["excerpt"], "properties": {"excerpt": {"type": "string"}}},
        {"required": ["excerpt_sha256"], "properties": {"excerpt_sha256": {"type": "string"}}},
    ]})

    relationship: Literal["supports", "contradicts"]
    locator: Label
    excerpt: Annotated[str, Field(min_length=1, max_length=4000, pattern=r"\S")] | None = None
    excerpt_sha256: Sha256 | None = None
    extraction: Literal["candidate", "parser", "model", "reviewer"]

    @model_validator(mode="after")
    def validate_excerpt(self) -> Self:
        if (self.excerpt is None) == (self.excerpt_sha256 is None):
            raise ValueError("source link requires exactly one of excerpt or excerpt_sha256")
        return self


class SupportingSourceLink(EvidenceSourceLink):
    relationship: Literal["supports"]


class ContradictingSourceLink(EvidenceSourceLink):
    relationship: Literal["contradicts"]


class EvidenceMeasurement(BaseModel):
    """Owner-provided basis for a number already stated in the claim."""

    model_config = ConfigDict(extra="forbid")

    method: Label
    scope: Label
    estimated: StrictBool


class CareerEvidenceItem(CareerContract, EvidenceRevisionRef):
    model_config = ConfigDict(json_schema_extra={"allOf": [
        {
            "if": {"properties": {"lifecycle": {"const": "private"}}},
            "then": {"required": ["is_private"], "properties": {"is_private": {"const": True}}},
        },
        {
            "if": {"properties": {"support": {"const": "independently_verified"}}},
            "then": {"required": ["verification_ref"], "properties": {"verification_ref": {"type": "string"}}},
            "else": {"properties": {"verification_ref": {"type": "null"}}},
        },
        {
            "if": {"properties": {"lifecycle": {"const": "confirmed"}}},
            "then": {"properties": {"sources": {"items": {"properties": {"relationship": {"const": "supports"}}}}}},
        },
        {
            "if": {"properties": {"lifecycle": {"const": "contradicted"}}},
            "then": {"properties": {"sources": {"contains": {"properties": {"relationship": {"const": "contradicts"}}}}}},
        },
    ]})

    owner_id: Identifier
    claim: Text
    category: EvidenceCategory
    ownership: Ownership
    scope: Label | None = None
    measurement: EvidenceMeasurement | None = None
    qualifiers: list[Label] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] | None = None
    lifecycle: EvidenceLifecycle
    support: EvidenceSupport
    is_private: StrictBool = False
    sources: list[EvidenceSourceLink] = Field(min_length=1)
    verification_ref: Identifier | None = None
    supersedes_revision: Revision | None = None

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if (self.support == "independently_verified") != (self.verification_ref is not None):
            raise ValueError("independent verification requires a verification_ref reserved for that support level")
        if self.lifecycle == "private" and not self.is_private:
            raise ValueError("private evidence must be marked private")
        if self.lifecycle == "confirmed" and (
            not any(link.relationship == "supports" for link in self.sources)
            or any(link.relationship == "contradicts" for link in self.sources)
        ):
            raise ValueError("confirmed evidence requires support and no unresolved contradiction")
        if self.lifecycle == "contradicted" and not any(link.relationship == "contradicts" for link in self.sources):
            raise ValueError("contradicted evidence requires a contradictory source")
        if self.supersedes_revision is not None and self.supersedes_revision >= self.revision:
            raise ValueError("superseded revision must be older than the evidence revision")
        return self


class CareerEvidenceDecision(CareerContract):
    evidence: EvidenceRevisionRef
    actor_id: Identifier
    action: EvidenceAction
    decided_at: Timestamp
    reason: Text | None = None
    resulting_revision: Revision

    @model_validator(mode="after")
    def validate_revision(self) -> Self:
        if self.resulting_revision <= self.evidence.revision:
            raise ValueError("evidence decisions require a newer revision")
        return self


class EvidenceProposal(BaseModel):
    """Internal proposal input. The caller cannot supply owner, support or lifecycle."""

    model_config = ConfigDict(extra="forbid")

    claim: Text
    category: EvidenceCategory
    ownership: Ownership
    scope: Label | None = None
    qualifiers: list[Label] = Field(default_factory=list, max_length=20)
    confidence: Literal["low", "medium", "high"] | None = None
    sources: list[EvidenceSourceLink] = Field(min_length=1, max_length=20)


class EvidenceDecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision: Revision
    action: EvidenceAction
    reason: Text | None = None
    claim: Text | None = None
    ownership: Ownership | None = None
    scope: Label | None = None
    measurement: EvidenceMeasurement | None = None

    def edit_values(self) -> dict:
        return self.model_dump(include={"claim", "ownership", "scope", "measurement"}, exclude_unset=True)

    @model_validator(mode="after")
    def validate_edit(self) -> Self:
        changes = self.edit_values()
        if self.action == "edit":
            if not changes or any(key in changes and changes[key] is None for key in ("claim", "ownership")):
                raise ValueError("provide an edit with a non-null claim or ownership when supplied")
        elif self.claim is not None or changes.keys() - {"claim"}:
            raise ValueError("only edits may change evidence fields")
        return self


class EvidenceHistory(BaseModel):
    revisions: list[CareerEvidenceItem]
    decisions: list[CareerEvidenceDecision]
