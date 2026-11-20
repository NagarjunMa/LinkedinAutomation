"""Authenticated target selection for Career Evidence."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.error_mapping import to_http_exception
from app.application.career_service import CareerApplicationService
from app.application.errors import ApplicationError
from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.career.persistence import CareerTargetInput
from app.schemas.career.sources import CareerTarget

router = APIRouter(prefix="/career/targets", tags=["career-targets"])


def _service(response: Response, owner: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return CareerApplicationService(db, owner)


Service = Annotated[CareerApplicationService, Depends(_service)]


@router.get("")
def list_active_targets(
    service: Service,
    offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[CareerTarget]:
    return service.list_targets(offset=offset, limit=limit, active_only=True)


@router.post("", status_code=201)
def create_career_target(data: CareerTargetInput, service: Service) -> CareerTarget:
    try:
        return service.create_target(data)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None
