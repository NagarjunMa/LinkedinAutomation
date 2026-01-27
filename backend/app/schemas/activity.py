from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class ActivityRecordBase(BaseModel):
    activity_type: str
    activity_subtype: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    activity_metadata: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[int] = None
    is_automated: Optional[bool] = False
    source: Optional[str] = None


class ActivityRecordCreate(ActivityRecordBase):
    pass


class ActivityRecordUpdate(ActivityRecordBase):
    activity_type: Optional[str] = None


class ActivityRecord(ActivityRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    timestamp: datetime
    created_at: datetime


class ActivitySummary(BaseModel):
    total_activities: int
    activities_today: int
    activities_this_week: int
    activities_this_month: int
    activity_types: Dict[str, int]


class ActivityCalendarResponse(BaseModel):
    activities: List[ActivityRecord]
    summary: ActivitySummary