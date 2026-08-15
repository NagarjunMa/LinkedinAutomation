from typing import Any, Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from enum import Enum

class TimeRange(str, Enum):
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_3_MONTHS = "last_3_months"


class ApplicationStatus(str, Enum):
    INTERESTED = "interested"
    PENDING = "pending"
    WANT_TO_APPLY = "want_to_apply"
    MAYBE_LATER = "maybe_later"
    NOT_INTERESTED = "not_interested"
    APPLIED = "applied"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEWED = "interviewed"
    REJECTED = "rejected"
    HIRED = "hired"


APPLIED_APPLICATION_STATUSES = frozenset(
    {
        ApplicationStatus.APPLIED.value,
        ApplicationStatus.INTERVIEW_SCHEDULED.value,
        ApplicationStatus.INTERVIEWED.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.HIRED.value,
    }
)


class JobListingBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    location: Optional[str] = Field(default=None, max_length=255)
    job_type: Optional[str] = Field(default=None, max_length=50)
    experience_level: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_range: Optional[str] = Field(default=None, max_length=100)
    application_url: Optional[str] = None
    source_url: Optional[str] = None
    source: Optional[str] = Field(default="linkedin", max_length=50)
    is_active: bool = True
    applied: bool = False
    skills: Optional[List[str]] = None

class JobListingCreate(JobListingBase):
    pass

class JobListingUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    company: Optional[str] = Field(default=None, min_length=1, max_length=255)
    location: Optional[str] = Field(default=None, max_length=255)
    job_type: Optional[str] = Field(default=None, max_length=50)
    experience_level: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_range: Optional[str] = Field(default=None, max_length=100)
    application_url: Optional[str] = None
    source_url: Optional[str] = None
    source: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None
    applied: Optional[bool] = None

class JobListingResponse(JobListingBase):
    id: int
    posted_date: Optional[datetime] = None
    extracted_date: Optional[datetime] = None
    applied_date: Optional[datetime] = None
    application_status: Optional[str] = None
    application_notes: Optional[str] = None
    application_context: Optional[str] = None
    compatibility_score: Optional[float] = None
    ai_insights: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobAppliedUpdate(BaseModel):
    applied: bool


class JobApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus = ApplicationStatus.PENDING
    notes: Optional[str] = Field(default=None, max_length=5000)
    context: Optional[str] = Field(default=None, max_length=2000)
    date: Optional[datetime] = None


class JobApplicationListItem(BaseModel):
    id: int
    user_id: str
    job_id: int
    application_status: str
    application_source: Optional[str] = None
    application_date: datetime
    source_url: Optional[str] = None
    user_notes: Optional[str] = None
    extraction_metadata: dict[str, Any]
    follow_up_date: Optional[date] = None
    company_response: bool
    response_date: Optional[datetime] = None
    job_listing: JobListingResponse


class PaginatedJobApplications(BaseModel):
    applications: list[JobApplicationListItem]
    total: int
    page: int
    limit: int
    total_pages: int

class DailyJobStats(BaseModel):
    date: str
    jobs_extracted: int
    jobs_applied: int

class JobStats(BaseModel):
    # Overall statistics (all time)
    total_jobs: int
    total_applied: int
    success_rate: float
    
    # Period statistics (for selected time range)
    period_jobs: int
    period_applied: int
    
    # Graph data
    time_range: str
    daily_stats: List[DailyJobStats]

class RecentApplication(BaseModel):
    id: int
    title: str
    company: str
    location: str
    extracted_date: datetime
    source_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
