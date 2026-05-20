"""JD analyze endpoint — extract requirements + tailor resume diff plan."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.services.jd.extractor import extract_jd_requirements
from app.services.jd.tailor import tailor_resume_to_jd
from app.services.resume.hallucination_guard import HallucinationError
from app.models.resume_document import ResumeDocument
from app.models.jd_evaluation import JDEvaluation
from app.schemas.resume import ResumeDocumentJSON
from app.middleware.credits import credit_transaction

router = APIRouter(prefix="/jd", tags=["jd"])


class AnalyzeRequest(BaseModel):
    resume_document_id: str
    jd_text: str


@router.post("/analyze")
async def analyze(
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """POST /jd/analyze — extract JD requirements, tailor resume, persist result.

    Costs 2 credits. Returns extracted_requirements + diff_plan.
    """
    doc_row = db.get(ResumeDocument, body.resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Resume document not found")

    result_payload = None
    with credit_transaction(db, current_user_id, amount=2, reason="tailor"):
        jd_ext = await extract_jd_requirements(body.jd_text)
        doc = ResumeDocumentJSON.model_validate(doc_row.parsed_json)
        try:
            plan = await tailor_resume_to_jd(doc, jd_ext)
        except HallucinationError as e:
            raise HTTPException(status_code=422, detail=f"Tailor rejected: {e}")

        row = JDEvaluation(
            id=str(uuid.uuid4()),
            user_id=current_user_id,
            resume_document_id=body.resume_document_id,
            jd_text=body.jd_text,
            extracted_requirements=jd_ext.model_dump(),
            diff_plan=plan.model_dump(),
            match_score=plan.match_score,
        )
        db.add(row)
        result_payload = {
            "jd_evaluation_id": row.id,
            "extracted_requirements": jd_ext.model_dump(),
            "diff_plan": plan.model_dump(),
        }
    db.commit()
    return result_payload
