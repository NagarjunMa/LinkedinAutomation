"""Authenticated endpoints for saving and resuming interviews."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.error_mapping import to_http_exception
from app.application.errors import ApplicationError
from app.application.interview_service import InterviewService
from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.career.common import Identifier
from app.schemas.career.interview_persistence import MessageView, SessionInput, SessionView


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
