from pydantic import BaseModel
from typing import Optional

class JobListingBase(BaseModel):
    title: str
    company: str
    location: str
    description: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    application_url: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    is_active: Optional[bool] = True

class JobListingCreate(JobListingBase):
    pass

class JobListingUpdate(JobListingBase):
    pass

class JobListingResponse(JobListingBase):
    id: int

    class Config:
        orm_mode = True