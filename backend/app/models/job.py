from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float, Index, Date
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class JobListing(Base):
    __tablename__ = "job_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    description = Column(Text)
    requirements = Column(Text)
    job_type = Column(String(50))  # Full-time, Part-time, Contract, etc.
    experience_level = Column(String(50))  # Entry, Mid, Senior, etc.
    salary_range = Column(String(100))
    skills = Column(JSON)  # List of required skills
    application_url = Column(Text)
    source = Column(String(50))  # linkedin, indeed, url_extraction, etc.
    source_url = Column(Text)
    is_active = Column(Boolean, default=True)
    posted_date = Column(DateTime)
    extracted_date = Column(DateTime, default=datetime.utcnow)
    applied = Column(Boolean, default=False)  # Track application status
    applied_date = Column(DateTime)  # When application was submitted
    
    # New comprehensive application status system
    application_status = Column(String(50), default="pending")  # applied, want_to_apply, maybe_later, not_interested
    application_notes = Column(Text)  # User notes about the application
    application_context = Column(Text)  # Context for why this status was chosen
    
    # AI matching fields
    compatibility_score = Column(Float)  # AI-generated compatibility score (0-100)
    ai_insights = Column(Text)  # AI-generated insights about the job match

    # Relationships (referral models currently not implemented)

    def __repr__(self):
        return f"<JobListing {self.title} at {self.company}>"

class UserProfile(Base):
    """
    AI-extracted user profile information from resumes
    """
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, unique=True, index=True)
    
    # Personal Information
    full_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    location = Column(String(255))
    work_authorization = Column(String(100))
    
    # Professional Summary
    years_of_experience = Column(Float, default=0.0)
    career_level = Column(String(50))  # "entry", "mid", "senior"
    professional_summary = Column(Text)
    
    # Skills & Technologies (JSON arrays)
    programming_languages = Column(JSON)
    frameworks_libraries = Column(JSON)
    tools_platforms = Column(JSON)
    soft_skills = Column(JSON)
    
    # Experience
    job_titles = Column(JSON)
    companies = Column(JSON)
    industries = Column(JSON)
    experience_descriptions = Column(JSON)
    
    # Education
    degrees = Column(JSON)
    institutions = Column(JSON)
    graduation_years = Column(JSON)
    relevant_coursework = Column(JSON)
    
    # Job Preferences
    desired_roles = Column(JSON)
    preferred_locations = Column(JSON)
    salary_range_min = Column(Integer)
    salary_range_max = Column(Integer)
    job_types = Column(JSON)
    company_size_preference = Column(JSON)
    
    # AI-Generated Insights
    ai_profile_summary = Column(Text)
    ai_strengths = Column(JSON)
    ai_improvement_areas = Column(JSON)
    ai_career_advice = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_resume_upload = Column(DateTime)
    
    def __repr__(self):
        return f"<UserProfile {self.full_name} ({self.user_id})>"

class JobApplication(Base):
    """Track user job applications and their status"""
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id"), nullable=False, index=True)
    
    # Application Status Tracking
    application_status = Column(String(50), default="interested", index=True)
    application_source = Column(String(100))
    application_date = Column(DateTime, default=datetime.utcnow)
    
    # External Application Tracking
    external_application_id = Column(String(255))
    application_url = Column(String(1000))
    source_url = Column(String(1000))
    
    # URL Extraction Metadata
    extraction_metadata = Column(JSON)
    
    # User Notes and Follow-up
    user_notes = Column(Text)
    follow_up_date = Column(Date)
    interview_date = Column(DateTime)
    
    # Response Tracking
    company_response = Column(Boolean, default=False)
    response_date = Column(DateTime)
    rejection_reason = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_listing = relationship("JobListing")
    
    def __repr__(self):
        return f"<JobApplication {self.user_id}:{self.job_id}:{self.application_status}>"

# Add indexes for better performance

# Composite indexes for efficient queries
Index('idx_job_applications_user_status', JobApplication.user_id, JobApplication.application_status)
Index('idx_job_applications_user_date', JobApplication.user_id, JobApplication.application_date.desc()) 