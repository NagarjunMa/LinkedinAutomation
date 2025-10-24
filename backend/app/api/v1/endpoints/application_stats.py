from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import calendar

from app.db.session import get_db
from app.models.user import User
from app.models.job import JobListing, JobApplication
from app.core.auth import get_authenticated_user_id

router = APIRouter()

@router.get("/application-extraction-stats")
async def get_application_extraction_stats(
    days: int = 7,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """
    Get application extraction statistics for the last N days.
    Returns actual user data from job applications.
    """
    try:
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)

        # Query actual job application data grouped by date
        stats_query = db.query(
            func.date(JobApplication.application_date).label('date'),
            func.count(JobApplication.id).label('jobs')
        ).filter(
            and_(
                JobApplication.user_id == user_id,
                func.date(JobApplication.application_date) >= start_date,
                func.date(JobApplication.application_date) <= end_date
            )
        ).group_by(
            func.date(JobApplication.application_date)
        ).order_by('date').all()

        # Create a dictionary for quick lookup
        stats_dict = {stat.date: stat.jobs for stat in stats_query}

        # Generate data for all days in the range, filling in zeros for days with no applications
        stats = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            jobs_count = stats_dict.get(current_date, 0)

            stats.append({
                "date": current_date.isoformat(),
                "jobs": jobs_count
            })

        total_applications = sum(stat["jobs"] for stat in stats)
        average_per_day = round(total_applications / days, 1) if days > 0 else 0

        return {
            "status": "success",
            "data": stats,
            "total_applications": total_applications,
            "average_per_day": average_per_day
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching application stats: {str(e)}")

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for the dashboard.
    Returns actual user application data.
    """
    try:
        # Get total applications count
        total_applications = db.query(func.count(JobApplication.id)).filter(
            JobApplication.user_id == user_id
        ).scalar() or 0

        # Get applied applications count (status = 'applied')
        applied_count = db.query(func.count(JobApplication.id)).filter(
            and_(
                JobApplication.user_id == user_id,
                JobApplication.application_status == 'applied'
            )
        ).scalar() or 0

        # Get interview count (applications with interview_date set)
        interview_count = db.query(func.count(JobApplication.id)).filter(
            and_(
                JobApplication.user_id == user_id,
                JobApplication.interview_date.is_not(None)
            )
        ).scalar() or 0

        # Calculate weekly change for applied applications
        one_week_ago = datetime.now() - timedelta(days=7)
        current_week_applied = db.query(func.count(JobApplication.id)).filter(
            and_(
                JobApplication.user_id == user_id,
                JobApplication.application_status == 'applied',
                JobApplication.application_date >= one_week_ago
            )
        ).scalar() or 0

        previous_week_applied = db.query(func.count(JobApplication.id)).filter(
            and_(
                JobApplication.user_id == user_id,
                JobApplication.application_status == 'applied',
                JobApplication.application_date >= datetime.now() - timedelta(days=14),
                JobApplication.application_date < one_week_ago
            )
        ).scalar() or 0

        # Calculate percentage change
        if previous_week_applied > 0:
            change_percent = round(((current_week_applied - previous_week_applied) / previous_week_applied) * 100, 1)
            change_type = "increase" if change_percent > 0 else "decrease" if change_percent < 0 else "neutral"
            change_text = f"{'+' if change_percent > 0 else ''}{change_percent}%"
        else:
            change_text = "+100%" if current_week_applied > 0 else "0%"
            change_type = "increase" if current_week_applied > 0 else "neutral"

        return {
            "status": "success",
            "data": {
                "overview": {
                    "total": total_applications,
                    "applied": applied_count,
                    "interviews": interview_count
                },
                "email_processing": {
                    "emails_sent": 0,  # This would need email service integration
                    "emails_processed": 0,  # This would need email service integration
                    "change": change_text,
                    "change_type": change_type
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard summary: {str(e)}")

@router.get("/job-extraction-calendar")
async def get_job_extraction_calendar(
    year: int = Query(default=None, description="Year (default: current year)"),
    month: int = Query(default=None, description="Month (1-12, default: current month)"),
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """
    Get job extraction calendar data for a specific month.
    Returns actual user application activity for each day of the month.
    """
    try:
        # Use current date if not specified
        now = datetime.now()
        target_year = year if year else now.year
        target_month = month if month else now.month

        # Validate month
        if target_month < 1 or target_month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

        # Get number of days in the target month
        days_in_month = calendar.monthrange(target_year, target_month)[1]

        # Define the date range for the target month
        start_date = datetime(target_year, target_month, 1).date()
        if target_month == 12:
            end_date = datetime(target_year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(target_year, target_month + 1, 1).date() - timedelta(days=1)

        # Query actual application data grouped by day
        applications_by_day = db.query(
            extract('day', JobApplication.application_date).label('day'),
            func.count(JobApplication.id).label('applications_added')
        ).filter(
            and_(
                JobApplication.user_id == user_id,
                func.date(JobApplication.application_date) >= start_date,
                func.date(JobApplication.application_date) <= end_date
            )
        ).group_by(
            extract('day', JobApplication.application_date)
        ).all()

        # Create a dictionary for quick lookup
        applications_dict = {int(row.day): row.applications_added for row in applications_by_day}

        # Generate extraction days data
        extraction_days = []
        total_applications = 0
        active_days = 0

        for day in range(1, days_in_month + 1):
            applications_added = applications_dict.get(day, 0)

            if applications_added > 0:
                extraction_days.append({
                    "date": day,
                    "jobs_extracted": applications_added,  # Using applications as extraction metric
                    "applications_added": applications_added
                })
                total_applications += applications_added
                active_days += 1

        # Sort by date (already in order, but just to be safe)
        extraction_days.sort(key=lambda x: x["date"])

        return {
            "status": "success",
            "data": {
                "year": target_year,
                "month": target_month,
                "month_name": calendar.month_name[target_month],
                "extraction_days": extraction_days,
                "summary": {
                    "total_extractions": total_applications,  # Using applications as extractions
                    "total_applications": total_applications,
                    "active_days": active_days,
                    "days_in_month": days_in_month
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching calendar data: {str(e)}")