"""Phase-2 PDF export endpoint.

POST /api/v1/exports  — render a resume to PDF, store, return signed URL. Costs 1 credit.
"""
import asyncio
import functools
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.config import settings
from app.core.supabase_storage import signed_url, upload_pdf
from app.db.session import get_db
from app.middleware.credits import credit_transaction
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.resume_export import ResumeExport
from app.schemas.resume import ResumeDocumentJSON
from app.schemas.resume_export import ExportRequest, ExportResponse
from app.services.pdf.renderer import PdfRenderTimeout, render_pdf_from_doc

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("", response_model=ExportResponse, status_code=201)
async def create_export(
    body: ExportRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    # 1. Verify the resume document exists and belongs to the caller.
    doc_row = db.get(ResumeDocument, body.resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Resume document not found")

    # 2. Optionally hydrate from a specific version.
    if body.resume_version_id:
        version = db.get(ResumeVersion, body.resume_version_id)
        if not version or version.resume_document_id != body.resume_document_id:
            raise HTTPException(status_code=404, detail="Version not found")
        doc_json = ResumeDocumentJSON.model_validate(version.parsed_json)
    else:
        doc_json = ResumeDocumentJSON.model_validate(doc_row.parsed_json)

    export_id = str(uuid.uuid4())
    storage_path = f"{current_user_id}/{export_id}.pdf"

    # 3. Debit 1 credit, render, upload. On render hard-fail the context manager rolls back the debit.
    response_payload: ExportResponse | None = None
    with credit_transaction(db, current_user_id, amount=1, reason="export"):
        try:
            # Run sync Playwright renderer in a thread pool to avoid
            # "sync_playwright inside asyncio loop" error in async endpoints.
            loop = asyncio.get_event_loop()
            pdf_bytes = await loop.run_in_executor(
                None,
                functools.partial(
                    render_pdf_from_doc,
                    doc_json,
                    country=body.country.value,
                    role=body.role_template.value,
                ),
            )
        except PdfRenderTimeout as exc:
            db.add(ResumeExport(
                id=export_id,
                user_id=current_user_id,
                resume_document_id=body.resume_document_id,
                resume_version_id=body.resume_version_id,
                country=body.country.value,
                role_template=body.role_template.value,
                storage_path=storage_path,
                status="timed_out",
                error_message=str(exc),
            ))
            raise HTTPException(status_code=500, detail="PDF render timed out; please retry") from exc

        upload_pdf(pdf_bytes, storage_path)
        url = signed_url(storage_path)
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.SUPABASE_SIGNED_URL_TTL_SECONDS
        )

        db.add(ResumeExport(
            id=export_id,
            user_id=current_user_id,
            resume_document_id=body.resume_document_id,
            resume_version_id=body.resume_version_id,
            country=body.country.value,
            role_template=body.role_template.value,
            storage_path=storage_path,
            status="succeeded",
            file_size_bytes=len(pdf_bytes),
        ))
        response_payload = ExportResponse(
            export_id=export_id,
            download_url=url,
            expires_at=expires_at,
            country=body.country,
            role_template=body.role_template,
        )
    db.commit()
    return response_payload


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    row = db.get(ResumeExport, export_id)
    if not row or row.user_id != current_user_id or row.status != "succeeded":
        raise HTTPException(status_code=404, detail="Export not found")
    url = signed_url(row.storage_path)
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.SUPABASE_SIGNED_URL_TTL_SECONDS
    )
    return ExportResponse(
        export_id=row.id,
        download_url=url,
        expires_at=expires_at,
        country=row.country,
        role_template=row.role_template,
    )
