"""Source identity, target roles and the LinkedIn PDF review contracts."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from .common import CareerContract, Identifier, Label, Revision, Sha256, SourceRef, Text, Timestamp
from .evidence import EvidenceRevisionRef

LOCATOR_FINDINGS = ("unsupported_claim", "ambiguous_claim", "evidence_gap", "consistency_question")
EVIDENCE_FINDINGS = ("missing_confirmed_evidence", "communication_gap", "weak_prominence")
TARGET_GAPS = ("experience_gap", "knowledge_gap")


class CareerSource(CareerContract):
    model_config = ConfigDict(json_schema_extra={
        "if": {"properties": {"kind": {"const": "resume"}}},
        "then": {"required": ["resume_document_id"], "properties": {"resume_document_id": {"type": "string"}}},
        "else": {"properties": {"resume_document_id": {"type": "null"}}},
    })

    source: SourceRef
    owner_id: Identifier
    kind: Literal["resume", "linkedin_profile_pdf", "candidate_introduction", "interview_message", "public_proof_link", "job_description"]
    content_sha256: Sha256
    created_at: Timestamp
    retention_expires_at: Timestamp | None = None
    resume_document_id: Identifier | None = None
    extraction_version: Identifier | None = None

    @model_validator(mode="after")
    def validate_reference(self) -> Self:
        if (self.kind == "resume") != (self.resume_document_id is not None):
            raise ValueError("resume sources require a resume_document_id reserved for that kind")
        if self.retention_expires_at and self.retention_expires_at <= self.created_at:
            raise ValueError("retention expiry must follow source creation")
        return self


class CareerTarget(CareerContract):
    target_id: Identifier
    owner_id: Identifier
    role_family: Label
    seniority: Label
    location: Label | None = None
    job_description: SourceRef | None = None
    desired_work: list[Label] = Field(default_factory=list)
    exclusions: list[Label] = Field(default_factory=list)
    status: Literal["active", "archived"]


class LinkedInSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Literal[
        "identity", "contact", "headline", "about", "experience", "education", "projects", "skills",
        "certifications", "licenses", "publications", "volunteering", "honors", "languages", "featured", "unclassified",
    ]
    page: Revision
    locator: Label
    text: Text


class LinkedInExperience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: Revision
    locator: Label
    title: Label | None = None
    company: Label | None = None
    employment_type: Label | None = None
    start_date: Label | None = None
    end_date: Label | None = None
    location: Label | None = None
    description: Text | None = None


class LinkedInDocument(CareerContract):
    source: SourceRef
    raw_text: str
    name: Label | None = None
    profile_url: HttpUrl | None = None
    location: Label | None = None
    contact_links: list[Label] = Field(default_factory=list)
    sections: list[LinkedInSection]
    experience: list[LinkedInExperience] = Field(default_factory=list)
    coverage: Literal["uploaded_export_only"]


class LinkedInFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"allOf": [
        {
            "if": {"properties": {"kind": {"enum": list(kinds)}}},
            "then": {"required": [field], "properties": {field: constraint}},
        }
        for kinds, field, constraint in (
            (LOCATOR_FINDINGS, "document_locator", {"type": "string"}),
            (EVIDENCE_FINDINGS, "evidence_revisions", {"minItems": 1}),
            (TARGET_GAPS, "target_requirement_id", {"type": "string"}),
        )
    ]})

    kind: Literal[
        "missing_confirmed_evidence", "unsupported_claim", "ambiguous_claim",
        "communication_gap", "evidence_gap", "consistency_question", "experience_gap", "knowledge_gap",
        "positioning_gap", "weak_prominence", "interview_question", "document_limit",
    ]
    explanation: Text
    document_locator: Label | None = None
    target_requirement_id: Identifier | None = None
    evidence_revisions: list[EvidenceRevisionRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_locator(self) -> Self:
        if self.kind in LOCATOR_FINDINGS and not self.document_locator:
            raise ValueError("a finding about a profile claim requires a document locator")
        if self.kind in EVIDENCE_FINDINGS and not self.evidence_revisions:
            raise ValueError("a finding about missing or buried evidence requires an evidence revision")
        if self.kind in TARGET_GAPS and not self.target_requirement_id:
            raise ValueError("a target gap requires a target requirement ID")
        return self


class LinkedInReview(CareerContract):
    document: SourceRef
    target_id: Identifier
    evidence_snapshot_version: Revision
    parser_version: Identifier
    model_manifest_id: Identifier | None = None
    generated_artifact_ids: list[Identifier] = Field(default_factory=list)
    findings: list[LinkedInFinding]
