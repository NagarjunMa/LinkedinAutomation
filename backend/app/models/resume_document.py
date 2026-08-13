from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base_class import Base


class ResumeDocument(Base):
    __tablename__ = "resume_documents"
    __table_args__ = (
        CheckConstraint(
            "storage_status IN ('pending', 'ready', 'deleting')",
            name="ck_resume_documents_storage_status",
        ),
        Index("ix_resume_documents_user_storage_status", "user_id", "storage_status"),
    )
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    storage_path = Column(String, nullable=True)   # Phase 4: Supabase Storage path
    storage_status = Column(String(length=16), nullable=False, default="ready", server_default="ready")
    file_type = Column(String, nullable=False)
    parsed_json = Column(JSONB, nullable=False)
    raw_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ResumeVersion(Base):
    __tablename__ = "resume_versions"
    id = Column(String, primary_key=True, index=True)
    resume_document_id = Column(String, ForeignKey("resume_documents.id"), nullable=False, index=True)
    parent_version_id = Column(String, nullable=True)
    change_set = Column(JSONB, nullable=False)
    parsed_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Tailor-flow additions (2026-05-25)
    jd_evaluation_id = Column(String, ForeignKey("jd_evaluations.id"), nullable=True, index=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    template_id = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    target_role_title = Column(String, nullable=True)
    role_category = Column(String, nullable=True)
    seniority = Column(String, nullable=True)
    country_hint = Column(String, nullable=True)
    match_score = Column(Integer, nullable=True)
    source_jd_text = Column(Text, nullable=True)
