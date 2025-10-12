from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random
import calendar

from app.db.session import get_db
from app.models.user import User

router = APIRouter()

@router.get("/application-extraction-stats")
async def get_application_extraction_stats(
    days: int = 7,
    user_id: str = Query(default="demo_user", description="User ID for context"),
    db: Session = Depends(get_db)
):
    """
    Get application extraction statistics for the last N days.
    For now, returns random data for demonstration.
    """
    try:
        # Generate data for the last N days
        stats = []
        base_date = datetime.now().date()

        for i in range(days):
            date = base_date - timedelta(days=days - 1 - i)
            # For now, generate random values between 5-20 applications per day
            applications_extracted = random.randint(5, 20)

            stats.append({
                "date": date.isoformat(),
                "jobs": applications_extracted
            })

        return {
            "status": "success",
            "data": stats,
            "total_applications": sum(stat["jobs"] for stat in stats),
            "average_per_day": round(sum(stat["jobs"] for stat in stats) / len(stats), 1)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching application stats: {str(e)}")

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    user_id: str = Query(default="demo_user", description="User ID for context"),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for the dashboard.
    For now, returns mock data for demonstration.
    """
    try:
        # Mock data for demonstration
        return {
            "status": "success",
            "data": {
                "overview": {
                    "total": random.randint(35, 50),
                    "applied": random.randint(20, 30),
                    "interviews": random.randint(10, 20)
                },
                "email_processing": {
                    "emails_sent": random.randint(20, 30),
                    "emails_processed": random.randint(15, 25),
                    "change": f"+{random.randint(10, 20)}%",
                    "change_type": "increase"
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard summary: {str(e)}")

@router.get("/job-extraction-calendar")
async def get_job_extraction_calendar(
    year: int = Query(default=None, description="Year (default: current year)"),
    month: int = Query(default=None, description="Month (1-12, default: current month)"),
    user_id: str = Query(default="demo_user", description="User ID for context"),
    db: Session = Depends(get_db)
):
    """
    Get job extraction calendar data for a specific month.
    Returns extraction activity for each day of the month.
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

        # Generate mock data for demonstration
        # In a real implementation, this would query your job extraction database
        extraction_days = []
        total_extractions = 0
        total_applications = 0
        active_days = 0

        # Simulate some extraction activity (about 7-10 active days per month)
        active_day_count = random.randint(7, 10)
        active_days_set = set(random.sample(range(1, days_in_month + 1), active_day_count))

        for day in active_days_set:
            jobs_extracted = random.randint(15, 30)
            applications_added = random.randint(8, 18)

            extraction_days.append({
                "date": day,
                "jobs_extracted": jobs_extracted,
                "applications_added": applications_added
            })

            total_extractions += jobs_extracted
            total_applications += applications_added
            active_days += 1

        # Sort by date
        extraction_days.sort(key=lambda x: x["date"])

        return {
            "status": "success",
            "data": {
                "year": target_year,
                "month": target_month,
                "month_name": calendar.month_name[target_month],
                "extraction_days": extraction_days,
                "summary": {
                    "total_extractions": total_extractions,
                    "total_applications": total_applications,
                    "active_days": active_days,
                    "days_in_month": days_in_month
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching calendar data: {str(e)}")