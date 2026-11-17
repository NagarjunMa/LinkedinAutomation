"""Authenticated endpoints for saving and resuming interviews."""
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import suppress
import logging
import os
from pathlib import Path
from typing import Annotated

from anyio import CancelScope, create_task_group
from anyio.lowlevel import checkpoint

from fastapi import APIRouter, Depends, Query, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.types import Receive, Scope, Send

from app.api.error_mapping import to_http_exception
from app.application.career_model import CareerModel
from app.application.errors import ApplicationError, ExternalServiceError, ResourceConflictError, ResourceNotFoundError
from app.application.interview_service import InterviewService
from app.application.interview_turn_service import AdmittedTurn, InterviewTurnService, run_admitted_turn
from app.core.auth import get_current_user_id
from app.core.config import settings
from app.core.openai_client import DEFAULT_MANIFESTS, get_model_runtime
from app.db.session import get_db
from app.schemas.career.common import Identifier
from app.schemas.career.interview_persistence import (
    MessageView, SessionInput, SessionView, TurnAssistant, TurnChapterCompleted, TurnClarification,
    TurnCompleted, TurnFailed, TurnInput, TurnInterrupted, TurnPending, TurnProgress, TurnReplayed, TurnStarted,
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


_TurnEvent = (
    TurnStarted | TurnProgress | TurnClarification | TurnAssistant | TurnChapterCompleted | TurnCompleted
    | TurnFailed | TurnPending | TurnInterrupted | TurnReplayed
)


def _frame(event: _TurnEvent) -> str:
    return f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"


class _TurnStream(StreamingResponse):
    def __init__(self, frames: AsyncIterator[str], *, on_close: Callable[[], Awaitable[None]] | None = None):
        super().__init__(frames, media_type="text/event-stream",
                         headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})
        self.on_close = on_close

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            async with create_task_group() as tasks:
                async def on_disconnect() -> None:
                    await self.listen_for_disconnect(receive)
                    tasks.cancel_scope.cancel()

                # Also listen on ASGI 2.4, where a broken send alone would not interrupt model I/O.
                tasks.start_soon(on_disconnect)
                try:
                    with suppress(OSError):
                        await self.stream_response(send)
                finally:
                    tasks.cancel_scope.cancel()
        finally:
            if self.on_close is not None:
                with CancelScope(shield=True):
                    await self.on_close()


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
        admitted = turns.begin(session_id, data, create_model=_turn_model)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None

    if not isinstance(admitted, AdmittedTurn):
        async def existing():
            yield _frame(admitted)

        return _TurnStream(existing())

    finished = False

    async def settle_interruption() -> None:
        nonlocal finished
        if not finished:
            try:
                await run_in_threadpool(turns.interrupt, admitted)
                finished = True
            except Exception:
                logger.warning("Career turn interruption reconciliation deferred")

    async def record_dispatch() -> None:
        await run_in_threadpool(turns.record_dispatch, admitted)
        await checkpoint()

    async def stream():
        nonlocal finished
        try:
            yield _frame(TurnStarted(key=admitted.message.key, position=admitted.message.position))
            yield _frame(TurnProgress())
            now = await run_in_threadpool(turns.validate_admission, admitted)
            outcome = await run_admitted_turn(admitted, now=now, before_attempt=record_dispatch)
            message, state = await run_in_threadpool(turns.complete, admitted, outcome)
            finished = True
            if outcome.decision.action == "confirm_stage":
                yield _frame(TurnClarification())
            if outcome.decision.action == "advance_chapter":
                yield _frame(TurnChapterCompleted(chapter=admitted.planning_state.chapter))
            yield _frame(TurnAssistant(message=message))
            yield _frame(TurnCompleted(state=state, proposal_validated=bool(outcome.runs) and outcome.fallback_reason is None,
                                       tokens_reserved=outcome.tokens_reserved))
            return
        except (ResourceConflictError, ResourceNotFoundError):
            failure = TurnFailed(code="state_changed")
        except Exception:
            logger.warning("Career turn could not complete")
            failure = TurnFailed(code="turn_unavailable")
        with CancelScope(shield=True):
            await settle_interruption()
        yield _frame(failure)

    return _TurnStream(stream(), on_close=settle_interruption)
