"""Internal inputs for Career run, artifact and proof metadata."""

from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter, field_validator, model_validator

from app.core.openai_client import ModelManifest

from .common import CareerContract, Count, Identifier, Ownership, Revision, Sha256, SourceRef, Timestamp
from .evidence import EvidenceRevisionRef
from .resume import ClaimEvidence, GeneratedClaimLineage, ResumeReasonCode

ArtifactKind = Literal["resume", "linkedin_recommendations", "interview_story_bank", "hiring_manager_brief", "learning_plan"]
RunFailure = Literal["model_unavailable", "model_timeout", "schema_invalid", "proposal_rejected", "provider_error"]
ApplicationCommit = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]


class CareerRunManifest(CareerContract):
    """Exact release inputs for the Career proposal boundary, without user content."""

    model_config = ConfigDict(frozen=True)
    provider: Identifier
    transport: Identifier
    model_snapshot: Identifier
    prompt_name: Identifier
    prompt_version: Identifier
    prompt_hash: Sha256
    response_schema_version: Identifier
    schema_hash: Sha256
    policy_version: Identifier
    max_output_tokens: Annotated[int, Field(strict=True, ge=16, le=4096)]
    timeout_ms: Annotated[int, Field(strict=True, ge=1, le=30000)]
    max_attempts: Literal[1] = 1
    store_response: Literal[False] | None = None


RunManifest = CareerRunManifest | ModelManifest


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
    manifest: RunManifest
    metadata: RunMetadata

    @field_validator("manifest")
    @classmethod
    def validate_manifest(cls, manifest: RunManifest) -> RunManifest:
        if isinstance(manifest, CareerRunManifest):
            return manifest
        identifiers = [manifest.model_snapshot, manifest.prompt_name, manifest.prompt_version, manifest.schema_version]
        if manifest.pricing:
            identifiers.append(manifest.pricing.version)
        TypeAdapter(list[Identifier]).validate_python(identifiers)
        return manifest

    @model_validator(mode="after")
    def validate_career_commit(self) -> Self:
        if isinstance(self.manifest, CareerRunManifest):
            TypeAdapter(ApplicationCommit).validate_python(self.metadata.application_commit)
        return self


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
