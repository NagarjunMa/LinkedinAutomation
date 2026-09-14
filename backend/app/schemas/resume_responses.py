"""Resume HTTP envelopes, separate from model-output and editing schemas.

List/detail retain legacy aliases until their consumers migrate. Nullable fields
without defaults are required keys: the service emits null rather than omitting them.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.resume_v2 import (
    BulletFlag,
    FormatIssue,
    ResumeDocumentJSON,
    ScoreBreakdown,
    ScoreExplanation,
)


class ResumeUploadResponse(ResumeDocumentJSON):
    resume_document_id: str


class ResumeEvaluationFields(BaseModel):
    """Fields shared by the immediate result and persisted evaluation views."""

    overall_score: int = Field(ge=0, le=100)
    readiness_label: Literal["ready", "minor_edits", "needs_work"]
    score_breakdown: ScoreBreakdown
    score_explanation: list[ScoreExplanation]
    top_actions_before_applying: list[str]
    parser_confidence: Literal["high", "medium", "low"]
    bullet_flags: list[BulletFlag]
    format_issues: list[FormatIssue]


class ResumeEvaluationResponse(ResumeEvaluationFields):
    evaluation_id: str
    summary_critique: str | None
    ats_parseability: int
    ats_raw_text: str


class ResumeKeywordAnalysis(BaseModel):
    relevant: list[str]
    missing: list[str]
    score: int


class ResumeSavedEvaluation(ResumeEvaluationFields):
    id: str
    resume_id: str
    resume_document_id: str
    ats_score: int
    ats_compliance_score: int
    content_quality_score: int
    experience_points_score: int
    job_relevance_score: int
    quality_checks_score: int
    strengths: list[str]
    improvements: list[str]
    ats_compatibility: Literal["good", "fair"]
    detailed_feedback: str | None
    keyword_analysis: ResumeKeywordAnalysis
    # Preserve the service's ISO string verbatim, including legacy naive timestamps.
    created_at: str | None


class ResumeListItem(BaseModel):
    id: str
    resume_document_id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    uploaded_at: str | None
    evaluation_status: Literal["pending", "completed"]
    is_primary: bool
    evaluation_result: ResumeSavedEvaluation | None


class ResumeListResponse(BaseModel):
    resumes: list[ResumeListItem]
    total_count: int
    totalCount: int


class ResumeDetailResponse(BaseModel):
    resume: ResumeListItem
    evaluation: ResumeSavedEvaluation | None


class ResumeVersionResponse(BaseModel):
    version_id: str
