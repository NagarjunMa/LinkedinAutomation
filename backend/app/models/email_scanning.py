from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, Boolean, ForeignKey, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import uuid


class EmailScanHistory(Base):
    """Track email scanning operations"""
    __tablename__ = "email_scan_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    scan_type = Column(String, nullable=False)  # 'full' or 'urgent'
    emails_processed = Column(Integer, default=0)
    status_updates_made = Column(Integer, default=0)
    urgent_emails_found = Column(Integer, default=0)
    scan_started_at = Column(DateTime(timezone=True), server_default=func.now())
    scan_completed_at = Column(DateTime(timezone=True), nullable=True)
    errors = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<EmailScanHistory(id={self.id}, user_id={self.user_id}, type={self.scan_type})>"


class ProcessedEmail(Base):
    """Store processed job-related emails"""
    __tablename__ = "processed_emails"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id"), nullable=True, index=True)
    email_from = Column(String, nullable=True)
    email_subject = Column(String, nullable=True)
    email_body = Column(Text, nullable=True)
    email_type = Column(String, nullable=True)  # confirmation, interview_invitation, rejection, offer
    received_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    status_update_applied = Column(Boolean, default=False)
    parsed_data = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User")
    job = relationship("JobListing")

    def __repr__(self):
        return f"<ProcessedEmail(id={self.id}, user_id={self.user_id}, type={self.email_type})>"
