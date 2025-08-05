from datetime import datetime, date
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
    source = Column(String(50))  # linkedin, indeed, rss_app_texas, etc.
    source_url = Column(Text)
    is_active = Column(Boolean, default=True)
    posted_date = Column(DateTime)
    extracted_date = Column(DateTime, default=datetime.utcnow)
    applied = Column(Boolean, default=False)  # Track application status
    applied_date = Column(DateTime)  # When application was submitted
    
    # Relationships - removed unused relationships
    
    def __repr__(self):
        return f"<JobListing {self.title} at {self.company}>"

class RSSFeedConfiguration(Base):
    """
    New model for managing RSS feeds - replaces SearchQuery for RSS-based architecture
    """
    __tablename__ = "rss_feed_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Texas Software Engineers", "California Developers"
    feed_url = Column(Text, nullable=False)  # RSS.app feed URL
    source_type = Column(String(50), default="rss_app")  # rss_app, indeed_rss, etc.
    
    # Feed filtering/preferences
    location_filter = Column(String(255))  # Optional location filtering
    keyword_filter = Column(String(512))  # Optional keyword filtering  
    job_type_filter = Column(String(50))  # Optional job type filtering
    experience_filter = Column(String(50))  # Optional experience filtering
    
    # Feed management
    is_active = Column(Boolean, default=True)
    refresh_interval = Column(Integer, default=3600)  # Seconds between refreshes (60 min default)
    last_refresh = Column(DateTime)
    last_job_count = Column(Integer, default=0)  # Track job count for monitoring
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))  # Optional user tracking
    description = Column(Text)  # Human-readable description
    tags = Column(JSON)  # Tags for categorization: ["state:texas", "level:senior", "type:remote"]
    
    def __repr__(self):
        return f"<RSSFeedConfiguration {self.name}>"

# REMOVED: UserJobPreferences model - functionality merged into UserProfile

# REMOVED: SearchQuery and SearchResult models - deprecated and replaced by RSS feeds

# =====================================================
# AI-POWERED JOB MATCHING SYSTEM MODELS
# =====================================================

class UserProfile(Base):
    """
    AI-extracted user profile information from resumes
    Replaces the need to store actual resume files
    """
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, unique=True, index=True)
    
    # Personal Information
    full_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    location = Column(String(255))  # Current location
    work_authorization = Column(String(100))  # "US Citizen", "H1B", "F1 OPT", etc.
    
    # Professional Summary
    years_of_experience = Column(Float, default=0.0)
    career_level = Column(String(50))  # "entry", "mid", "senior"
    professional_summary = Column(Text)  # AI-generated summary
    
    # Skills & Technologies (JSON arrays)
    programming_languages = Column(JSON)  # ["Python", "JavaScript", "Java"]
    frameworks_libraries = Column(JSON)  # ["React", "Django", "Spring Boot"]
    tools_platforms = Column(JSON)      # ["AWS", "Docker", "Git"]
    soft_skills = Column(JSON)          # ["Leadership", "Communication"]
    
    # Experience
    job_titles = Column(JSON)            # Previous job titles
    companies = Column(JSON)             # Previous companies
    industries = Column(JSON)            # Industry experience
    experience_descriptions = Column(JSON)  # Key achievements/responsibilities
    
    # Education
    degrees = Column(JSON)               # ["B.S. Computer Science", "M.S. Data Science"]
    institutions = Column(JSON)          # ["Stanford University", "MIT"]
    graduation_years = Column(JSON)      # [2020, 2022]
    relevant_coursework = Column(JSON)   # ["Machine Learning", "Algorithms"]
    
    # Job Preferences (integrated from UserJobPreferences)
    desired_roles = Column(JSON)         # ["Software Engineer", "Data Scientist"]
    preferred_locations = Column(JSON)   # ["San Francisco", "Remote"]
    salary_range_min = Column(Integer)
    salary_range_max = Column(Integer)
    job_types = Column(JSON)             # ["Full-time", "Contract"]
    company_size_preference = Column(JSON)  # ["Startup", "Mid-size", "Enterprise"]
    
    # AI-Generated Insights
    ai_profile_summary = Column(Text)    # GPT-generated profile summary
    ai_strengths = Column(JSON)          # AI-identified strengths
    ai_improvement_areas = Column(JSON)  # AI-suggested improvement areas
    ai_career_advice = Column(Text)      # AI-generated career advice
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_resume_upload = Column(DateTime)
    
    # Relationships - removed unused relationships
    
    def __repr__(self):
        return f"<UserProfile {self.full_name} ({self.user_id})>"

# REMOVED: JobScore and DailyDigest models - not actively used in current application

# =====================================================
# JOB APPLICATION TRACKING
# =====================================================

class JobApplication(Base):
    """Track user job applications and their status"""
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id"), nullable=False, index=True)
    
    # Application Status Tracking
    application_status = Column(String(50), default="interested", index=True)  # interested, applied, interviewed, rejected, hired
    application_source = Column(String(100))  # direct, indeed, linkedin, referral
    application_date = Column(DateTime, default=datetime.utcnow)
    
    # External Application Tracking
    external_application_id = Column(String(255))  # ID from external job board
    application_url = Column(String(1000))  # Direct application link
    source_url = Column(String(1000))  # Original URL if extracted from web
    
    # URL Extraction Metadata (for AI-extracted jobs)
    extraction_metadata = Column(JSON)  # Store extraction confidence, method, etc.
    
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
from sqlalchemy import Index

# Composite indexes for efficient queries
Index('idx_job_applications_user_status', JobApplication.user_id, JobApplication.application_status)
Index('idx_job_applications_user_date', JobApplication.user_id, JobApplication.application_date.desc()) 