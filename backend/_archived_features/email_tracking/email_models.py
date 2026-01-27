from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


class UserGmailConnection(Base):
    __tablename__ = "user_gmail_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    email = Column(String, nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expiry = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailEvent(Base):
    __tablename__ = "email_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    gmail_connection_id = Column(Integer, ForeignKey("user_gmail_connections.id"))
    message_id = Column(String, unique=True, index=True, nullable=False)
    thread_id = Column(String, index=True, nullable=False)
    sender = Column(String)
    recipient = Column(String)
    subject = Column(String)
    body = Column(Text)
    snippet = Column(String)
    date = Column(DateTime)
    labels = Column(JSON)
    is_job_related = Column(Boolean, default=False)
    job_classification = Column(JSON)
    extracted_company = Column(String)
    extracted_position = Column(String)
    extracted_status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    gmail_connection = relationship("UserGmailConnection", backref="email_events")


class EmailSyncLog(Base):
    __tablename__ = "email_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    gmail_connection_id = Column(Integer, ForeignKey("user_gmail_connections.id"))
    sync_type = Column(String)  # 'full' or 'incremental'
    status = Column(String)  # 'started', 'completed', 'failed'
    emails_processed = Column(Integer, default=0)
    job_related_found = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    gmail_connection = relationship("UserGmailConnection", backref="sync_logs")