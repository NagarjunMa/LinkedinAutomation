"""HTTP adapters for JD analysis and resume tailoring."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import get_jd_application_service
from app.api.error_mapping import to_http_exception
from app.api.response_contracts import PrivateResponseRoute
from app.application.errors import ApplicationError
from app.application.jd_service import JDTailoringApplicationService
from app.core.auth import get_current_user_id
from app.schemas.jd import BulletDiff
from app.schemas.resume_v2 import ApplyTailorRequest, ApplyTailorResponse
from app.schemas.workflow_responses import JDAnalysisResponse


router = APIRouter(prefix="/jd", tags=["jd"], route_class=PrivateResponseRoute)


class AnalyzeRequest(BaseModel):
    resume_document_id: str
    jd_text: str = Field(..., min_length=50)


@router.post("/analyze", response_model=JDAnalysisResponse)
async def analyze(
    body: AnalyzeRequest,
    service: JDTailoringApplicationService = Depends(get_jd_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        return await service.analyze(
            resume_document_id=body.resume_document_id,
            jd_text=body.jd_text,
            user_id=current_user_id,
        )
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc

@router.post("/{jd_evaluation_id}/apply", response_model=ApplyTailorResponse)
def apply_tailor(
    jd_evaluation_id: str,
    body: ApplyTailorRequest,
    service: JDTailoringApplicationService = Depends(get_jd_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        return service.apply(jd_evaluation_id, body, current_user_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.post("/{jd_evaluation_id}/bullets/{bullet_id}/options", response_model=BulletDiff)
async def regenerate_bullet_options(
    jd_evaluation_id: str,
    bullet_id: str,
    service: JDTailoringApplicationService = Depends(get_jd_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        return await service.regenerate_options(
            evaluation_id=jd_evaluation_id,
            bullet_id=bullet_id,
            user_id=current_user_id,
        )
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc
