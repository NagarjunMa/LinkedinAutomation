"""Application orchestration for the tailored resume library."""

import asyncio
import functools
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.application.errors import (
    InvalidOperationError,
    RenderError,
    ResourceBusyError,
    ResourceNotFoundError,
)
from app.application.credits import paid_operation
from app.application.export_service import PdfDownload
from app.models.resume_export import ResumeExport
from app.repositories.export_repository import ResumeExportRepository
from app.repositories.jd_repository import JDEvaluationRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume_v2 import ResumeDocumentJSON
from app.schemas.tailored_resume import (
    TailoredDownloadRequest,
    TailoredResumeDetail,
    TailoredResumeListItem,
)
from app.services.pdf.export_options import parse_template_id, sanitize_pdf_filename
from app.services.pdf.renderer import (
    BlankPdfError,
    PdfRenderTimeout,
    get_pdf_page_count,
    render_pdf_from_doc,
)


_DOWNLOAD_SEMAPHORE = asyncio.Semaphore(3)


class TailoredResumeApplicationService:
    def __init__(self, session: Session):
        self.session = session
        self.resumes = ResumeRepository(session)
        self.evaluations = JDEvaluationRepository(session)
        self.exports = ResumeExportRepository(session)

    def list(self, user_id: str) -> list[TailoredResumeListItem]:
        return [
            _list_item(version, document)
            for version, document in self.resumes.list_owned_tailored(user_id)
        ]

    def get(self, version_id: str, user_id: str) -> TailoredResumeDetail:
        version, document = self._owned_version(version_id, user_id)
        evaluation = self.evaluations.get(version.jd_evaluation_id)
        return TailoredResumeDetail(
            **_list_item(version, document).model_dump(),
            resume_json=version.parsed_json,
            source_jd_text=version.source_jd_text or (
                evaluation.jd_text if evaluation else None
            ),
            extracted_requirements=evaluation.extracted_requirements if evaluation else {},
            diff_plan=evaluation.diff_plan if evaluation else {},
            accepted_changes=(
                version.change_set if isinstance(version.change_set, list) else []
            ),
        )

    async def download(
        self,
        version_id: str,
        request: TailoredDownloadRequest,
        user_id: str,
    ) -> PdfDownload:
        version, document = self._owned_version(version_id, user_id)
        try:
            country, role = parse_template_id(
                request.template_id or version.template_id or "us-swe"
            )
        except ValueError as exc:
            raise InvalidOperationError(str(exc)) from exc
        resume = ResumeDocumentJSON.model_validate(version.parsed_json)
        filename = sanitize_pdf_filename(
            request.filename
            or f"{version.company_name or resume.contact.name or 'resume'}-{role}.pdf"
        )

        with paid_operation(self.session, user_id, amount=1, reason="export"):
            try:
                pdf_bytes = await _render_pdf(resume, country, role)
            except (BlankPdfError, PdfRenderTimeout) as exc:
                self.exports.add(
                    ResumeExport(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        resume_document_id=version.resume_document_id,
                        resume_version_id=version.id,
                        country=country,
                        role_template=role,
                        storage_path=None,
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
            self.exports.add(
                ResumeExport(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    resume_document_id=document.id,
                    resume_version_id=version.id,
                    country=country,
                    role_template=role,
                    storage_path=None,
                    status="succeeded",
                    file_size_bytes=len(pdf_bytes),
                    created_at=datetime.now(timezone.utc),
                )
            )
            self.session.commit()
        return PdfDownload(
            content=pdf_bytes,
            filename=filename,
            page_count=get_pdf_page_count(pdf_bytes),
        )

    def _owned_version(self, version_id: str, user_id: str):
        owned = self.resumes.get_owned_version(version_id, user_id)
        if not owned:
            raise ResourceNotFoundError("Tailored resume not found")
        return owned


def _list_item(version, document) -> TailoredResumeListItem:
    changes = version.change_set if isinstance(version.change_set, list) else []
    return TailoredResumeListItem(
        version_id=version.id,
        resume_document_id=version.resume_document_id,
        source_filename=document.original_filename,
        company_name=version.company_name,
        target_role_title=version.target_role_title,
        role_category=version.role_category,
        seniority=version.seniority,
        country_hint=version.country_hint,
        match_score=version.match_score,
        template_id=version.template_id,
        accepted_change_count=len(changes),
        created_at=version.created_at,
        accepted_at=version.accepted_at,
    )


async def _render_pdf(resume: ResumeDocumentJSON, country: str, role: str) -> bytes:
    try:
        await asyncio.wait_for(_DOWNLOAD_SEMAPHORE.acquire(), timeout=1)
    except TimeoutError as exc:
        raise ResourceBusyError("PDF export capacity is busy; please retry shortly") from exc
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(render_pdf_from_doc, resume, country=country, role=role),
        )
    finally:
        _DOWNLOAD_SEMAPHORE.release()
