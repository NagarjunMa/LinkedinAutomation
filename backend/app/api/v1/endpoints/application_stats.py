from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import random

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