"""Pure Career Interview chapter transitions."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.application.errors import InvalidOperationError, ResourceConflictError
from app.schemas.career.common import CandidateStage, Identifier, Revision
from app.schemas.career.interview import CareerSessionState

INTRODUCTION = "introduction"
FINAL_CHAPTER = "evidence_confirmation"
WORK_HISTORY = ("work_project_timeline", "project_ownership")

_MODE_CHAPTERS = {
    "foundation": (*WORK_HISTORY, "technical_depth", "outcomes", "constraints_recovery",
                   "collaboration_leadership", "learning", "communication_gaps"),
    "target_calibration": (*WORK_HISTORY, "technical_depth", "learning", "communication_gaps"),
    "application_gap": ("communication_gaps", *WORK_HISTORY, "outcomes", "learning"),
    "career_refresh": (*WORK_HISTORY, "technical_depth", "outcomes", "constraints_recovery",
                       "collaboration_leadership"),
}


class InterviewEvent(BaseModel):
    """Application-owned event. Provider recommendations have a separate contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: Identifier
    expected_state_version: Revision
    kind: Literal["confirm_stage", "chapter_reviewed", "pause", "resume", "complete", "fail"]
    candidate_stage: CandidateStage | None = None

    @model_validator(mode="after")
    def validate_stage(self) -> Self:
        if (self.kind == "confirm_stage") != (self.candidate_stage is not None):
            raise ValueError("Only stage confirmation requires a candidate stage")
        return self


def transition(state: CareerSessionState, event: InterviewEvent) -> CareerSessionState:
    """Return a new snapshot for the application's session-version check before saving."""
    if not isinstance(event, InterviewEvent) or event.session_id != state.session_id:
        raise InvalidOperationError("Expected an application event for this interview session")
    if event.expected_state_version != state.state_version:
        raise ResourceConflictError("Interview state version is no longer current")
    if state.status in ("completed", "failed"):
        raise ResourceConflictError("Interview is terminal")

    chapters = interview_chapters(state)

    match (state.status, event.kind, state.chapter):
        case ("active", "confirm_stage", chapter) if chapter == INTRODUCTION:
            updates = {"candidate_stage": event.candidate_stage, "chapter": _chapters(state, event.candidate_stage)[1]}
        case ("active", "chapter_reviewed", chapter) if chapter not in (INTRODUCTION, FINAL_CHAPTER):
            updates = {"chapter": chapters[chapters.index(chapter) + 1]}
        case ("active", "pause", _):
            updates = {"status": "paused"}
        case ("paused", "resume", _):
            updates = {"status": "active"}
        case ("active", "complete", chapter) if chapter == FINAL_CHAPTER:
            updates = {"status": "completed"}
        case ("active" | "paused", "fail", _):
            updates = {"status": "failed"}
        case _:
            raise InvalidOperationError("Interview event is not legal in the current state")

    return state.model_copy(update={**updates, "state_version": state.state_version + 1})


def interview_chapters(state: CareerSessionState) -> tuple[str, ...]:
    chapters = _chapters(state, state.candidate_stage)
    if state.chapter not in chapters or (state.chapter != INTRODUCTION and state.candidate_stage is None):
        raise InvalidOperationError("Interview chapter is invalid for this mode or stage")
    return chapters


def _chapters(state: CareerSessionState, stage: CandidateStage | None) -> tuple[str, ...]:
    academic = ("academic_foundation",) if state.mode == "foundation" and stage in ("student", "new_graduate") else ()
    return (INTRODUCTION, *academic, *_MODE_CHAPTERS[state.mode], FINAL_CHAPTER)
