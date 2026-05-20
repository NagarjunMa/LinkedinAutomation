from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base_class import Base


class JDEvaluation(Base):
    __tablename__ = "jd_evaluations"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    resume_document_id = Column(String, ForeignKey("resume_documents.id"), nullable=False)
    jd_text = Column(Text, nullable=False)
    extracted_requirements = Column(JSONB, nullable=False)
    diff_plan = Column(JSONB, nullable=False)
    match_score = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
