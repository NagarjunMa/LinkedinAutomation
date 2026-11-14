"""Authenticated reads and decisions for the Career Evidence ledger."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.error_mapping import to_http_exception
from app.application.errors import ApplicationError
from app.application.evidence_service import EvidenceService
from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.career.common import Identifier
from app.schemas.career.evidence import CareerEvidenceItem, EvidenceDecisionInput, EvidenceHistory

router = APIRouter(prefix="/career/evidence", tags=["career-evidence"])


def _service(response: Response, owner: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return EvidenceService(db, owner)


Service = Annotated[EvidenceService, Depends(_service)]
Offset = Annotated[int, Query(ge=0, le=1_000_000)]
Limit = Annotated[int, Query(ge=1, le=100)]


@router.get("")
def list_evidence(service: Service, offset: Offset = 0, limit: Limit = 50) -> list[CareerEvidenceItem]:
    try:
        return service.list(offset=offset, limit=limit)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.get("/{evidence_id}")
def get_evidence(evidence_id: Identifier, service: Service) -> CareerEvidenceItem:
    try:
        return service.get(evidence_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.get("/{evidence_id}/history")
def get_history(evidence_id: Identifier, service: Service, offset: Offset = 0, limit: Limit = 50) -> EvidenceHistory:
    try:
        return service.history(evidence_id, offset=offset, limit=limit)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.patch("/{evidence_id}/decision")
def decide(evidence_id: Identifier, data: EvidenceDecisionInput, service: Service) -> CareerEvidenceItem:
    try:
        return service.decide(evidence_id, data)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None
