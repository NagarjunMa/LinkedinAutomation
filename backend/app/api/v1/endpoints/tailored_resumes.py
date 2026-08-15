"""HTTP adapters for the tailored resume library."""

from fastapi import APIRouter, Body, Depends
from fastapi.responses import Response

from app.api.dependencies import get_tailored_resume_application_service
from app.api.error_mapping import to_http_exception
from app.application.errors import ApplicationError
from app.application.tailored_resume_service import TailoredResumeApplicationService
from app.core.auth import get_current_user_id
from app.schemas.tailored_resume import (
    TailoredDownloadRequest,
    TailoredResumeDetail,
    TailoredResumeListItem,
)


router = APIRouter(prefix="/tailored-resumes", tags=["tailored-resumes"])


@router.get("", response_model=list[TailoredResumeListItem])
def list_tailored_resumes(
    service: TailoredResumeApplicationService = Depends(
        get_tailored_resume_application_service
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    return service.list(current_user_id)


@router.get("/{version_id}", response_model=TailoredResumeDetail)
def get_tailored_resume(
    version_id: str,
    service: TailoredResumeApplicationService = Depends(
        get_tailored_resume_application_service
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        return service.get(version_id, current_user_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.post("/{version_id}/download")
async def download_tailored_resume(
    version_id: str,
    body: TailoredDownloadRequest | None = Body(default=None),
    service: TailoredResumeApplicationService = Depends(
        get_tailored_resume_application_service
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        download = await service.download(
            version_id,
            body or TailoredDownloadRequest(),
            current_user_id,
        )
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc
    return Response(
        content=download.content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{download.filename}"',
            "Cache-Control": "private, no-store",
            "X-Resume-Page-Count": str(download.page_count),
        },
    )
