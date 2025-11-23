"""
Educational Information Models for Enhanced Job Matching

This module contains database models for storing comprehensive educational information
that will be used by AI services for better job matching and resume evaluation.
"""

from sqlalchemy import Column, String, Integer, Float, Date, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base


class EducationRecord(Base):
    """
    Comprehensive educational information for enhanced job matching.

    This model stores detailed education data including institution details,
    degree information, academic performance, and skills gained.
    """
    __tablename__ = "education_records"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)

    # Institution Details
    institution_name = Column(String(255), nullable=False, index=True)
    institution_type = Column(String(100))  # University, College, Community College, Trade School, Bootcamp
    institution_location = Column(String(255))  # City, State/Country
    institution_ranking = Column(Integer)  # For AI matching weight (1-100 scale)
    institution_website = Column(String(255))

    # Degree Information
    degree_type = Column(String(100), nullable=False)  # Bachelor's, Master's, PhD, Certificate, Diploma
    degree_name = Column(String(255), nullable=False)  # B.S. Computer Science, M.A. Business Administration
    field_of_study = Column(String(255), nullable=False, index=True)  # Computer Science, Business, etc.
    major = Column(String(255))  # Primary major
    minor = Column(String(255))  # Minor field of study
    concentration = Column(String(255))  # Specialization within major

    # Academic Performance
    gpa = Column(Float)  # Grade Point Average
    gpa_scale = Column(Float, default=4.0)  # Scale (4.0, 10.0, etc.)
    class_rank = Column(String(100))  # Top 10%, Magna Cum Laude, etc.
    honors = Column(JSON)  # ["Dean's List", "Summa Cum Laude", "Phi Beta Kappa"]
    awards = Column(JSON)  # Academic awards and scholarships

    # Timeline
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)  # Null for current enrollment
    graduation_date = Column(Date)
    expected_graduation = Column(Date)  # For current students
    is_current = Column(Boolean, default=False)
    is_graduated = Column(Boolean, default=False)

    # Academic Details
    coursework = Column(JSON)  # Relevant courses taken
    thesis_topic = Column(Text)  # Thesis or capstone project title/description
    research_areas = Column(JSON)  # Research interests and projects
    academic_projects = Column(JSON)  # Notable academic projects
    extracurricular = Column(JSON)  # Clubs, societies, activities

    # Skills & Learning Outcomes
    technical_skills_gained = Column(JSON)  # Programming languages, tools learned
    soft_skills_gained = Column(JSON)  # Leadership, communication, etc.
    programming_languages_learned = Column(JSON)  # Specific to tech roles
    frameworks_learned = Column(JSON)  # Frameworks and libraries
    tools_learned = Column(JSON)  # Software tools and platforms

    # Additional Information
    study_abroad = Column(Boolean, default=False)
    study_abroad_details = Column(JSON)  # Countries, programs, duration
    internships_during = Column(JSON)  # Internships completed during studies
    part_time_work = Column(JSON)  # Relevant work experience during studies

    # AI Enhancement Fields
    relevance_score = Column(Float)  # AI-calculated relevance to career goals (0-100)
    skills_extracted = Column(JSON)  # AI-extracted skills from courses/projects
    job_market_alignment = Column(JSON)  # How education aligns with job market demands

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # user = relationship("User", back_populates="education_records")


