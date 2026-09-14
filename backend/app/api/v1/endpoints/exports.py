"""HTTP adapters for stored resume exports."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.api.dependencies import get_export_application_service
from app.api.error_mapping import to_http_exception
from app.application.errors import ApplicationError
from app.application.export_service import ExportApplicationService
from app.core.auth import get_current_user_id
from app.schemas.resume_export import ExportRequest, ExportResponse


router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("", response_model=ExportResponse, status_code=201)
async def create_export(
    body: ExportRequest,
    service: ExportApplicationService = Depends(get_export_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        return await service.create(body, current_user_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.get("/{export_id}", response_model=ExportResponse)
def get_export(
    export_id: str,
    service: ExportApplicationService = Depends(get_export_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        return service.get(export_id, current_user_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.get(
    "/{export_id}/download",
    response_class=Response,
    responses={200: {
        "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}},
        "headers": {
            "Content-Disposition": {"schema": {"type": "string"}, "description": "PDF attachment filename"},
            "Cache-Control": {"schema": {"type": "string"}, "description": "private, no-store"},
        },
    }},
)
def download_export(
    export_id: str,
    service: ExportApplicationService = Depends(get_export_application_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        download = service.download(export_id, current_user_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc
    return Response(
        content=download.content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{download.filename}"',
            "Cache-Control": "private, no-store",
        },
    )
