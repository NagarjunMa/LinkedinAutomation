"""Phase-1 resume endpoints.

Task 14: POST /api/v1/resumes/upload
Task 15: POST /api/v1/resumes/{id}/evaluate  — ATS + credit debit
Task 16: POST /api/v1/resumes/{id}/rewrite/{bullet_id}  — hallucination-guarded, zero-credit
Task 17: POST /api/v1/resumes/{id}/versions  — apply_changes + persist ResumeVersion
"""
import uuid
import os
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.core.config import settings
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.resume_evaluation_v2 import ResumeEvaluationV2
from app.models.jd_evaluation import JDEvaluation
from app.models.resume_export import ResumeExport
from app.schemas.resume_v2 import ResumeDocumentJSON, ChangeItem
from app.services.resume.parser import parse_resume
from app.services.resume.evaluator import evaluate_resume
from app.services.resume.ats_simulator import simulate_ats
from app.services.resume.rewriter import rewrite_bullet
from app.services.resume.hallucination_guard import HallucinationError
from app.services.storage.supabase_storage import get_storage
from app.middleware.credits import credit_transaction

router = APIRouter(tags=["resumes-v2"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "uploads", "resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Task 14: POST /upload
# ---------------------------------------------------------------------------

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
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds maximum upload size")
    try:
        doc_json = parse_resume(content, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    doc_id = str(uuid.uuid4())
    ext = file.filename.rsplit(".", 1)[-1].lower()

    # Phase 4: upload to Supabase Storage instead of local disk.
    # file_path is kept populated for backward compat (will be deprecated post-backfill).
    storage = get_storage()
    storage_path = storage.upload(
        user_id=current_user_id,
        file_id=doc_id,
        content=content,
        filename=file.filename,
    )

    db_doc = ResumeDocument(
        id=doc_id,
        user_id=current_user_id,
        original_filename=file.filename,
        file_path=storage_path,       # legacy column — mirrors storage_path for one release
        storage_path=storage_path,    # Phase 4 canonical column
        file_type=ext,
        parsed_json=doc_json.model_dump(),
        raw_text=doc_json.raw_text,
    )
    db.add(db_doc)
    db.commit()

    return {"resume_document_id": doc_id, **doc_json.model_dump()}


# ---------------------------------------------------------------------------
# Profile compatibility: list/detail/delete v2 resume documents
# ---------------------------------------------------------------------------

@router.get("/list")
async def list_resumes(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    docs = (
        db.query(ResumeDocument)
        .filter(ResumeDocument.user_id == current_user_id)
        .order_by(ResumeDocument.created_at.desc())
        .all()
    )
    latest_eval_by_doc: dict[str, ResumeEvaluationV2] = {}
    if docs:
        evaluations = (
            db.query(ResumeEvaluationV2)
            .filter(
                ResumeEvaluationV2.user_id == current_user_id,
                ResumeEvaluationV2.resume_document_id.in_([doc.id for doc in docs]),
            )
            .order_by(ResumeEvaluationV2.created_at.desc())
            .all()
        )
        for evaluation in evaluations:
            latest_eval_by_doc.setdefault(evaluation.resume_document_id, evaluation)

    return {
        "resumes": [
            _resume_list_item(
                doc,
                evaluation=latest_eval_by_doc.get(doc.id),
                is_primary=index == 0,
            )
            for index, doc in enumerate(docs)
        ],
        "total_count": len(docs),
        "totalCount": len(docs),
    }


@router.get("/{resume_document_id}")
async def get_resume(
    resume_document_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    doc_row = db.get(ResumeDocument, resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Not found")

    evaluation = (
        db.query(ResumeEvaluationV2)
        .filter(
            ResumeEvaluationV2.user_id == current_user_id,
            ResumeEvaluationV2.resume_document_id == resume_document_id,
        )
        .order_by(ResumeEvaluationV2.created_at.desc())
        .first()
    )
    return {
        "resume": _resume_list_item(doc_row, evaluation=evaluation, is_primary=False),
        "evaluation": _evaluation_payload(evaluation) if evaluation else None,
    }


@router.delete("/{resume_document_id}", status_code=204)
async def delete_resume(
    resume_document_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    doc_row = db.get(ResumeDocument, resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Not found")

    storage_path = doc_row.storage_path or doc_row.file_path
    try:
        get_storage().delete(storage_path)
    except Exception:
        # Database state is authoritative for the app; stale storage objects can
        # be cleaned by an admin job without keeping the profile UI blocked.
        pass

    db.query(ResumeExport).filter(
        ResumeExport.user_id == current_user_id,
        ResumeExport.resume_document_id == resume_document_id,
    ).delete(synchronize_session=False)
    db.query(ResumeEvaluationV2).filter(
        ResumeEvaluationV2.user_id == current_user_id,
        ResumeEvaluationV2.resume_document_id == resume_document_id,
    ).delete(synchronize_session=False)
    db.query(ResumeVersion).filter(
        ResumeVersion.resume_document_id == resume_document_id,
    ).delete(synchronize_session=False)
    db.query(JDEvaluation).filter(
        JDEvaluation.user_id == current_user_id,
        JDEvaluation.resume_document_id == resume_document_id,
    ).delete(synchronize_session=False)
    db.delete(doc_row)
    db.commit()
    return None


def _resume_list_item(
    doc: ResumeDocument,
    evaluation: ResumeEvaluationV2 | None = None,
    is_primary: bool = False,
) -> dict:
    created = doc.created_at.isoformat() if doc.created_at else None
    return {
        "id": doc.id,
        "resume_document_id": doc.id,
        "filename": doc.original_filename,
        "original_filename": doc.original_filename,
        "file_size": 0,
        "file_type": doc.file_type,
        "uploaded_at": created,
        "evaluation_status": "completed" if evaluation else "pending",
        "is_primary": is_primary,
        "evaluation_result": _evaluation_payload(evaluation) if evaluation else None,
    }


def _evaluation_payload(evaluation: ResumeEvaluationV2 | None) -> dict | None:
    if not evaluation:
        return None
    score_breakdown = evaluation.score_breakdown or {
        "content_quality": evaluation.overall_score,
        "role_fit": evaluation.overall_score,
        "evidence_strength": evaluation.overall_score,
        "recruiter_readability": evaluation.overall_score,
    }
    score_explanation = evaluation.score_explanation or []
    top_actions = evaluation.top_actions_before_applying or []
    return {
        "id": evaluation.id,
        "resume_id": evaluation.resume_document_id,
        "resume_document_id": evaluation.resume_document_id,
        "overall_score": evaluation.overall_score,
        "readiness_label": evaluation.readiness_label or "needs_work",
        "score_breakdown": score_breakdown,
        "score_explanation": score_explanation,
        "top_actions_before_applying": top_actions,
        "parser_confidence": evaluation.parser_confidence or "medium",
        "bullet_flags": evaluation.bullet_flags or [],
        "format_issues": evaluation.format_issues or [],
        "ats_score": evaluation.ats_parseability,
        "ats_compliance_score": evaluation.ats_parseability,
        "content_quality_score": score_breakdown.get("content_quality", evaluation.overall_score),
        "experience_points_score": score_breakdown.get("evidence_strength", evaluation.overall_score),
        "job_relevance_score": score_breakdown.get("role_fit", evaluation.overall_score),
        "quality_checks_score": score_breakdown.get("recruiter_readability", evaluation.overall_score),
        "strengths": [
            item.get("reason", "")
            for item in score_explanation
            if item.get("score", 0) >= 80 and item.get("reason")
        ][:3],
        "improvements": top_actions,
        "ats_compatibility": "good" if evaluation.ats_parseability >= 80 else "fair",
        "detailed_feedback": evaluation.summary_critique,
        "keyword_analysis": {
            "relevant": [],
            "missing": [],
            "score": score_breakdown.get("role_fit", 0),
        },
        "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
    }


# ---------------------------------------------------------------------------
# Task 15: POST /{resume_document_id}/evaluate
# ---------------------------------------------------------------------------

class EvalRequest(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=200)


@router.post("/{resume_document_id}/evaluate")
async def evaluate(
    resume_document_id: str,
    body: EvalRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Evaluate a resume and run ATS simulation.

    Costs 1 credit.  Persists the result in resume_evaluations_v2.
    """
    doc_row = db.get(ResumeDocument, resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Not found")

    result_payload = None
    with credit_transaction(db, current_user_id, amount=1, reason="evaluate"):
        doc_json = ResumeDocumentJSON.model_validate(doc_row.parsed_json)
        report = await evaluate_resume(doc_json, target_role=body.target_role, user_id=current_user_id)

        # ATS simulation: download raw bytes from Supabase Storage.
        # Falls back to file_path for rows uploaded before Phase 4 (backfill pending).
        storage = get_storage()
        content_bytes = storage.download(doc_row.storage_path or doc_row.file_path)
        ats = simulate_ats(content_bytes, filename=doc_row.original_filename)

        eval_row = ResumeEvaluationV2(
            id=str(uuid.uuid4()),
            resume_document_id=resume_document_id,
            user_id=current_user_id,
            overall_score=report.overall_score,
            bullet_flags=[f.model_dump() for f in report.bullet_flags],
            format_issues=[i.model_dump() for i in (report.format_issues + ats.format_issues)],
            readiness_label=report.readiness_label,
            score_breakdown=report.score_breakdown.model_dump(),
            score_explanation=[item.model_dump() for item in report.score_explanation],
            top_actions_before_applying=report.top_actions_before_applying,
            parser_confidence=report.parser_confidence,
            summary_critique=report.summary_critique,
            ats_parseability=ats.parseability_score,
            ats_raw_text=ats.raw_text,
            model_version="gpt-4o-2024-08-06",
        )
        db.add(eval_row)
        result_payload = {
            "evaluation_id": eval_row.id,
            "overall_score": report.overall_score,
            "readiness_label": report.readiness_label,
            "score_breakdown": report.score_breakdown.model_dump(),
            "score_explanation": [item.model_dump() for item in report.score_explanation],
            "top_actions_before_applying": report.top_actions_before_applying,
            "parser_confidence": report.parser_confidence,
            "bullet_flags": [f.model_dump() for f in report.bullet_flags],
            "format_issues": [i.model_dump() for i in (report.format_issues + ats.format_issues)],
            "summary_critique": report.summary_critique,
            "ats_parseability": ats.parseability_score,
            "ats_raw_text": ats.raw_text,
        }
    db.commit()
    return result_payload


# ---------------------------------------------------------------------------
# Task 16: POST /{resume_document_id}/rewrite/{bullet_id}
# ---------------------------------------------------------------------------

class RewriteRequest(BaseModel):
    target_role: str
    country: str = "US"
    jd_context: Optional[str] = None


@router.post("/{resume_document_id}/rewrite/{bullet_id}")
async def rewrite(
    resume_document_id: str,
    bullet_id: str,
    body: RewriteRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Rewrite a single bullet — hallucination-guarded, zero-credit cost."""
    doc_row = db.get(ResumeDocument, resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Not found")

    doc_json = ResumeDocumentJSON.model_validate(doc_row.parsed_json)

    original = next(
        (b.text for exp in doc_json.experience for b in exp.bullets if b.id == bullet_id),
        None,
    )
    if original is None:
        raise HTTPException(status_code=404, detail="Bullet not found")

    try:
        result = await rewrite_bullet(
            original=original,
            target_role=body.target_role,
            country=body.country,
            jd_context=body.jd_context,
            user_id=current_user_id,
        )
    except HallucinationError as exc:
        raise HTTPException(status_code=422, detail=f"Rewrite rejected: {exc}")

    return result.model_dump()


# ---------------------------------------------------------------------------
# Task 17: POST /{resume_document_id}/versions
# ---------------------------------------------------------------------------

class VersionRequest(BaseModel):
    parent_version_id: Optional[str] = None
    change_set: list[ChangeItem]


def apply_changes(doc: ResumeDocumentJSON, changes: list[ChangeItem]) -> ResumeDocumentJSON:
    """Apply a list of change items to a ResumeDocumentJSON and return the result.

    Supported change types:
    - bullet_update: update text of bullet with matching id (searches experience AND projects)
    - skills_reorder: replace hard skills with new_skills_order list
    - summary_update: replace summary with new_summary string
    """
    data = doc.model_dump()
    for ch in changes:
        if ch.type == "bullet_update" and ch.bullet_id and ch.new_text:
            # Update across BOTH experience and projects
            for container in (data.get("experience", []), data.get("projects", [])):
                for entry in container:
                    for b in entry.get("bullets", []):
                        if b["id"] == ch.bullet_id:
                            b["text"] = ch.new_text
        elif ch.type == "skills_reorder" and ch.new_skills_order is not None:
            data["skills"]["hard"] = ch.new_skills_order
        elif ch.type == "summary_update" and ch.new_summary is not None:
            data["summary"] = ch.new_summary
    return ResumeDocumentJSON.model_validate(data)


@router.post("/{resume_document_id}/versions", status_code=201)
async def create_version(
    resume_document_id: str,
    body: VersionRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Apply a change_set to a resume and persist it as a new version."""
    doc_row = db.get(ResumeDocument, resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Not found")

    if body.parent_version_id:
        parent = db.get(ResumeVersion, body.parent_version_id)
        if parent is None or parent.resume_document_id != resume_document_id:
            raise HTTPException(status_code=404, detail="Parent version not found")
        base = ResumeDocumentJSON.model_validate(parent.parsed_json)
    else:
        base = ResumeDocumentJSON.model_validate(doc_row.parsed_json)

    new_doc = apply_changes(base, body.change_set)

    version = ResumeVersion(
        id=str(uuid.uuid4()),
        resume_document_id=resume_document_id,
        parent_version_id=body.parent_version_id,
        change_set=[c.model_dump() for c in body.change_set],
        parsed_json=new_doc.model_dump(),
    )
    db.add(version)
    db.commit()

    return {"version_id": version.id}
