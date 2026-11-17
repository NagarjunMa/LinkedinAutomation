"""Inputs and views for durable interview sessions."""
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, StrictBool

from .common import CandidateStage, Count, Identifier, Revision, Text, Timestamp
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


class TurnRecoveryView(BaseModel):
    candidate_stage: CandidateStage | None


class MessageView(MessageInput):
    position: Revision
    role: MessageRole
    processing_status: MessageStatus
    created_at: Timestamp
    turn_recovery: TurnRecoveryView | None = None


class TurnInput(MessageInput):
    expected_state_version: Revision
    candidate_stage: CandidateStage | None = None
    retry: StrictBool = False


class TurnStarted(BaseModel):
    type: Literal["turn.started"] = "turn.started"
    key: Identifier
    position: Revision


class TurnProgress(BaseModel):
    type: Literal["analysis.progress"] = "analysis.progress"
    status: Literal["validating"] = "validating"


class TurnAssistant(BaseModel):
    type: Literal["assistant.message"] = "assistant.message"
    message: MessageView


class TurnClarification(BaseModel):
    type: Literal["clarification.required"] = "clarification.required"
    reason: Literal["confirm_stage"] = "confirm_stage"


class TurnChapterCompleted(BaseModel):
    type: Literal["chapter.completed"] = "chapter.completed"
    chapter: Identifier


class TurnCompleted(BaseModel):
    type: Literal["turn.completed"] = "turn.completed"
    state: SessionView
    proposal_validated: bool
    tokens_reserved: Count


class TurnFailed(BaseModel):
    type: Literal["turn.failed"] = "turn.failed"
    code: Literal["state_changed", "turn_unavailable"]


class TurnPending(BaseModel):
    type: Literal["turn.pending"] = "turn.pending"
    key: Identifier
    lease_expires_at: Timestamp


class TurnInterrupted(BaseModel):
    type: Literal["turn.interrupted"] = "turn.interrupted"
    key: Identifier
    state_version: Revision
    can_retry: bool


class TurnReplayed(BaseModel):
    type: Literal["turn.replayed"] = "turn.replayed"
    message: MessageView
    state: SessionView
    recovered: bool
