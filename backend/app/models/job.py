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
    
    # Relationships
    search_results = relationship("SearchResult", back_populates="job_listing")
    
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

class UserJobPreferences(Base):
    """
    User job preferences and filtering criteria
    """
    __tablename__ = "user_job_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)  # User identifier
    
    # Location preferences
    preferred_locations = Column(JSON)  # ["San Francisco, CA", "Austin, TX", "Remote"]
    location_radius = Column(Integer, default=50)  # Miles from preferred locations
    
    # Job preferences
    preferred_job_types = Column(JSON)  # ["Full-time", "Contract"]
    preferred_experience_levels = Column(JSON)  # ["Entry level", "Mid level"]
    preferred_company_sizes = Column(JSON)  # ["Startup", "Large company"]
    
    # Skills and keywords
    required_keywords = Column(JSON)  # Must-have keywords
    excluded_keywords = Column(JSON)  # Avoid these keywords
    
    # Compensation
    min_salary = Column(Integer)  # Minimum acceptable salary
    max_salary = Column(Integer)  # Maximum salary expectation
    
    # Notification settings
    email_notifications = Column(Boolean, default=True)
    notification_frequency = Column(String(50), default="daily")  # daily, weekly
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserJobPreferences {self.user_id}>"

# Legacy model - keep for backward compatibility but deprecate
class SearchQuery(Base):
    """
    DEPRECATED: This model was designed for LinkedIn scraping.
    Use RSSFeedConfiguration for RSS feed-based job aggregation.
    """
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    location = Column(String(255))
    keywords = Column(String(512))
    job_type = Column(String(50))
    experience_level = Column(String(50))
    date_posted = Column(String, nullable=True)
    salary_range = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    schedule = Column(String(50))  # daily, weekly, monthly, etc.
    last_run = Column(DateTime)
    job_metadata = Column(JSON)
    
    # Relationships
    search_results = relationship("SearchResult", back_populates="search_query")
    
    def __repr__(self):
        return f"<SearchQuery {self.title} in {self.location}>"

class SearchResult(Base):
    __tablename__ = "search_results"
    
    id = Column(Integer, primary_key=True, index=True)
    search_query_id = Column(Integer, ForeignKey("search_queries.id"))
    job_listing_id = Column(Integer, ForeignKey("job_listings.id"))
    match_score = Column(Float)  # How well the job matches the search criteria
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    search_query = relationship("SearchQuery", back_populates="search_results")
    job_listing = relationship("JobListing", back_populates="search_results") 

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
    
    # Relationships
    job_scores = relationship("JobScore", back_populates="user_profile")
    daily_digests = relationship("DailyDigest", back_populates="user_profile")
    
    def __repr__(self):
        return f"<UserProfile {self.full_name} ({self.user_id})>"

class JobScore(Base):
    """
    AI-generated compatibility scores between users and jobs
    """
    __tablename__ = "job_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), ForeignKey("user_profiles.user_id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id"), nullable=False, index=True)
    
    # Scoring
    compatibility_score = Column(Float, nullable=False, index=True)  # 0.0 - 100.0
    confidence_score = Column(Float, default=0.0)  # AI confidence in the score
    
    # AI Reasoning
    ai_reasoning = Column(Text)          # Why this score was given
    match_factors = Column(JSON)         # ["skills_match", "location_match", "experience_match"]
    mismatch_factors = Column(JSON)      # Areas where user doesn't match
    
    # Detailed Breakdown
    skills_match_score = Column(Float, default=0.0)    # 0-100
    location_match_score = Column(Float, default=0.0)  # 0-100
    experience_match_score = Column(Float, default=0.0) # 0-100
    salary_match_score = Column(Float, default=0.0)    # 0-100
    culture_match_score = Column(Float, default=0.0)   # 0-100
    
    # User Actions
    user_interested = Column(Boolean)    # User marked as interested
    user_applied = Column(Boolean, default=False)
    user_feedback = Column(String(20))   # "good_match", "poor_match", "not_interested"
    
    # Metadata
    scored_at = Column(DateTime, default=datetime.utcnow, index=True)
    score_version = Column(String(10), default="1.0")  # For model versioning
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="job_scores")
    job_listing = relationship("JobListing")
    
    def __repr__(self):
        return f"<JobScore {self.user_id}:{self.job_id} = {self.compatibility_score}%>"

class DailyDigest(Base):
    """
    AI-generated daily job digest for users
    """
    __tablename__ = "daily_digests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), ForeignKey("user_profiles.user_id"), nullable=False, index=True)
    digest_date = Column(Date, nullable=False, index=True)
    
    # Digest Content
    digest_title = Column(String(255))   # "5 Perfect Matches for Software Engineer"
    digest_summary = Column(Text)        # AI-generated summary
    digest_html = Column(Text)           # Full HTML content for email
    
    # Top Jobs (JSON array of job IDs with scores)
    top_jobs = Column(JSON)              # [{"job_id": 123, "score": 95.5, "reason": "Perfect skills match"}]
    total_new_jobs = Column(Integer, default=0)
    total_matches = Column(Integer, default=0)
    
    # Market Insights
    market_trends = Column(JSON)         # AI-generated market insights
    skill_recommendations = Column(JSON) # Skills to learn based on market
    
    # Delivery Status
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime)
    email_opened = Column(Boolean, default=False)
    email_clicked = Column(Boolean, default=False)
    
    # User Engagement
    user_viewed = Column(Boolean, default=False)
    user_viewed_at = Column(DateTime)
    jobs_clicked = Column(JSON)          # Track which jobs user clicked
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    generation_time_seconds = Column(Float)  # Performance tracking
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="daily_digests")
    
    def __repr__(self):
        return f"<DailyDigest {self.user_id}:{self.digest_date}>"

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
Index('idx_job_scores_user_score', JobScore.user_id, JobScore.compatibility_score.desc())
Index('idx_job_scores_job_score', JobScore.job_id, JobScore.compatibility_score.desc())
Index('idx_daily_digests_user_date', DailyDigest.user_id, DailyDigest.digest_date.desc())
Index('idx_job_applications_user_status', JobApplication.user_id, JobApplication.application_status)
Index('idx_job_applications_user_date', JobApplication.user_id, JobApplication.application_date.desc()) 