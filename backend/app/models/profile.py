from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Date, JSON
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

    # Enhanced profile fields for comprehensive user context
    referral_template = Column(Text, nullable=True)  # Editable referral email template

    # Work Experience (JSON array)
    work_experiences = Column(JSON, nullable=True)
    # Structure: [{"job_title": str, "company": str, "location": str, "start_date": str,
    #             "end_date": str, "description": str, "is_current": bool, "achievements": [str]}]

    # Project Experience (JSON array)
    project_experiences = Column(JSON, nullable=True)
    # Structure: [{"name": str, "description": str, "tech_stack": [str], "url": str,
    #             "start_date": str, "end_date": str, "role": str, "key_features": [str]}]

    # Education Details (JSON array)
    education_details = Column(JSON, nullable=True)
    # Structure: [{"degree": str, "field_of_study": str, "school": str, "location": str,
    #             "graduation_year": int, "gpa": str, "relevant_coursework": [str], "honors": [str]}]

    # Skills categorization (enhanced from basic skills)
    technical_skills = Column(JSON, nullable=True)  # [{"category": "Languages", "skills": ["Python", "JavaScript"]}]
    soft_skills = Column(JSON, nullable=True)  # ["Leadership", "Communication", "Problem Solving"]

    # Career preferences
    career_goals = Column(Text, nullable=True)  # Long-term career objectives
    preferred_work_environment = Column(JSON, nullable=True)  # ["Remote", "Hybrid", "On-site"]
    salary_expectations = Column(JSON, nullable=True)  # {"min": 80000, "max": 120000, "currency": "USD"}

    # Social/Professional links
    linkedin_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    personal_website = Column(String, nullable=True)

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