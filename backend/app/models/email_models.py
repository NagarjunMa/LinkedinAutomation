from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class UserGmailConnection(Base):
    """Track Gmail connections for users using Google OAuth"""
    __tablename__ = "user_gmail_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)  # Using string to match existing user_id pattern
    
    # Google OAuth identifiers
    google_user_id = Column(String(255), unique=True, nullable=True, index=True)
    gmail_email = Column(String(255), nullable=True)
    
    # OAuth tokens (encrypted in production)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    
    # Connection status
    is_authorized = Column(Boolean, default=False)
    
    # Simple sync tracking
    last_sync_at = Column(DateTime, nullable=True)
    total_emails_processed = Column(Integer, default=0)
    
    # Settings
    sync_enabled = Column(Boolean, default=True)
    auto_update_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    email_events = relationship("EmailEvent", back_populates="gmail_connection")
    
    def __repr__(self):
        return f"<UserGmailConnection {self.user_id} - Gmail ({'✓' if self.is_authorized else '✗'})>"
    
    @property
    def status_display(self):
        if self.is_authorized:
            return "Connected"
        return "Not Connected"
    
    @property
    def is_token_expired(self):
        """Check if the access token is expired"""
        if not self.token_expiry:
            return True
        return datetime.utcnow() > self.token_expiry

class EmailEvent(Base):
    """Track individual email events and classifications"""
    __tablename__ = "email_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic relationships
    user_id = Column(String(100), nullable=False, index=True)
    gmail_connection_id = Column(Integer, ForeignKey("user_gmail_connections.id"), nullable=False)
    
    # Email identifiers
    email_message_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Email content
    sender_email = Column(String(255), nullable=False)
    sender_name = Column(String(255), nullable=True)
    subject = Column(Text, nullable=False)
    email_received_at = Column(DateTime, nullable=False, index=True)
    
    # Classification
    email_type = Column(String(20), nullable=False, default='unknown', index=True)  # rejection, interview, offer, update, confirmation, unknown
    confidence_score = Column(Float, default=0.0)
    company_name = Column(String(255), nullable=True, index=True)
    
    # Job matching
    matched_job_listing_id = Column(Integer, ForeignKey("job_listings.id"), nullable=True)
    
    # Status tracking
    status_updated = Column(Boolean, default=False)
    user_reviewed = Column(Boolean, default=False)
    
    # AI data (JSON field)
    ai_data = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    gmail_connection = relationship("UserGmailConnection", back_populates="email_events")
    # job_listing = relationship("JobListing")  # Commented out to avoid import issues
    
    def __repr__(self):
        return f"<EmailEvent {self.sender_email} - {self.email_type}>"
    
    @property
    def needs_review(self):
        return self.confidence_score < 0.8 and not self.user_reviewed
    
    def mark_reviewed(self):
        self.user_reviewed = True
        self.save()

# Simple sync log for debugging
class EmailSyncLog(Base):
    """Track email sync operations"""
    __tablename__ = "email_sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    emails_found = Column(Integer, default=0)
    emails_processed = Column(Integer, default=0)
    status = Column(String(20), default='completed')  # started, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<EmailSyncLog {self.user_id} - {self.status} ({self.created_at})>"

# Create indexes for better performance
Index('idx_email_events_user_type', EmailEvent.user_id, EmailEvent.email_type)
Index('idx_email_events_confidence', EmailEvent.confidence_score)
Index('idx_email_events_company', EmailEvent.company_name)
Index('idx_gmail_connections_user', UserGmailConnection.user_id)
Index('idx_sync_logs_user_status', EmailSyncLog.user_id, EmailSyncLog.status) 