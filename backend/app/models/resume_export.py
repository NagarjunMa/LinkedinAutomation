from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.base_class import Base


class ResumeExport(Base):
    __tablename__ = "resume_exports"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    resume_document_id = Column(String, ForeignKey("resume_documents.id"), nullable=False, index=True)
    resume_version_id = Column(String, ForeignKey("resume_versions.id"), nullable=True)
    country = Column(String(2), nullable=False)
    role_template = Column(String(8), nullable=False)
    storage_path = Column(String, nullable=True)
    status = Column(String(16), nullable=False, default="succeeded")
    render_ms = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
