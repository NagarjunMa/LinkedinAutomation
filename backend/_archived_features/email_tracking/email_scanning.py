from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Float, ForeignKey
from datetime import datetime
from app.db.base_class import Base


class EmailScanHistory(Base):
    __tablename__ = "email_scan_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    scan_started_at = Column(DateTime, default=datetime.utcnow)
    scan_completed_at = Column(DateTime)
    status = Column(String)  # 'running', 'completed', 'failed'
    emails_scanned = Column(Integer, default=0)
    job_emails_found = Column(Integer, default=0)
    applications_created = Column(Integer, default=0)
    applications_updated = Column(Integer, default=0)
    error_message = Column(Text)
    scan_config = Column(JSON)  # Store scan parameters/filters
    summary = Column(JSON)  # Store detailed results summary


class ProcessedEmail(Base):
    __tablename__ = "processed_emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    email_message_id = Column(String, unique=True, index=True, nullable=False)
    scan_history_id = Column(Integer, ForeignKey("email_scan_history.id"))
    processed_at = Column(DateTime, default=datetime.utcnow)
    is_job_related = Column(Boolean, default=False)
    job_type = Column(String)  # 'application_confirmation', 'interview_request', 'rejection', etc.
    extracted_data = Column(JSON)
    confidence_score = Column(Float)
    action_taken = Column(String)  # 'created_application', 'updated_status', 'ignored', etc.
    related_job_id = Column(Integer, ForeignKey("job_listings.id"))
    created_at = Column(DateTime, default=datetime.utcnow)