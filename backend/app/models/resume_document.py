from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base_class import Base


class ResumeDocument(Base):
    __tablename__ = "resume_documents"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    storage_path = Column(String, nullable=True)   # Phase 4: Supabase Storage path
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
