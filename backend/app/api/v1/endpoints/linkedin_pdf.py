"""Authenticated, private LinkedIn profile export uploads."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, Response, UploadFile
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.error_mapping import to_http_exception
from app.application.errors import ApplicationError, ExternalServiceError
from app.application.linkedin_pdf_service import LinkedInPdfService
from app.application.linkedin_review import LinkedInReviewService
from app.core.auth import get_current_user_id
from app.core.config import settings
from app.db.session import get_db
from app.schemas.career.common import Identifier, SourceRef
from app.schemas.career.sources import (
    LinkedInCopyRequest, LinkedInRecommendation, LinkedInReviewPreview, LinkedInReviewRequest,
    LinkedInTargetSelection, LinkedInUpload, LinkedInUploadSummary,
)
from app.services.linkedin_pdf import read_profile_pages
from app.services.resume.file_security import ResumeFileError, read_resume_upload
from app.services.storage.supabase_storage import StorageClient, get_storage

router = APIRouter(prefix="/career/linkedin-profiles", tags=["linkedin-pdf"])


def _service(response: Response, owner: str = Depends(get_current_user_id), db: Session = Depends(get_db),
             storage: StorageClient = Depends(get_storage)):
    if settings.SUPABASE_STORAGE_BUCKET != "resume":
        raise to_http_exception(ExternalServiceError("Private PDF Storage is unavailable"))
    response.headers["Cache-Control"] = "no-store"
    return LinkedInPdfService(db, owner, storage)


Service = Annotated[LinkedInPdfService, Depends(_service)]
Pdf = Annotated[UploadFile, File()]
Version = Annotated[int, Path(ge=1, le=2_147_483_647)]


def _review_service(response: Response, owner: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return LinkedInReviewService(db, owner)


ReviewService = Annotated[LinkedInReviewService, Depends(_review_service)]


async def _upload(file: UploadFile, service: LinkedInPdfService, previous: SourceRef | None = None):
    try:
        if not settings.LINKEDIN_PDF_UPLOADS_ENABLED:
            raise ExternalServiceError("LinkedIn PDF uploads are paused")
        if previous is not None:
            await run_in_threadpool(service.check_append, previous)
        if not (file.filename or "").lower().endswith(".pdf"):
            raise ResumeFileError("Only LinkedIn profile PDF files are supported")
        validated = await read_resume_upload(file)
        pages, sidebar_lines = await read_profile_pages(validated.content)
        return await run_in_threadpool(service.add, validated.content, pages, previous, sidebar_lines=sidebar_lines)
    except ResumeFileError as exc:
        raise HTTPException(exc.status_code, str(exc)) from None
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.post("", status_code=201)
async def upload_linkedin_pdf(file: Pdf, service: Service) -> LinkedInUpload:
    return await _upload(file, service)


@router.get("")
def list_linkedin_pdfs(service: Service, offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
                       limit: Annotated[int, Query(ge=1, le=100)] = 50) -> list[LinkedInUploadSummary]:
    return service.list(offset, limit)


@router.post("/{source_id}/versions/{version}", status_code=201)
async def append_linkedin_pdf(source_id: Identifier, version: Version, file: Pdf, service: Service) -> LinkedInUpload:
    return await _upload(file, service, SourceRef(source_id=source_id, source_version=version))


@router.get("/{source_id}/versions/{version}")
def get_linkedin_pdf(source_id: Identifier, version: Version, service: Service) -> LinkedInUpload:
    try:
        return service.get(SourceRef(source_id=source_id, source_version=version))
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.post("/{source_id}/versions/{version}/review")
def preview_linkedin_review(
    source_id: Identifier, version: Version, data: LinkedInReviewRequest, service: ReviewService,
) -> LinkedInReviewPreview:
    source = SourceRef(source_id=source_id, source_version=version)
    try:
        return service.preview(source, data.target_id, resume_source=data.resume_source)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.post("/{source_id}/versions/{version}/recommendations")
def list_linkedin_recommendations(
    source_id: Identifier, version: Version, data: LinkedInTargetSelection, service: ReviewService,
) -> list[LinkedInRecommendation]:
    try:
        return service.recommendations(SourceRef(source_id=source_id, source_version=version), data.target_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.post("/{source_id}/versions/{version}/recommendations/copy")
def copy_linkedin_recommendation(
    source_id: Identifier, version: Version, data: LinkedInCopyRequest, service: ReviewService,
) -> LinkedInRecommendation:
    try:
        return service.copy_recommendation(
            SourceRef(source_id=source_id, source_version=version), data.target_id, data.selection,
        )
    except ApplicationError as exc:
        raise to_http_exception(exc) from None


@router.get("/{source_id}/versions/{version}/pdf", response_class=Response, responses={
    200: {"content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}},
})
def download_linkedin_pdf(source_id: Identifier, version: Version, service: Service) -> Response:
    try:
        content = service.download(SourceRef(source_id=source_id, source_version=version))
    except ApplicationError as exc:
        raise to_http_exception(exc) from None
    return Response(content, media_type="application/pdf", headers={
        "Content-Disposition": 'attachment; filename="linkedin-profile.pdf"',
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
    })


@router.delete("/{source_id}", status_code=204)
def delete_linkedin_pdf(source_id: Identifier, service: Service):
    try:
        service.delete(source_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from None
