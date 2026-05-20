"""Phase-1 resume endpoints — upload and (future) evaluate/rewrite.

Task 14: POST /api/v1/resumes/upload
"""
import uuid
import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.services.resume.parser import parse_resume
from app.models.resume_document import ResumeDocument

router = APIRouter(tags=["resumes-v2"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "uploads", "resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Parse and persist a PDF or DOCX resume.

    Returns the new ``resume_document_id`` plus the structured JSON
    representation of the resume (contact, experience, education, etc.).
    """
    if not file.filename or not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    content = await file.read()
    try:
        doc_json = parse_resume(content, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
    with open(file_path, "wb") as fh:
        fh.write(content)

    ext = file.filename.rsplit(".", 1)[-1].lower()
    db_doc = ResumeDocument(
        id=doc_id,
        user_id=current_user_id,
        original_filename=file.filename,
        file_path=file_path,
        file_type=ext,
        parsed_json=doc_json.model_dump(),
        raw_text=doc_json.raw_text,
    )
    db.add(db_doc)
    db.commit()

    return {"resume_document_id": doc_id, **doc_json.model_dump()}
