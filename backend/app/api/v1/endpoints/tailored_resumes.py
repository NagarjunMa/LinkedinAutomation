"""Tailored resume library endpoints.

Saved tailored resumes are stored as JSON in ``resume_versions``. PDF downloads
are rendered on demand from that JSON and are not persisted to Supabase Storage.
"""
import asyncio
import functools
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.endpoints.exports import _parse_template_id, _sanitize_filename
from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.middleware.credits import credit_transaction
from app.models.jd_evaluation import JDEvaluation
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.resume_export import ResumeExport
from app.schemas.resume_v2 import ResumeDocumentJSON
from app.services.pdf.renderer import BlankPdfError, PdfRenderTimeout, render_pdf_from_doc

router = APIRouter(prefix="/tailored-resumes", tags=["tailored-resumes"])
_DOWNLOAD_SEMAPHORE = asyncio.Semaphore(3)


class TailoredResumeListItem(BaseModel):
    version_id: str
    resume_document_id: str
    source_filename: str
    company_name: Optional[str] = None
    target_role_title: Optional[str] = None
    role_category: Optional[str] = None
    seniority: Optional[str] = None
    country_hint: Optional[str] = None
    match_score: Optional[int] = None
    template_id: Optional[str] = None
    accepted_change_count: int
    created_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None


class TailoredResumeDetail(TailoredResumeListItem):
    resume_json: dict
    source_jd_text: Optional[str] = None
    extracted_requirements: dict
    diff_plan: dict
    accepted_changes: list[dict]


class TailoredDownloadRequest(BaseModel):
    template_id: Optional[str] = None
    filename: Optional[str] = None


def _list_item(version: ResumeVersion, doc: ResumeDocument) -> TailoredResumeListItem:
    changes = version.change_set if isinstance(version.change_set, list) else []
    return TailoredResumeListItem(
        version_id=version.id,
        resume_document_id=version.resume_document_id,
        source_filename=doc.original_filename,
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


def _get_owned_version(
    db: Session,
    version_id: str,
    current_user_id: str,
) -> tuple[ResumeVersion, ResumeDocument]:
    version = db.get(ResumeVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Tailored resume not found")
    doc = db.get(ResumeDocument, version.resume_document_id)
    if not doc or doc.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Tailored resume not found")
    return version, doc


@router.get("", response_model=list[TailoredResumeListItem])
def list_tailored_resumes(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    rows = (
        db.query(ResumeVersion, ResumeDocument)
        .join(ResumeDocument, ResumeVersion.resume_document_id == ResumeDocument.id)
        .filter(
            ResumeDocument.user_id == current_user_id,
            ResumeVersion.jd_evaluation_id.isnot(None),
        )
        .order_by(ResumeVersion.created_at.desc())
        .all()
    )
    return [_list_item(version, doc) for version, doc in rows]


@router.get("/{version_id}", response_model=TailoredResumeDetail)
def get_tailored_resume(
    version_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    version, doc = _get_owned_version(db, version_id, current_user_id)
    jd_row = db.get(JDEvaluation, version.jd_evaluation_id) if version.jd_evaluation_id else None
    base = _list_item(version, doc).model_dump()
    return TailoredResumeDetail(
        **base,
        resume_json=version.parsed_json,
        source_jd_text=version.source_jd_text or (jd_row.jd_text if jd_row else None),
        extracted_requirements=jd_row.extracted_requirements if jd_row else {},
        diff_plan=jd_row.diff_plan if jd_row else {},
        accepted_changes=version.change_set if isinstance(version.change_set, list) else [],
    )


@router.post("/{version_id}/download")
async def download_tailored_resume(
    version_id: str,
    body: TailoredDownloadRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    version, doc = _get_owned_version(db, version_id, current_user_id)
    request_body = body or TailoredDownloadRequest()
    template_id = request_body.template_id or version.template_id or "us-swe"
    country_str, role_str = _parse_template_id(template_id)
    doc_json = ResumeDocumentJSON.model_validate(version.parsed_json)
    filename = _sanitize_filename(
        request_body.filename
        or f"{version.company_name or doc_json.contact.name or 'resume'}-{role_str}.pdf"
    )

    with credit_transaction(db, current_user_id, amount=1, reason="export"):
        try:
            try:
                await asyncio.wait_for(_DOWNLOAD_SEMAPHORE.acquire(), timeout=1)
            except asyncio.TimeoutError as exc:
                raise HTTPException(
                    status_code=429,
                    detail="PDF export capacity is busy; please retry shortly",
                ) from exc

            try:
                loop = asyncio.get_running_loop()
                pdf_bytes = await loop.run_in_executor(
                    None,
                    functools.partial(
                        render_pdf_from_doc,
                        doc_json,
                        country=country_str,
                        role=role_str,
                    ),
                )
            finally:
                _DOWNLOAD_SEMAPHORE.release()
        except (BlankPdfError, PdfRenderTimeout) as exc:
            db.add(ResumeExport(
                id=str(uuid.uuid4()),
                user_id=current_user_id,
                resume_document_id=version.resume_document_id,
                resume_version_id=version.id,
                country=country_str,
                role_template=role_str,
                storage_path=None,
                status="timed_out" if isinstance(exc, PdfRenderTimeout) else "errored",
                error_message=str(exc),
            ))
            detail = (
                "PDF render timed out; please retry"
                if isinstance(exc, PdfRenderTimeout)
                else "PDF render produced a blank file; please retry"
            )
            raise HTTPException(status_code=500, detail=detail) from exc

        db.add(ResumeExport(
            id=str(uuid.uuid4()),
            user_id=current_user_id,
            resume_document_id=version.resume_document_id,
            resume_version_id=version.id,
            country=country_str,
            role_template=role_str,
            storage_path=None,
            status="succeeded",
            file_size_bytes=len(pdf_bytes),
            created_at=datetime.now(timezone.utc),
        ))
    db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, no-store",
        },
    )
