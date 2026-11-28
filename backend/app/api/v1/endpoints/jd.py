"""HTTP adapters for JD analysis and resume tailoring."""

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from app.api.dependencies import get_jd_application_service
from app.api.error_mapping import to_http_exception
from app.api.response_contracts import PrivateResponseRoute
from app.application.errors import ApplicationError
from app.application.grounded_tailor import suggest_grounded_wording, validate_grounded_wording, wording_options
from app.application.jd_service import JDTailoringApplicationService
from app.core.auth import get_current_user_id
from app.core.config import settings
from app.core.rate_limiter import RateLimiter
from app.schemas.grounded_tailor import GroundedTailorApplyRequest, GroundedTailorPreviewRequest, GroundedTailorResponse
from app.schemas.jd import BulletDiff
from app.schemas.resume_v2 import ApplyTailorRequest, ApplyTailorResponse
from app.schemas.workflow_responses import JDAnalysisResponse


router = APIRouter(prefix="/jd", tags=["jd"], route_class=PrivateResponseRoute)
_wording_limits = RateLimiter()


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

@router.post("/grounded/preview", response_model=GroundedTailorResponse)
async def preview_grounded(
    body: GroundedTailorPreviewRequest,
    response: Response,
    service: JDTailoringApplicationService = Depends(get_jd_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        args = body.model_dump(exclude={"suggest_wording"})
        args["evaluation_id"] = body.evaluation_id or service.resolve_grounded_evaluation(
            body.document_id, body.target_id, current_user_id,
        )
        model_attempt = body.suggest_wording and settings.ENABLE_AI_FEATURES and _wording_limits.check_endpoint_rate_limit(
            current_user_id, "grounded_tailor_wording", max_requests=5, window_seconds=60,
        )
        preview = service.preview_grounded(**args, user_id=current_user_id)
        wording = None
        candidate = next((bullet for bullet in preview.bullets if len(wording_options(bullet)) > 1), None)
        if body.suggest_wording and candidate:
            if model_attempt:
                service.session.rollback()
            option, validation = (await suggest_grounded_wording(candidate, service.runtime) if model_attempt
                                  else validate_grounded_wording(candidate, None))
            current = service.preview_grounded(**args, user_id=current_user_id) if model_attempt else preview
            if current.bullets == preview.bullets:
                wording = {
                    "plan_id": candidate.plan.plan_id, "selected_option": option, "validation": validation,
                    "receipt": service.grounded_wording_receipt(args, current_user_id, validation),
                }
            preview = current
        response.headers["Cache-Control"] = "no-store"
        return {
            "evaluation_id": args["evaluation_id"], "resume_version_id": preview.resume_version_id,
            "jd_source": preview.jd_source, "wording": wording,
            "choices": [{"plan_id": bullet.plan.plan_id, "requirements": bullet.requirements,
                         "evidence": bullet.plan.evidence_revisions, "options": wording_options(bullet)}
                        for bullet in preview.bullets],
        }
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.post("/grounded/apply", response_model=ApplyTailorResponse)
def apply_grounded(
    body: GroundedTailorApplyRequest,
    response: Response,
    service: JDTailoringApplicationService = Depends(get_jd_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        response.headers["Cache-Control"] = "no-store"
        return service.apply_grounded(**body.model_dump(), user_id=current_user_id)
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
