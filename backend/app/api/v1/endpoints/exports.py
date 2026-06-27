"""Phase-2 PDF export endpoint.

POST /api/v1/exports  — render a resume to PDF, store, return signed URL. Costs 1 credit.
"""
import asyncio
import functools
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.config import settings
from app.core.supabase_storage import download_pdf, signed_url, upload_pdf
from app.db.session import get_db
from app.middleware.credits import credit_transaction
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.resume_export import ResumeExport
from app.schemas.resume_v2 import ResumeDocumentJSON
from app.schemas.resume_export import Country, ExportRequest, ExportResponse, RoleTemplate
from app.services.pdf.renderer import BlankPdfError, PdfRenderTimeout, render_pdf_from_doc

router = APIRouter(prefix="/exports", tags=["exports"])
_EXPORT_SEMAPHORE = asyncio.Semaphore(3)

_SAFE_CHARS = re.compile(r"[^a-zA-Z0-9._-]")
_DEFAULT_FILENAME = "resume.pdf"


def _sanitize_filename(name: str | None, default: str = _DEFAULT_FILENAME) -> str:
    """Return a safe, .pdf-suffixed filename.

    Steps:
    1. Strip directory parts (handles both / and \\ separators).
    2. Remove control characters (\\x00-\\x1f) and null bytes.
    3. Allow only [a-zA-Z0-9._-]; replace all other chars with '-'.
    4. Strip leading/trailing '-'.
    5. Fall back to *default* if result is empty after sanitizing.
    6. Ensure filename ends with '.pdf'.
    """
    if not name:
        return default if default.endswith(".pdf") else default + ".pdf"

    # 1. Strip directory traversal
    name = name.replace("\\", "/").split("/")[-1]

    # 2. Remove control chars (includes \x00-\x1f)
    name = re.sub(r"[\x00-\x1f]", "", name)

    # 3. Replace unsafe chars
    name = _SAFE_CHARS.sub("-", name)

    # 4. Strip leading/trailing dashes
    name = name.strip("-")

    # 5. Fall back to default if empty
    if not name:
        name = default.removesuffix(".pdf") if default.endswith(".pdf") else default

    # 6. Ensure .pdf suffix
    if not name.lower().endswith(".pdf"):
        name = name + ".pdf"

    return name


def _parse_template_id(template_id: str) -> tuple[str, str]:
    """Parse a template_id like 'us-swe' or 'us/swe' into (country_upper, role_lower).

    Returns e.g. ('US', 'swe').
    Raises HTTPException 422 if the format is invalid.
    """
    normalized = template_id.replace("/", "-")
    parts = normalized.split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=422, detail=f"Invalid template_id: {template_id}")
    country_str, role_str = parts
    country = country_str.upper()
    role = role_str.lower()
    if country not in ("US", "IN") or role not in ("swe", "ds", "pm"):
        raise HTTPException(status_code=422, detail=f"Invalid template_id: {template_id}")
    return country, role


@router.post("", response_model=ExportResponse, status_code=201)
async def create_export(
    body: ExportRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    # Resolve the two supported request shapes into common variables.
    if body.resume_version_id:
        # Apply-flow shape: resume_version_id + optional template_id
        version = db.get(ResumeVersion, body.resume_version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        # Ownership via parent document
        doc_row = db.get(ResumeDocument, version.resume_document_id)
        if not doc_row or doc_row.user_id != current_user_id:
            raise HTTPException(status_code=404, detail="Resume document not found")

        resume_doc_id = version.resume_document_id
        raw_template_id = body.template_id or version.template_id or "us-swe"
        country_str, role_str = _parse_template_id(raw_template_id)
        country_enum = Country(country_str)
        role_enum = RoleTemplate(role_str)
        doc_json = ResumeDocumentJSON.model_validate(version.parsed_json)
    else:
        # Legacy Phase-2 shape: resume_document_id + country + role_template
        if not (body.resume_document_id and body.country and body.role_template):
            raise HTTPException(
                status_code=422,
                detail="Either resume_version_id OR (resume_document_id + country + role_template) required",
            )
        doc_row = db.get(ResumeDocument, body.resume_document_id)
        if not doc_row or doc_row.user_id != current_user_id:
            raise HTTPException(status_code=404, detail="Resume document not found")

        resume_doc_id = body.resume_document_id
        country_enum = body.country
        role_enum = body.role_template
        doc_json = ResumeDocumentJSON.model_validate(doc_row.parsed_json)

    # 2b. Sanitize download filename (server-side, never trust client input on storage paths).
    safe_filename = _sanitize_filename(body.filename)

    export_id = str(uuid.uuid4())
    storage_path = f"{current_user_id}/{export_id}.pdf"

    # 3. Debit 1 credit, render, upload. On render hard-fail the context manager rolls back the debit.
    response_payload: ExportResponse | None = None
    with credit_transaction(db, current_user_id, amount=1, reason="export"):
        try:
            # Run sync Playwright renderer in a thread pool to avoid
            # "sync_playwright inside asyncio loop" error in async endpoints.
            try:
                await asyncio.wait_for(_EXPORT_SEMAPHORE.acquire(), timeout=1)
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
                        country=country_enum.value,
                        role=role_enum.value,
                    ),
                )
            finally:
                _EXPORT_SEMAPHORE.release()
        except (BlankPdfError, PdfRenderTimeout) as exc:
            db.add(ResumeExport(
                id=export_id,
                user_id=current_user_id,
                resume_document_id=resume_doc_id,
                resume_version_id=body.resume_version_id,
                country=country_enum.value,
                role_template=role_enum.value,
                storage_path=storage_path,
                status="timed_out" if isinstance(exc, PdfRenderTimeout) else "errored",
                error_message=str(exc),
            ))
            detail = (
                "PDF render timed out; please retry"
                if isinstance(exc, PdfRenderTimeout)
                else "PDF render produced a blank file; please retry"
            )
            raise HTTPException(status_code=500, detail=detail) from exc

        # Persist the audit row BEFORE asking for a signed URL. If signed_url()
        # fails after upload_pdf() succeeds, we'd otherwise leak an untracked
        # storage object with no DB record. With this ordering the GET endpoint
        # can always regenerate the URL because the row exists.
        upload_pdf(pdf_bytes, storage_path)
        db.add(ResumeExport(
            id=export_id,
            user_id=current_user_id,
            resume_document_id=resume_doc_id,
            resume_version_id=body.resume_version_id,
            country=country_enum.value,
            role_template=role_enum.value,
            storage_path=storage_path,
            status="succeeded",
            file_size_bytes=len(pdf_bytes),
        ))
        url = signed_url(storage_path)
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.SUPABASE_SIGNED_URL_TTL_SECONDS
        )
        response_payload = ExportResponse(
            export_id=export_id,
            download_url=url,
            expires_at=expires_at,
            country=country_enum,
            role_template=role_enum,
            filename=safe_filename,
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


@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    row = db.get(ResumeExport, export_id)
    if not row or row.user_id != current_user_id or row.status != "succeeded":
        raise HTTPException(status_code=404, detail="Export not found")

    try:
        pdf_bytes = download_pdf(row.storage_path)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Export file not found") from exc

    filename = _sanitize_filename(f"resume-{export_id}.pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, no-store",
        },
    )
