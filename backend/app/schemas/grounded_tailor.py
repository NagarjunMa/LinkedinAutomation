"""Request and response contracts for tailoring from saved, owned sources."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.career.common import Identifier, Sha256, SourceRef
from app.schemas.career.evidence import EvidenceRevisionRef
from app.schemas.career.jd_mapping import JDRequirementRef
from app.schemas.career.resume import ResumeRenderValidationResult


class GroundedTailorRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: Identifier
    target_id: Identifier
    resume_version_id: Identifier | None
    review_id: Identifier
    evaluation_id: Identifier | None = None


class GroundedTailorPreviewRequest(GroundedTailorRequest):
    suggest_wording: bool = False


class GroundedTailorApplyRequest(GroundedTailorRequest):
    evaluation_id: Identifier
    wording_receipt: str | None = Field(default=None, max_length=4096)
    selections: dict[Sha256, Literal["safe", "action_first"]] = Field(min_length=1, max_length=80)


class GroundedWording(BaseModel):
    plan_id: Sha256
    selected_option: Literal["safe", "action_first"]
    validation: ResumeRenderValidationResult
    receipt: str


class GroundedTailorChoice(BaseModel):
    plan_id: Sha256
    requirements: list[JDRequirementRef]
    evidence: list[EvidenceRevisionRef]
    options: dict[Literal["safe", "action_first"], str]


class GroundedTailorResponse(BaseModel):
    evaluation_id: Identifier
    resume_version_id: Identifier | None
    jd_source: SourceRef
    choices: list[GroundedTailorChoice]
    wording: GroundedWording | None = None
