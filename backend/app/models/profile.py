from sqlalchemy import Column, String, Text, Integer, DateTime, UUID, ForeignKey, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import uuid


class ProfileInfo(Base):
    """Extended user profile information"""
    __tablename__ = "profile_info"

    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    target_job_titles = Column(JSON)  # ["Software Engineer", "Frontend Developer"]
    preferred_locations = Column(JSON)  # ["Boston", "Remote", "San Francisco"]
    minimum_salary = Column(Integer, nullable=True)
    experience_level = Column(String, nullable=True)  # "New Grad", "0-1 years", "1-3 years"
    graduation_date = Column(Date, nullable=True)
    university = Column(String, nullable=True)
    background_summary = Column(Text, nullable=True)  # For referral emails
    email_signature = Column(Text, nullable=True)  # For referral emails
    primary_resume_id = Column(String, nullable=True)  # Reference to resume evaluation

    # New fields for enhanced profile
    referral_template = Column(Text, nullable=True)  # Editable referral email template
    work_experiences = Column(JSON, nullable=True)  # [{"job_title": "", "company": "", "location": "", "start_date": "", "end_date": ""}]
    education_history = Column(JSON, nullable=True)  # [{"university": "", "degree": "", "field": "", "location": "", "start_date": "", "end_date": ""}]

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profile_info")


class UserSettings(Base):
    """User application settings and preferences"""
    __tablename__ = "profile_settings"

    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True, index=True)

    # Email Notifications
    email_notifications = Column(JSON, default=lambda: {
        "application_updates": True,
        "interview_reminders": True,
        "weekly_digest": True,
        "referral_responses": True
    })
    notification_frequency = Column(String, default="realtime")  # realtime, daily, weekly

    # Email Tracking Settings
    email_forwarding_enabled = Column(String, default="inactive")  # active, inactive
    forwarding_address = Column(String, nullable=True)
    last_email_check = Column(DateTime(timezone=True), nullable=True)

    # Privacy Settings
    data_retention_days = Column(Integer, default=365)
    analytics_enabled = Column(String, default="enabled")  # enabled, disabled

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="settings")


class ProfileChangeHistory(Base):
    """Track profile updates for audit purposes"""
    __tablename__ = "profile_change_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    field_changed = Column(String, nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")