class Certification(Base):
    """
    Professional certifications, licenses, and credentials.

    Tracks industry certifications that enhance job matching accuracy.
    """
    __tablename__ = "certifications"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)

    # Certification Details
    name = Column(String(255), nullable=False, index=True)
    issuing_organization = Column(String(255), nullable=False)
    credential_id = Column(String(255))  # Certification ID/number
    credential_url = Column(String(500))  # Verification URL

    # Timeline
    issue_date = Column(Date, nullable=False)
    expiration_date = Column(Date)
    never_expires = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Certification Details
    certification_type = Column(String(100))  # Professional, Technical, Industry-specific
    skill_level = Column(String(50))  # Beginner, Intermediate, Advanced, Expert
    preparation_hours = Column(Integer)  # Hours of study/preparation
    exam_score = Column(String(100))  # Score achieved (if applicable)

    # Skills and Relevance
    skills_validated = Column(JSON)  # Skills this certification validates
    industry_relevance = Column(JSON)  # Industries where this cert is valuable
    job_roles_relevant = Column(JSON)  # Job roles that value this certification
    technology_stack = Column(JSON)  # Technologies/tools covered

    # AI Enhancement
    market_demand_score = Column(Float)  # AI-calculated market demand (0-100)
    salary_impact_score = Column(Float)  # Estimated salary impact (0-100)
    job_matching_weight = Column(Float, default=1.0)  # Weight in job matching algorithm

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OnlineCourse(Base):
    """
    Online courses, bootcamps, and self-directed learning.

    Tracks modern learning approaches like online courses, MOOCs, bootcamps.
    """
    __tablename__ = "online_courses"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)

    # Course Details
    course_name = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=False)  # Coursera, Udemy, Pluralsight, etc.
    platform = Column(String(100))  # Online platform
    instructor = Column(String(255))
    course_url = Column(String(500))

    # Course Information
    course_type = Column(String(100))  # MOOC, Bootcamp, Specialization, Certificate
    skill_level = Column(String(50))  # Beginner, Intermediate, Advanced
    duration_hours = Column(Float)  # Course duration in hours
    completion_percentage = Column(Float, default=0.0)  # 0-100

    # Timeline
    start_date = Column(Date)
    completion_date = Column(Date)
    certificate_date = Column(Date)
    is_completed = Column(Boolean, default=False)
    is_certified = Column(Boolean, default=False)

    # Learning Outcomes
    skills_learned = Column(JSON)  # Skills acquired
    projects_completed = Column(JSON)  # Projects built during course
    technologies_used = Column(JSON)  # Technologies/tools used
    course_rating = Column(Float)  # User's rating of the course

    # Verification
    certificate_id = Column(String(255))
    certificate_url = Column(String(500))
    is_verified = Column(Boolean, default=False)

    # AI Enhancement
    relevance_score = Column(Float)  # Relevance to career goals
    skill_validation_score = Column(Float)  # How well it validates claimed skills

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AcademicProject(Base):
    """
    Academic and personal projects demonstrating skills.

    Detailed project information for AI-powered skill assessment.
    """
    __tablename__ = "academic_projects"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    education_record_id = Column(String, ForeignKey("education_records.id"), nullable=True)

    # Project Details
    project_name = Column(String(255), nullable=False)
    project_type = Column(String(100))  # Academic, Personal, Open Source, Hackathon
    description = Column(Text)
    detailed_description = Column(Text)  # More comprehensive description

    # Timeline and Context
    start_date = Column(Date)
    end_date = Column(Date)
    is_ongoing = Column(Boolean, default=False)
    course_context = Column(String(255))  # Which course/class it was for
    team_size = Column(Integer)
    role_in_project = Column(String(255))  # Lead Developer, Team Member, etc.

    # Technical Details
    technologies_used = Column(JSON)  # Programming languages, frameworks
    tools_used = Column(JSON)  # Development tools, platforms
    project_scale = Column(String(100))  # Small, Medium, Large
    lines_of_code = Column(Integer)  # Approximate LOC

    # Outcomes and Impact
    project_outcomes = Column(JSON)  # What was achieved
    challenges_overcome = Column(JSON)  # Technical challenges solved
    skills_demonstrated = Column(JSON)  # Skills this project demonstrates
    learning_outcomes = Column(JSON)  # What was learned

    # Links and Documentation
    github_url = Column(String(500))
    demo_url = Column(String(500))
    documentation_url = Column(String(500))
    presentation_url = Column(String(500))

    # Recognition
    awards_received = Column(JSON)  # Any awards or recognition
    grade_received = Column(String(50))  # Grade if academic project
    peer_reviews = Column(JSON)  # Peer feedback if available

    # AI Enhancement
    complexity_score = Column(Float)  # AI-calculated project complexity
    skill_demonstration_score = Column(JSON)  # Score per skill demonstrated
    industry_relevance = Column(Float)  # How relevant to industry needs

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())