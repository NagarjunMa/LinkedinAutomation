"""
Educational Information Pydantic Schemas

Schemas for educational data validation and serialization.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from enum import Enum


class DegreeTypeEnum(str, Enum):
    """Valid degree types"""
    ASSOCIATE = "Associate's"
    BACHELOR = "Bachelor's"
    MASTER = "Master's"
    DOCTORAL = "Doctoral"
    PHD = "PhD"
    CERTIFICATE = "Certificate"
    DIPLOMA = "Diploma"
    BOOTCAMP = "Bootcamp"
    PROFESSIONAL = "Professional Certificate"


class InstitutionTypeEnum(str, Enum):
    """Valid institution types"""
    UNIVERSITY = "University"
    COLLEGE = "College"
    COMMUNITY_COLLEGE = "Community College"
    TRADE_SCHOOL = "Trade School"
    BOOTCAMP = "Bootcamp"
    ONLINE_PLATFORM = "Online Platform"
    PROFESSIONAL_SCHOOL = "Professional School"


class CareerLevelEnum(str, Enum):
    """Valid career levels"""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"


# Base schemas
class EducationRecordBase(BaseModel):
    """Base schema for education records"""
    institution_name: str = Field(..., min_length=1, max_length=255)
    institution_type: Optional[InstitutionTypeEnum] = None
    institution_location: Optional[str] = Field(None, max_length=255)
    degree_type: DegreeTypeEnum
    degree_name: str = Field(..., min_length=1, max_length=255)
    field_of_study: str = Field(..., min_length=1, max_length=255)
    major: Optional[str] = Field(None, max_length=255)
    minor: Optional[str] = Field(None, max_length=255)
    concentration: Optional[str] = Field(None, max_length=255)


class EducationRecordCreate(EducationRecordBase):
    """Schema for creating education records"""
    # Academic performance
    gpa: Optional[float] = Field(None, ge=0, le=4.0)
    gpa_scale: Optional[float] = Field(4.0, ge=1.0, le=10.0)
    class_rank: Optional[str] = Field(None, max_length=100)
    honors: Optional[List[str]] = Field(default_factory=list)
    awards: Optional[List[str]] = Field(default_factory=list)

    # Timeline
    start_date: date
    end_date: Optional[date] = None
    graduation_date: Optional[date] = None
    expected_graduation: Optional[date] = None
    is_current: Optional[bool] = False
    is_graduated: Optional[bool] = False

    # Academic details
    coursework: Optional[List[str]] = Field(default_factory=list)
    thesis_topic: Optional[str] = None
    research_areas: Optional[List[str]] = Field(default_factory=list)
    academic_projects: Optional[List[str]] = Field(default_factory=list)
    extracurricular: Optional[List[str]] = Field(default_factory=list)

    # Skills gained
    technical_skills_gained: Optional[List[str]] = Field(default_factory=list)
    soft_skills_gained: Optional[List[str]] = Field(default_factory=list)
    programming_languages_learned: Optional[List[str]] = Field(default_factory=list)
    frameworks_learned: Optional[List[str]] = Field(default_factory=list)
    tools_learned: Optional[List[str]] = Field(default_factory=list)

    # Additional info
    study_abroad: Optional[bool] = False
    study_abroad_details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    internships_during: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    part_time_work: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    @validator('end_date', 'graduation_date', 'expected_graduation')
    def validate_dates(cls, v, values):
        if v and 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('gpa')
    def validate_gpa(cls, v, values):
        if v is not None:
            gpa_scale = values.get('gpa_scale', 4.0)
            if v > gpa_scale:
                raise ValueError(f'GPA cannot exceed scale of {gpa_scale}')
        return v


class EducationRecordUpdate(BaseModel):
    """Schema for updating education records"""
    institution_name: Optional[str] = Field(None, min_length=1, max_length=255)
    institution_type: Optional[InstitutionTypeEnum] = None
    institution_location: Optional[str] = Field(None, max_length=255)
    degree_type: Optional[DegreeTypeEnum] = None
    degree_name: Optional[str] = Field(None, min_length=1, max_length=255)
    field_of_study: Optional[str] = Field(None, min_length=1, max_length=255)
    major: Optional[str] = Field(None, max_length=255)
    minor: Optional[str] = Field(None, max_length=255)
    concentration: Optional[str] = Field(None, max_length=255)
    gpa: Optional[float] = Field(None, ge=0, le=4.0)
    is_current: Optional[bool] = None
    is_graduated: Optional[bool] = None


class EducationRecordResponse(EducationRecordBase):
    """Schema for education record responses"""
    id: str
    user_id: str
    gpa: Optional[float] = None
    gpa_scale: Optional[float] = None
    class_rank: Optional[str] = None
    honors: List[str] = []
    awards: List[str] = []
    start_date: date
    end_date: Optional[date] = None
    graduation_date: Optional[date] = None
    is_current: bool
    is_graduated: bool
    coursework: List[str] = []
    technical_skills_gained: List[str] = []
    relevance_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Certification schemas
class CertificationBase(BaseModel):
    """Base schema for certifications"""
    name: str = Field(..., min_length=1, max_length=255)
    issuing_organization: str = Field(..., min_length=1, max_length=255)
    credential_id: Optional[str] = Field(None, max_length=255)
    credential_url: Optional[str] = Field(None, max_length=500)


class CertificationCreate(CertificationBase):
    """Schema for creating certifications"""
    issue_date: date
    expiration_date: Optional[date] = None
    never_expires: Optional[bool] = False
    certification_type: Optional[str] = Field(None, max_length=100)
    skill_level: Optional[str] = Field(None, max_length=50)
    skills_validated: Optional[List[str]] = Field(default_factory=list)
    industry_relevance: Optional[List[str]] = Field(default_factory=list)
    job_roles_relevant: Optional[List[str]] = Field(default_factory=list)
    technology_stack: Optional[List[str]] = Field(default_factory=list)

    @validator('expiration_date')
    def validate_expiration(cls, v, values):
        if v and 'issue_date' in values and v < values['issue_date']:
            raise ValueError('Expiration date must be after issue date')
        return v


class CertificationResponse(CertificationBase):
    """Schema for certification responses"""
    id: str
    user_id: str
    issue_date: date
    expiration_date: Optional[date] = None
    never_expires: bool
    is_active: bool
    skills_validated: List[str] = []
    industry_relevance: List[str] = []
    market_demand_score: Optional[float] = None
    salary_impact_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Online Course schemas
class OnlineCourseBase(BaseModel):
    """Base schema for online courses"""
    course_name: str = Field(..., min_length=1, max_length=255)
    provider: str = Field(..., min_length=1, max_length=255)
    platform: Optional[str] = Field(None, max_length=100)
    instructor: Optional[str] = Field(None, max_length=255)


class OnlineCourseCreate(OnlineCourseBase):
    """Schema for creating online courses"""
    course_type: Optional[str] = Field(None, max_length=100)
    skill_level: Optional[str] = Field(None, max_length=50)
    duration_hours: Optional[float] = Field(None, ge=0)
    completion_percentage: Optional[float] = Field(0.0, ge=0, le=100)
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    skills_learned: Optional[List[str]] = Field(default_factory=list)
    projects_completed: Optional[List[str]] = Field(default_factory=list)
    technologies_used: Optional[List[str]] = Field(default_factory=list)


class OnlineCourseResponse(OnlineCourseBase):
    """Schema for online course responses"""
    id: str
    user_id: str
    completion_percentage: float
    is_completed: bool
    is_certified: bool
    skills_learned: List[str] = []
    relevance_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Academic Project schemas
class AcademicProjectCreate(BaseModel):
    """Schema for creating academic projects"""
    project_name: str = Field(..., min_length=1, max_length=255)
    project_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    education_record_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    technologies_used: Optional[List[str]] = Field(default_factory=list)
    tools_used: Optional[List[str]] = Field(default_factory=list)
    skills_demonstrated: Optional[List[str]] = Field(default_factory=list)
    github_url: Optional[str] = Field(None, max_length=500)
    demo_url: Optional[str] = Field(None, max_length=500)


class AcademicProjectResponse(BaseModel):
    """Schema for academic project responses"""
    id: str
    user_id: str
    project_name: str
    project_type: Optional[str] = None
    description: Optional[str] = None
    technologies_used: List[str] = []
    skills_demonstrated: List[str] = []
    complexity_score: Optional[float] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Comprehensive profile schemas
class EducationalProfileCreate(BaseModel):
    """Schema for creating complete educational profile"""
    education_records: List[EducationRecordCreate] = []
    certifications: List[CertificationCreate] = []
    online_courses: List[OnlineCourseCreate] = []
    academic_projects: List[AcademicProjectCreate] = []


class EducationalProfileResponse(BaseModel):
    """Schema for educational profile responses"""
    education_records: List[EducationRecordResponse] = []
    certifications: List[CertificationResponse] = []
    online_courses: List[OnlineCourseResponse] = []
    academic_projects: List[AcademicProjectResponse] = []
    overall_education_score: Optional[float] = None
    skill_coverage_score: Optional[float] = None
    market_alignment_score: Optional[float] = None


# Educational analysis schemas
class EducationJobMatchAnalysis(BaseModel):
    """Schema for education-job match analysis"""
    education_match_score: float = Field(..., ge=0, le=100)
    degree_relevance_score: float = Field(..., ge=0, le=100)
    skills_match_score: float = Field(..., ge=0, le=100)
    experience_level_match: float = Field(..., ge=0, le=100)
    certification_bonus: float = Field(..., ge=0, le=20)
    institution_prestige_factor: float = Field(..., ge=0.8, le=1.2)
    recommendations: List[str] = []
    skill_gaps: List[str] = []
    recommended_certifications: List[str] = []


class EducationRecommendation(BaseModel):
    """Schema for education recommendations"""
    recommendation_type: str  # course, certification, degree
    title: str
    provider: str
    description: str
    estimated_time: Optional[str] = None
    cost_estimate: Optional[str] = None
    skills_gained: List[str] = []
    career_impact_score: float = Field(..., ge=0, le=100)
    priority: str = Field(..., pattern="^(high|medium|low)$")