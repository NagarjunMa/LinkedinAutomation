from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base_class import Base


class ResumeEvaluationV2(Base):
    __tablename__ = "resume_evaluations_v2"
    id = Column(String, primary_key=True, index=True)
    resume_document_id = Column(String, ForeignKey("resume_documents.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    overall_score = Column(Integer, nullable=False)
    bullet_flags = Column(JSONB, nullable=False)
    format_issues = Column(JSONB, nullable=False)
    readiness_label = Column(String, nullable=False, server_default="needs_work")
    score_breakdown = Column(JSONB, nullable=False, server_default="{}")
    score_explanation = Column(JSONB, nullable=False, server_default="[]")
    top_actions_before_applying = Column(JSONB, nullable=False, server_default="[]")
    parser_confidence = Column(String, nullable=False, server_default="medium")
    summary_critique = Column(Text, nullable=True)
    ats_parseability = Column(Integer, nullable=False)
    ats_raw_text = Column(Text, nullable=False)
    model_version = Column(String, nullable=False)
    cost_usd = Column(Numeric(10, 6), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
