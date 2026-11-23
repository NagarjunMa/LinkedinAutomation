"""Authenticated target selection for Career Evidence."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.error_mapping import to_http_exception
from app.application.career_service import CareerApplicationService
from app.application.errors import ApplicationError
from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.career.common import Identifier
from app.schemas.career.persistence import CareerTargetInput
from app.schemas.career.sources import CareerTarget
from app.schemas.career.target_coverage import CoverageScope, TargetResumeCoverage, TargetRoleCoverage

router = APIRouter(prefix="/career/targets", tags=["career-targets"])


def _service(response: Response, owner: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return CareerApplicationService(db, owner)


Service = Annotated[CareerApplicationService, Depends(_service)]
Explain = Annotated[bool, Query(description="Include the eligibility and ordering explanation for each focus.")]
RequiredScope = Annotated[
    CoverageScope | None,
    Query(description=(
        "Minimum scope for the saved target level. Order: component, team, cross_team, organization. "
        "Only recognized scope labels on confirmed applied evidence count."
    )),
]


@router.get("")
def list_active_targets(
    service: Service,
    offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[CareerTarget]:
    return service.list_targets(offset=offset, limit=limit, active_only=True)


@router.get("/{target_id}/coverage", response_model_exclude_unset=True)
def get_target_coverage(
    target_id: Identifier, service: Service, explain: Explain = False, required_scope: RequiredScope = None,
) -> TargetRoleCoverage:
    try:
        return service.target_coverage(target_id, explain=explain, required_scope=required_scope)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.get("/{target_id}/coverage/resume/{resume_document_id}", response_model_exclude_unset=True)
def get_target_resume_coverage(
    target_id: Identifier, resume_document_id: Identifier, service: Service,
    explain: Explain = False, required_scope: RequiredScope = None,
) -> TargetResumeCoverage:
    try:
        return service.target_resume_coverage(
            target_id, resume_document_id, explain=explain, required_scope=required_scope,
        )
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.post("", status_code=201)
def create_career_target(data: CareerTargetInput, service: Service) -> CareerTarget:
    try:
        return service.create_target(data)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None
