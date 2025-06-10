from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from .job import JobListingResponse

class SearchQueryBase(BaseModel):
    title: str
    location: Optional[str] = None
    keywords: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    date_posted: Optional[str] = None 
    salary_range: Optional[str] = None
    schedule: Optional[str] = None
    job_metadata: Optional[Dict[str, Any]] = None

class SearchQueryCreate(SearchQueryBase):
    pass

class SearchQueryUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    keywords: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    date_posted: Optional[str] = None 
    salary_range: Optional[str] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None
    job_metadata: Optional[Dict[str, Any]] = None

class SearchQueryResponse(SearchQueryBase):
    id: int
    created_at: datetime
    is_active: bool
    last_run: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SearchResultBase(BaseModel):
    search_query_id: int
    job_listing_id: int
    match_score: int

class SearchResultCreate(SearchResultBase):
    pass

class SearchResultResponse(SearchResultBase):
    id: int
    created_at: datetime
    job_listing: JobListingResponse
    
    class Config:
        from_attributes = True 