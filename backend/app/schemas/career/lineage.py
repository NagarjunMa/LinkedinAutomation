"""Internal inputs for Career run, artifact and proof metadata."""

from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator

from app.core.openai_client import ModelManifest

from .common import CareerContract, Count, Identifier, Ownership, Revision, SourceRef, Timestamp
from .evidence import EvidenceRevisionRef
from .resume import ClaimEvidence, GeneratedClaimLineage, ResumeReasonCode

ArtifactKind = Literal["resume", "linkedin_recommendations", "interview_story_bank", "hiring_manager_brief", "learning_plan"]
RunFailure = Literal["model_unavailable", "model_timeout", "schema_invalid", "proposal_rejected", "provider_error"]


class RunMetadata(CareerContract):
    application_commit: Identifier
    session_id: Identifier | None = None
    provider_request_id: Identifier | None = None
    start_state: Identifier | None = None
    end_state: Identifier | None = None
    input_tokens: Count | None = None
    output_tokens: Count | None = None
    cost_usd: Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=6)] | None = None
    latency_ms: Count
    retry_count: Count = 0
    repair_count: Count = 0
    reason_codes: list[ResumeReasonCode] = Field(default_factory=list, max_length=32)
    failure: RunFailure | None = None


class StoredRun(CareerContract):
    manifest: ModelManifest
    metadata: RunMetadata

    @field_validator("manifest")
    @classmethod
    def validate_manifest(cls, manifest: ModelManifest) -> ModelManifest:
        identifiers = [manifest.model_snapshot, manifest.prompt_name, manifest.prompt_version, manifest.schema_version]
        if manifest.pricing:
            identifiers.append(manifest.pricing.version)
        TypeAdapter(list[Identifier]).validate_python(identifiers)
        return manifest


class GeneratorManifest(CareerContract):
    application_commit: Identifier
    generator_version: Identifier
    policy_version: Identifier


class ArtifactRef(CareerContract):
    artifact_id: Identifier
    version: Revision


class ClaimInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: Identifier
    evidence_revisions: ClaimEvidence


class ArtifactInput(CareerContract):
    kind: ArtifactKind
    generator: GeneratorManifest
    target_id: Identifier | None = None
    run_id: Identifier | None = None
    claims: list[ClaimInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_claims(self) -> Self:
        ids = {claim.claim_id for claim in self.claims}
        if len(ids) != len(self.claims) or sum(len(c.evidence_revisions) for c in self.claims) > 500:
            raise ValueError("Artifact requires unique claims and at most 500 evidence links")
        return self


class ArtifactView(ArtifactRef):
    kind: ArtifactKind
    generator: GeneratorManifest
    target_id: Identifier | None
    run_id: Identifier | None
    created_at: Timestamp
    status: Literal["eligible", "invalidated"]
    claims: list[GeneratedClaimLineage]


class ProofMetadata(CareerContract):
    source: SourceRef
    evidence: EvidenceRevisionRef
    access: Literal["public", "restricted"]
    confidentiality: Literal["public", "private"]
    ownership: Ownership
    inspection: Literal["unreviewed", "available", "unavailable"] = "unreviewed"
