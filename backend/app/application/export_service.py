"""Application orchestration for stored PDF exports."""

import asyncio
import functools
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.application.errors import (
    InvalidOperationError,
    RenderError,
    ResourceBusyError,
    ResourceNotFoundError,
)
from app.application.credits import paid_operation
from app.core.config import settings
from app.core.supabase_storage import download_pdf, signed_url, upload_pdf
from app.models.resume_export import ResumeExport
from app.repositories.export_repository import ResumeExportRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume_export import Country, ExportRequest, ExportResponse, RoleTemplate
from app.schemas.resume_v2 import ResumeDocumentJSON
from app.services.pdf.export_options import parse_template_id, sanitize_pdf_filename
from app.services.pdf.renderer import BlankPdfError, PdfRenderTimeout, render_pdf_from_doc


_EXPORT_SEMAPHORE = asyncio.Semaphore(3)


@dataclass(frozen=True)
class PdfDownload:
    content: bytes
    filename: str
    page_count: int | None = None


class ExportApplicationService:
    def __init__(self, session: Session):
        self.session = session
        self.resumes = ResumeRepository(session)
        self.exports = ResumeExportRepository(session)

    async def create(self, request: ExportRequest, user_id: str) -> ExportResponse:
        (
            resume_document_id,
            country,
            role,
            resume,
        ) = self._resolve_request(request, user_id)
        filename = sanitize_pdf_filename(request.filename)
        export_id = str(uuid.uuid4())
        storage_path = f"{user_id}/{export_id}.pdf"

        with paid_operation(self.session, user_id, amount=1, reason="export"):
            try:
                pdf_bytes = await _render_pdf(resume, country.value, role.value)
            except (BlankPdfError, PdfRenderTimeout) as exc:
                self.exports.add(
                    ResumeExport(
                        id=export_id,
                        user_id=user_id,
                        resume_document_id=resume_document_id,
                        resume_version_id=request.resume_version_id,
                        country=country.value,
                        role_template=role.value,
                        storage_path=storage_path,
                        status="timed_out" if isinstance(exc, PdfRenderTimeout) else "errored",
                        error_message=str(exc),
                    )
                )
                detail = (
                    "PDF render timed out; please retry"
                    if isinstance(exc, PdfRenderTimeout)
                    else "PDF render produced a blank file; please retry"
                )
                raise RenderError(detail) from exc

            upload_pdf(pdf_bytes, storage_path)
            self.exports.add(
                ResumeExport(
                    id=export_id,
                    user_id=user_id,
                    resume_document_id=resume_document_id,
                    resume_version_id=request.resume_version_id,
                    country=country.value,
                    role_template=role.value,
                    storage_path=storage_path,
                    status="succeeded",
                    file_size_bytes=len(pdf_bytes),
                )
            )
            url = signed_url(storage_path)
            response = ExportResponse(
                export_id=export_id,
                download_url=url,
                expires_at=_signed_url_expiry(),
                country=country,
                role_template=role,
                filename=filename,
            )
            self.session.commit()
        return response

    def get(self, export_id: str, user_id: str) -> ExportResponse:
        row = self.exports.get_owned_succeeded(export_id, user_id)
        if not row:
            raise ResourceNotFoundError("Export not found")
        return ExportResponse(
            export_id=row.id,
            download_url=signed_url(row.storage_path),
            expires_at=_signed_url_expiry(),
            country=row.country,
            role_template=row.role_template,
        )

    def download(self, export_id: str, user_id: str) -> PdfDownload:
        row = self.exports.get_owned_succeeded(export_id, user_id)
        if not row:
            raise ResourceNotFoundError("Export not found")
        try:
            content = download_pdf(row.storage_path)
        except Exception as exc:
            raise ResourceNotFoundError("Export file not found") from exc
        return PdfDownload(
            content=content,
            filename=sanitize_pdf_filename(f"resume-{export_id}.pdf"),
        )

    def _resolve_request(
        self,
        request: ExportRequest,
        user_id: str,
    ) -> tuple[str, Country, RoleTemplate, ResumeDocumentJSON]:
        if request.resume_version_id:
            owned = self.resumes.get_owned_version(request.resume_version_id, user_id)
            if not owned:
                version = self.resumes.get_version(request.resume_version_id)
                detail = "Version not found" if not version else "Resume document not found"
                raise ResourceNotFoundError(detail)
            version, _ = owned
            try:
                country_value, role_value = parse_template_id(
                    request.template_id or version.template_id or "us-swe"
                )
            except ValueError as exc:
                raise InvalidOperationError(str(exc)) from exc
            return (
                version.resume_document_id,
                Country(country_value),
                RoleTemplate(role_value),
                ResumeDocumentJSON.model_validate(version.parsed_json),
            )

        if not (request.resume_document_id and request.country and request.role_template):
            raise InvalidOperationError(
                "Either resume_version_id OR "
                "(resume_document_id + country + role_template) required"
            )
        document = self.resumes.get_owned_ready(request.resume_document_id, user_id)
        if not document:
            raise ResourceNotFoundError("Resume document not found")
        return (
            request.resume_document_id,
            request.country,
            request.role_template,
            ResumeDocumentJSON.model_validate(document.parsed_json),
        )


async def _render_pdf(resume: ResumeDocumentJSON, country: str, role: str) -> bytes:
    try:
        await asyncio.wait_for(_EXPORT_SEMAPHORE.acquire(), timeout=1)
    except TimeoutError as exc:
        raise ResourceBusyError("PDF export capacity is busy; please retry shortly") from exc
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(render_pdf_from_doc, resume, country=country, role=role),
        )
    finally:
        _EXPORT_SEMAPHORE.release()


def _signed_url_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        seconds=settings.SUPABASE_SIGNED_URL_TTL_SECONDS
    )
