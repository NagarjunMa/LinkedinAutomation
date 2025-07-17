from typing import Optional, List, Dict
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class TimeRange(str, Enum):
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_3_MONTHS = "last_3_months"

class JobListingBase(BaseModel):
    title: str
    company: str
    location: str
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_range: Optional[str] = None
    application_url: Optional[str] = None
    source_url: Optional[str] = None
    source: str = "linkedin"
    is_active: bool = True
    applied: bool = False

class JobListingCreate(JobListingBase):
    pass

class JobListingUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_range: Optional[str] = None
    application_url: Optional[str] = None
    source_url: Optional[str] = None
    source: Optional[str] = None
    is_active: Optional[bool] = None
    applied: Optional[bool] = None

class JobListingResponse(JobListingBase):
    id: int
    posted_date: Optional[datetime] = None
    extracted_date: datetime
    
    class Config:
        from_attributes = True

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
    
    class Config:
        from_attributes = True