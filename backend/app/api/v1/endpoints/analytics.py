"""Analytics endpoints — zero-credit, read-only, scoped to current user.

GET /api/v1/analytics/jd-progress
    Returns per-JD funnel counts (evaluations → versions → exports) for the
    authenticated user.  Never accepts a user_id query parameter — scoping is
    enforced server-side via the JWT subject claim.
"""
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.models.jd_evaluation import JDEvaluation
from app.models.resume_document import ResumeVersion
from app.models.resume_export import ResumeExport

router = APIRouter(prefix="/analytics", tags=["analytics"])


class JDProgressRow(BaseModel):
    jd_evaluation_id: str
    resume_document_id: str
    match_score: int
    versions_count: int
    exports_count: int


@router.get("/jd-progress", response_model=List[JDProgressRow])
def get_jd_progress(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> List[JDProgressRow]:
    """Return per-JD funnel counts strictly scoped to the current user.

    - versions_count: resume_versions linked to each JD evaluation.
    - exports_count: resume_exports owned by the user (joined via user_id;
      resume_exports does not carry a jd_evaluation_id so we count all exports
      the user has created — a per-document join would require an extra hop that
      isn't modelled yet).
    Credit cost: 0 (pure read query).
    """
    # Count resume_versions per jd_evaluation_id (for this user's evaluations)
    versions_subq = (
        db.query(
            ResumeVersion.jd_evaluation_id.label("jd_evaluation_id"),
            func.count(ResumeVersion.id).label("versions_count"),
        )
        .filter(ResumeVersion.jd_evaluation_id.isnot(None))
        .group_by(ResumeVersion.jd_evaluation_id)
        .subquery()
    )

    # Count succeeded exports per resume_document (user-scoped proxy for exports_count)
    exports_subq = (
        db.query(
            ResumeExport.resume_document_id.label("resume_document_id"),
            func.count(ResumeExport.id).label("exports_count"),
        )
        .filter(
            ResumeExport.user_id == current_user_id,
            ResumeExport.status == "succeeded",
        )
        .group_by(ResumeExport.resume_document_id)
        .subquery()
    )

    rows = (
        db.query(
            JDEvaluation.id.label("jd_evaluation_id"),
            JDEvaluation.resume_document_id.label("resume_document_id"),
            JDEvaluation.match_score.label("match_score"),
            func.coalesce(versions_subq.c.versions_count, 0).label("versions_count"),
            func.coalesce(exports_subq.c.exports_count, 0).label("exports_count"),
        )
        .outerjoin(
            versions_subq,
            versions_subq.c.jd_evaluation_id == JDEvaluation.id,
        )
        .outerjoin(
            exports_subq,
            exports_subq.c.resume_document_id == JDEvaluation.resume_document_id,
        )
        # Defense in depth: always scope to current user, never trust query params
        .filter(JDEvaluation.user_id == current_user_id)
        .order_by(JDEvaluation.created_at.desc())
        .all()
    )

    return [
        JDProgressRow(
            jd_evaluation_id=r.jd_evaluation_id,
            resume_document_id=r.resume_document_id,
            match_score=r.match_score,
            versions_count=r.versions_count,
            exports_count=r.exports_count,
        )
        for r in rows
    ]
