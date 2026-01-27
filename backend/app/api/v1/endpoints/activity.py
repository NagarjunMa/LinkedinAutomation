from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta, date
from pydantic import BaseModel
from app.models.activity import ActivityRecord
from app.schemas.activity import (
    ActivityRecord as ActivitySchema,
    ActivityRecordCreate,
    ActivityRecordUpdate,
    ActivitySummary,
    ActivityCalendarResponse
)
from app.db.rls_session import get_db, set_current_user
from app.core.auth import get_authenticated_user_id

router = APIRouter()

# Frontend-compatible request models
class ActivityTrackRequest(BaseModel):
    user_id: str
    activity_type: str
    metadata: Optional[Dict[str, Any]] = None

class ActivityStatsResponse(BaseModel):
    totalTasks: int
    activeDays: int
    maxStreak: int
    currentStreak: int
    dailyActivity: List[Dict[str, Any]]

class DailyActivityItem(BaseModel):
    date: str
    jobExtractions: int
    referralEmails: int
    totalTasks: int


# Frontend-compatible endpoints
@router.post("/track")
def track_activity(
    request: ActivityTrackRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Track a new activity (frontend-compatible endpoint)"""
    set_current_user(user_id)

    # Validate user owns this activity
    if request.user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot track activity for other users")

    db_activity = ActivityRecord(
        user_id=user_id,
        activity_type=request.activity_type,
        timestamp=datetime.utcnow(),
        metadata=request.metadata or {}
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)

    return {
        "id": db_activity.id,
        "user_id": db_activity.user_id,
        "activity_type": db_activity.activity_type,
        "created_at": db_activity.timestamp.isoformat(),
        "metadata": db_activity.metadata
    }


@router.get("/stats/{user_id}")
def get_activity_stats(
    user_id_param: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get activity statistics (frontend-compatible endpoint)"""
    set_current_user(user_id)

    # Validate user can only access their own stats
    if user_id_param != user_id:
        raise HTTPException(status_code=403, detail="Cannot access other users' activity stats")

    # Calculate stats for last 90 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)

    # Get all activities in range
    activities = db.query(ActivityRecord).filter(
        and_(
            ActivityRecord.user_id == user_id,
            ActivityRecord.timestamp >= start_date,
            ActivityRecord.timestamp <= end_date
        )
    ).order_by(desc(ActivityRecord.timestamp)).all()

    # Calculate statistics
    total_tasks = len(activities)

    # Group activities by date
    daily_activity_map = {}
    active_days_set = set()

    for activity in activities:
        activity_date = activity.timestamp.date().isoformat()
        active_days_set.add(activity_date)

        if activity_date not in daily_activity_map:
            daily_activity_map[activity_date] = {
                "date": activity_date,
                "jobExtractions": 0,
                "referralEmails": 0,
                "totalTasks": 0
            }

        if activity.activity_type == "job_extraction":
            daily_activity_map[activity_date]["jobExtractions"] += 1
        elif activity.activity_type == "referral_email":
            daily_activity_map[activity_date]["referralEmails"] += 1

        daily_activity_map[activity_date]["totalTasks"] += 1

    # Calculate streaks
    current_streak = 0
    max_streak = 0
    temp_streak = 0

    # Sort dates and check for consecutive days
    today = datetime.utcnow().date()
    for i in range(90):  # Check last 90 days
        check_date = today - timedelta(days=i)
        date_str = check_date.isoformat()

        if date_str in daily_activity_map:
            temp_streak += 1
            if i == 0 or (today - timedelta(days=i-1)).isoformat() in daily_activity_map:
                if i == 0:  # Today or most recent activity
                    current_streak = temp_streak
        else:
            max_streak = max(max_streak, temp_streak)
            if current_streak == 0:
                temp_streak = 0
            else:
                break  # Stop counting current streak

    max_streak = max(max_streak, current_streak)

    # Convert daily activity to list
    daily_activity = list(daily_activity_map.values())
    daily_activity.sort(key=lambda x: x["date"], reverse=True)

    return ActivityStatsResponse(
        totalTasks=total_tasks,
        activeDays=len(active_days_set),
        maxStreak=max_streak,
        currentStreak=current_streak,
        dailyActivity=daily_activity
    )


@router.get("/daily/{user_id}")
def get_daily_activity(
    user_id_param: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get daily activity data (frontend-compatible endpoint)"""
    set_current_user(user_id)

    # Validate user can only access their own data
    if user_id_param != user_id:
        raise HTTPException(status_code=403, detail="Cannot access other users' activity data")

    # Parse dates
    if start_date:
        start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    else:
        start_datetime = datetime.utcnow() - timedelta(days=30)

    if end_date:
        end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    else:
        end_datetime = datetime.utcnow()

    # Get activities
    activities = db.query(ActivityRecord).filter(
        and_(
            ActivityRecord.user_id == user_id,
            ActivityRecord.timestamp >= start_datetime,
            ActivityRecord.timestamp <= end_datetime
        )
    ).order_by(desc(ActivityRecord.timestamp)).all()

    # Group by date
    daily_data = {}
    for activity in activities:
        activity_date = activity.timestamp.date().isoformat()

        if activity_date not in daily_data:
            daily_data[activity_date] = {
                "date": activity_date,
                "jobExtractions": 0,
                "referralEmails": 0,
                "totalTasks": 0,
                "activities": []
            }

        if activity.activity_type == "job_extraction":
            daily_data[activity_date]["jobExtractions"] += 1
        elif activity.activity_type == "referral_email":
            daily_data[activity_date]["referralEmails"] += 1

        daily_data[activity_date]["totalTasks"] += 1
        daily_data[activity_date]["activities"].append({
            "id": activity.id,
            "type": activity.activity_type,
            "timestamp": activity.timestamp.isoformat(),
            "metadata": activity.metadata
        })

    return {"daily_activity": list(daily_data.values())}


@router.post("/", response_model=ActivitySchema)
def create_activity(
    activity: ActivityRecordCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Create a new activity record"""
    set_current_user(user_id)
    db_activity = ActivityRecord(
        user_id=user_id,
        **activity.dict()
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity


@router.get("/", response_model=List[ActivitySchema])
def get_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    activity_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get user's activities with optional filtering"""
    set_current_user(user_id)
    query = db.query(ActivityRecord).filter(ActivityRecord.user_id == user_id)

    if activity_type:
        query = query.filter(ActivityRecord.activity_type == activity_type)

    if start_date:
        query = query.filter(ActivityRecord.timestamp >= start_date)

    if end_date:
        query = query.filter(ActivityRecord.timestamp <= end_date)

    return query.order_by(ActivityRecord.timestamp.desc()).offset(skip).limit(limit).all()


@router.get("/calendar", response_model=ActivityCalendarResponse)
def get_activity_calendar(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get activity calendar data with summary statistics"""
    set_current_user(user_id)
    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    # Get activities
    activities = db.query(ActivityRecord).filter(
        and_(
            ActivityRecord.user_id == user_id,
            ActivityRecord.timestamp >= start_date,
            ActivityRecord.timestamp <= end_date
        )
    ).order_by(ActivityRecord.timestamp.desc()).all()

    # Calculate summary statistics
    now = datetime.utcnow()
    today_start = datetime.combine(now.date(), datetime.min.time())
    week_start = today_start - timedelta(days=now.weekday())
    month_start = datetime.combine(now.date().replace(day=1), datetime.min.time())

    total_activities = len(activities)
    activities_today = len([a for a in activities if a.timestamp >= today_start])
    activities_this_week = len([a for a in activities if a.timestamp >= week_start])
    activities_this_month = len([a for a in activities if a.timestamp >= month_start])

    # Count by activity type
    activity_types = {}
    for activity in activities:
        activity_types[activity.activity_type] = activity_types.get(activity.activity_type, 0) + 1

    summary = ActivitySummary(
        total_activities=total_activities,
        activities_today=activities_today,
        activities_this_week=activities_this_week,
        activities_this_month=activities_this_month,
        activity_types=activity_types
    )

    return ActivityCalendarResponse(activities=activities, summary=summary)


@router.get("/summary", response_model=ActivitySummary)
def get_activity_summary(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get activity summary statistics"""
    set_current_user(user_id)
    now = datetime.utcnow()
    today_start = datetime.combine(now.date(), datetime.min.time())
    week_start = today_start - timedelta(days=now.weekday())
    month_start = datetime.combine(now.date().replace(day=1), datetime.min.time())

    base_query = db.query(ActivityRecord).filter(ActivityRecord.user_id == user_id)

    total_activities = base_query.count()
    activities_today = base_query.filter(ActivityRecord.timestamp >= today_start).count()
    activities_this_week = base_query.filter(ActivityRecord.timestamp >= week_start).count()
    activities_this_month = base_query.filter(ActivityRecord.timestamp >= month_start).count()

    # Get activity type counts
    activity_type_counts = db.query(
        ActivityRecord.activity_type,
        func.count(ActivityRecord.id)
    ).filter(
        ActivityRecord.user_id == user_id
    ).group_by(ActivityRecord.activity_type).all()

    activity_types = {activity_type: count for activity_type, count in activity_type_counts}

    return ActivitySummary(
        total_activities=total_activities,
        activities_today=activities_today,
        activities_this_week=activities_this_week,
        activities_this_month=activities_this_month,
        activity_types=activity_types
    )


@router.get("/{activity_id}", response_model=ActivitySchema)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get a specific activity by ID"""
    set_current_user(user_id)
    activity = db.query(ActivityRecord).filter(
        and_(
            ActivityRecord.id == activity_id,
            ActivityRecord.user_id == user_id
        )
    ).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    return activity


@router.put("/{activity_id}", response_model=ActivitySchema)
def update_activity(
    activity_id: int,
    activity_update: ActivityRecordUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Update an activity record"""
    set_current_user(user_id)
    activity = db.query(ActivityRecord).filter(
        and_(
            ActivityRecord.id == activity_id,
            ActivityRecord.user_id == user_id
        )
    ).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    update_data = activity_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(activity, field, value)

    db.commit()
    db.refresh(activity)
    return activity


@router.delete("/{activity_id}")
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Delete an activity record"""
    set_current_user(user_id)
    activity = db.query(ActivityRecord).filter(
        and_(
            ActivityRecord.id == activity_id,
            ActivityRecord.user_id == user_id
        )
    ).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    db.delete(activity)
    db.commit()
    return {"message": "Activity deleted successfully"}