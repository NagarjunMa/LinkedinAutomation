"""Inputs and views for durable interview sessions."""
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict

from .common import CandidateStage, Identifier, Revision, Text, Timestamp
from .interview import CareerSessionState
from .persistence import _without_null

InterviewMode = Literal["foundation", "target_calibration", "application_gap", "career_refresh"]
MessageRole = Literal["user", "assistant"]
MessageStatus = Literal["pending", "complete", "interrupted"]


class SessionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: InterviewMode
    target_id: Identifier | None = None
    candidate_stage: CandidateStage | None = None


class SessionView(CareerSessionState):
    created_at: Timestamp
    updated_at: Timestamp
    retention_expires_at: Timestamp | None = None


class MessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: Identifier
    content: Annotated[Text, AfterValidator(_without_null)]


class MessageView(MessageInput):
    position: Revision
    role: MessageRole
    processing_status: MessageStatus
    created_at: Timestamp
