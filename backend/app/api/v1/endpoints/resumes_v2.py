"""HTTP adapters for resume document workflows."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.exceptions import ResponseValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field

from app.api.dependencies import get_resume_application_service
from app.api.error_mapping import to_http_exception
from app.application.errors import ApplicationError
from app.application.resume_service import ResumeApplicationService
from app.core.auth import get_current_user_id
from app.schemas.resume_responses import (
    ResumeDetailResponse,
    ResumeEvaluationResponse,
    ResumeListResponse,
    ResumeUploadResponse,
    ResumeVersionResponse,
)
from app.schemas.resume_v2 import ChangeItem, RewriteResult
from app.services.resume.file_security import ResumeFileError


logger = logging.getLogger(__name__)


class ResumeResponseRoute(APIRoute):
    """Contain response-validation errors before a traceback can expose resume data."""

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_response(request: Request):
            try:
                return await handler(request)
            except ResponseValidationError:
                # Do not log the exception, inputs, URL, or user/document identifiers.
                logger.error("Resume response contract validation failed")
                raise HTTPException(500, "Resume response could not be processed") from None

        return safe_response


router = APIRouter(tags=["resumes-v2"], route_class=ResumeResponseRoute)


class EvalRequest(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=200)


class RewriteRequest(BaseModel):
    target_role: str
    country: str = "US"
    jd_context: Optional[str] = None


class VersionRequest(BaseModel):
    parent_version_id: Optional[str] = None
    change_set: list[ChangeItem]


@router.post("/upload", status_code=201, response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    service: ResumeApplicationService = Depends(get_resume_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        return await service.upload(file, current_user_id)
    except ResumeFileError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc

@router.get("/list", response_model=ResumeListResponse)
def list_resumes(
    service: ResumeApplicationService = Depends(get_resume_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    return service.list(current_user_id)


@router.get("/{resume_document_id}", response_model=ResumeDetailResponse)
def get_resume(
    resume_document_id: str,
    service: ResumeApplicationService = Depends(get_resume_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        return service.get(resume_document_id, current_user_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.delete("/{resume_document_id}", status_code=204)
def delete_resume(
    resume_document_id: str,
    service: ResumeApplicationService = Depends(get_resume_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        service.delete(resume_document_id, current_user_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc
    return None


@router.post("/{resume_document_id}/evaluate", response_model=ResumeEvaluationResponse)
async def evaluate(
    resume_document_id: str,
    body: EvalRequest,
    service: ResumeApplicationService = Depends(get_resume_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        return await service.evaluate(resume_document_id, body.target_role, current_user_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.post("/{resume_document_id}/rewrite/{bullet_id}", response_model=RewriteResult)
async def rewrite(
    resume_document_id: str,
    bullet_id: str,
    body: RewriteRequest,
    service: ResumeApplicationService = Depends(get_resume_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        return await service.rewrite(
            resume_document_id=resume_document_id,
            bullet_id=bullet_id,
            target_role=body.target_role,
            country=body.country,
            jd_context=body.jd_context,
            user_id=current_user_id,
        )
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.post("/{resume_document_id}/versions", status_code=201, response_model=ResumeVersionResponse)
def create_version(
    resume_document_id: str,
    body: VersionRequest,
    service: ResumeApplicationService = Depends(get_resume_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        return service.create_version(
            resume_document_id=resume_document_id,
            parent_version_id=body.parent_version_id,
            change_set=body.change_set,
            user_id=current_user_id,
        )
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc
