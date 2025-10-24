from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import List, Optional

from app.db.session import get_db
from app.models.activity import ActivityRecord
from app.schemas.activity import (
    ActivityRecordCreate, 
    ActivityRecordResponse, 
    ActivityStatsResponse,
    DailyActivityResponse
)

router = APIRouter()

@router.post("/track", response_model=ActivityRecordResponse)
async def track_activity(
    activity_data: ActivityRecordCreate,
    db: Session = Depends(get_db)
):
    """Track a new activity (job extraction or referral email)"""
    try:
        # Create new activity record
        activity = ActivityRecord(
            user_id=activity_data.user_id,
            activity_type=activity_data.activity_type,
            activity_metadata=activity_data.metadata
        )
        
        db.add(activity)
        db.commit()
        db.refresh(activity)
        
        return activity.to_dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to track activity: {str(e)}")

@router.get("/stats/{user_id}", response_model=ActivityStatsResponse)
async def get_activity_stats(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get activity statistics for a user"""
    try:
        # Get total tasks
        total_tasks = db.query(ActivityRecord).filter(
            ActivityRecord.user_id == user_id
        ).count()
        
        # Get active days (days with at least one activity)
        active_days = db.query(
            func.date(ActivityRecord.created_at).label('date')
        ).filter(
            ActivityRecord.user_id == user_id
        ).group_by(
            func.date(ActivityRecord.created_at)
        ).count()
        
        # Get daily activity for streak calculation
        daily_activities = db.query(
            func.date(ActivityRecord.created_at).label('date')
        ).filter(
            ActivityRecord.user_id == user_id
        ).group_by(
            func.date(ActivityRecord.created_at)
        ).order_by(
            func.date(ActivityRecord.created_at)
        ).all()
        
        # Calculate streaks
        max_streak = 0
        current_streak = 0
        temp_streak = 0
        
        # Convert to list of dates
        activity_dates = [activity.date for activity in daily_activities]
        
        # Calculate streaks
        if activity_dates:
            current_date = activity_dates[0]
            for activity_date in activity_dates:
                if activity_date == current_date:
                    temp_streak += 1
                    current_streak = temp_streak
                    max_streak = max(max_streak, temp_streak)
                else:
                    # Check if dates are consecutive
                    if (activity_date - current_date).days == 1:
                        temp_streak += 1
                        current_streak = temp_streak
                        max_streak = max(max_streak, temp_streak)
                    else:
                        temp_streak = 1
                        current_streak = 1
                    current_date = activity_date
        else:
            current_streak = 0
        
        return ActivityStatsResponse(
            total_tasks=total_tasks,
            active_days=active_days,
            max_streak=max_streak,
            current_streak=current_streak
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity stats: {str(e)}")

@router.get("/daily/{user_id}", response_model=List[DailyActivityResponse])
async def get_daily_activity(
    user_id: str,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """Get daily activity data for calendar display"""
    try:
        # Set default date range (past year if not specified)
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Query daily activity
        daily_activity = db.query(
            func.date(ActivityRecord.created_at).label('date'),
            func.sum(
                func.case(
                    (ActivityRecord.activity_type == 'job_extraction', 1),
                    else_=0
                )
            ).label('job_extractions'),
            func.sum(
                func.case(
                    (ActivityRecord.activity_type == 'referral_email', 1),
                    else_=0
                )
            ).label('referral_emails')
        ).filter(
            and_(
                ActivityRecord.user_id == user_id,
                func.date(ActivityRecord.created_at) >= start_dt.date(),
                func.date(ActivityRecord.created_at) <= end_dt.date()
            )
        ).group_by(
            func.date(ActivityRecord.created_at)
        ).order_by(
            func.date(ActivityRecord.created_at)
        ).all()
        
        # Convert to response format
        result = []
        for activity in daily_activity:
            result.append(DailyActivityResponse(
                date=activity.date.strftime("%Y-%m-%d"),
                job_extractions=int(activity.job_extractions or 0),
                referral_emails=int(activity.referral_emails or 0),
                total_tasks=int(activity.job_extractions or 0) + int(activity.referral_emails or 0)
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily activity: {str(e)}")
