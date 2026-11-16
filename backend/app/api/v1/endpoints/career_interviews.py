"""Authenticated endpoints for saving and resuming interviews."""
from contextlib import suppress
import logging
import os
from pathlib import Path
from typing import Annotated

from anyio import CancelScope

from fastapi import APIRouter, Depends, Query, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.error_mapping import to_http_exception
from app.application.career_model import CareerModel
from app.application.errors import ApplicationError, ExternalServiceError, ResourceConflictError, ResourceNotFoundError
from app.application.interview_service import InterviewService
from app.application.interview_turn_service import InterviewTurnService, run_admitted_turn
from app.core.auth import get_current_user_id
from app.core.config import settings
from app.core.openai_client import DEFAULT_MANIFESTS, get_model_runtime
from app.db.session import get_db
from app.schemas.career.common import Identifier
from app.schemas.career.interview_persistence import (
    MessageView, SessionInput, SessionView, TurnAssistant, TurnChapterCompleted, TurnClarification,
    TurnCompleted, TurnFailed, TurnInput, TurnProgress, TurnStarted,
)
from app.services.career_model_openai import OpenAICareerModel


def _service(response: Response, owner: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return InterviewService(db, owner)


Service = Annotated[InterviewService, Depends(_service)]
Offset = Annotated[int, Query(ge=0, le=1_000_000)]
Limit = Annotated[int, Query(ge=1, le=100)]
router = APIRouter(prefix="/career/sessions", tags=["career-interviews"])


@router.post("", status_code=201)
def create_session(data: SessionInput, service: Service) -> SessionView:
    try:
        return service.create(data)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.get("")
def list_sessions(service: Service, offset: Offset = 0, limit: Limit = 50) -> list[SessionView]:
    return service.list_sessions(offset=offset, limit=limit)


@router.get("/{session_id}")
def get_session(session_id: Identifier, service: Service) -> SessionView:
    try:
        return service.get(session_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.post("/{session_id}/resume")
def resume_session(session_id: Identifier, service: Service) -> SessionView:
    try:
        return service.resume(session_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.get("/{session_id}/messages")
def list_messages(session_id: Identifier, service: Service, offset: Offset = 0, limit: Limit = 50) -> list[MessageView]:
    try:
        return service.messages(session_id, offset=offset, limit=limit)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


logger = logging.getLogger(__name__)
_PACKAGED_REVISION = Path(__file__).resolve().parents[4] / "release_revision.txt"


def _turn_model() -> CareerModel | None:
    key = settings.CAREER_MODEL_SAFETY_KEY
    if not settings.ENABLE_AI_FEATURES or key is None:
        return None
    manifest = DEFAULT_MANIFESTS["evaluator"]
    try:
        try:
            commit = _PACKAGED_REVISION.read_text(encoding="ascii").strip()
        except FileNotFoundError:
            commit = os.getenv("RAILWAY_GIT_COMMIT_SHA") or settings.CAREER_MODEL_APPLICATION_COMMIT or ""
        safety_key = key.get_secret_value()
        transcript_key = settings.CAREER_TRANSCRIPT_KEY
        if safety_key in (settings.OPENAI_API_KEY, transcript_key.get_secret_value() if transcript_key else ""):
            raise ValueError("Career safety key must be dedicated")
        return OpenAICareerModel(
            get_model_runtime(), model_snapshot=manifest.model_snapshot, pricing=manifest.pricing,
            application_commit=commit, safety_key=safety_key.encode(),
        )
    except (OSError, ValueError):
        raise ExternalServiceError("Career model configuration is unavailable") from None


_TurnEvent = TurnStarted | TurnProgress | TurnClarification | TurnAssistant | TurnChapterCompleted | TurnCompleted | TurnFailed


def _frame(event: _TurnEvent) -> str:
    return f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"


@router.post(
    "/{session_id}/turns", response_class=StreamingResponse,
    responses={200: {"description": "Typed Career turn events as server-sent events",
                     "content": {"text/event-stream": {"schema": {"type": "string"}}}}},
)
def create_turn(session_id: Identifier, data: TurnInput, service: Service) -> StreamingResponse:
    turns = InterviewTurnService(service.db, service.owner)
    try:
        if not settings.CAREER_TURNS_ENABLED:
            raise ExternalServiceError("Career turns are unavailable")
        model = _turn_model()
        admitted = turns.begin(session_id, data, model_enabled=model is not None)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None

    async def validate_retry() -> None:
        await run_in_threadpool(turns.validate_admission, admitted)

    async def stream():
        committed = False
        failure = None
        try:
            yield _frame(TurnStarted(key=admitted.message.key, position=admitted.message.position))
            yield _frame(TurnProgress())
            now = await run_in_threadpool(turns.validate_admission, admitted)
            outcome = await run_admitted_turn(admitted, model, now=now, before_retry=validate_retry)
            message, state = await run_in_threadpool(turns.complete, admitted, outcome)
            committed = True
            if outcome.decision.action == "confirm_stage":
                yield _frame(TurnClarification())
            if outcome.decision.action == "advance_chapter":
                yield _frame(TurnChapterCompleted(chapter=admitted.planning_state.chapter))
            yield _frame(TurnAssistant(message=message))
            yield _frame(TurnCompleted(state=state, proposal_validated=bool(outcome.runs) and outcome.fallback_reason is None,
                                       tokens_reserved=outcome.tokens_reserved))
        except (ResourceConflictError, ResourceNotFoundError):
            failure = "state_changed"
        except Exception:
            logger.warning("Career turn could not complete")
            failure = "turn_unavailable"
        finally:
            if not committed:
                with CancelScope(shield=True), suppress(Exception):
                    await run_in_threadpool(turns.interrupt, admitted)
        if failure is not None:
            yield _frame(TurnFailed(code=failure))

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})
