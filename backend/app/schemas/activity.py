from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ActivityRecordCreate(BaseModel):
    user_id: str
    activity_type: str  # 'job_extraction' or 'referral_email'
    metadata: Optional[Dict[str, Any]] = None

class ActivityRecordResponse(BaseModel):
    id: int
    user_id: str
    activity_type: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class ActivityStatsResponse(BaseModel):
    total_tasks: int
    active_days: int
    max_streak: int
    current_streak: int

class DailyActivityResponse(BaseModel):
    date: str
    job_extractions: int
    referral_emails: int
    total_tasks: int
