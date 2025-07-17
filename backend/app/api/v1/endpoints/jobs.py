from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, Integer, extract, desc
from app.db.session import get_db
from app.models.job import JobListing
from app.schemas.job import (
    JobListingCreate, 
    JobListingResponse, 
    JobListingUpdate, 
    JobStats, 
    TimeRange,
    RecentApplication
)
from app.services.linkedin_scraper import LinkedInScraper
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/", response_model=List[JobListingResponse])
async def get_jobs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    title: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    experience_level: Optional[str] = None,
):
    """
    Retrieve job listings with optional filtering
    """
    query = db.query(JobListing)
    
    if title:
        query = query.filter(JobListing.title.ilike(f"%{title}%"))
    if company:
        query = query.filter(JobListing.company.ilike(f"%{company}%"))
    if location:
        query = query.filter(JobListing.location.ilike(f"%{location}%"))
    if job_type:
        query = query.filter(JobListing.job_type == job_type)
    if experience_level:
        query = query.filter(JobListing.experience_level == experience_level)
        
    jobs = query.offset(skip).limit(limit).all()
    return jobs

@router.get("/stats", response_model=JobStats)
async def get_job_stats(
    db: Session = Depends(get_db),
    time_range: TimeRange = Query(default=TimeRange.LAST_30_DAYS, description="Time range for stats"),
    custom_days: Optional[int] = Query(default=None, description="Custom number of days for stats")
):
    """
    Get job statistics including:
    - Overall total jobs and applications (all time)
    - Time-range specific graph data
    """
    # Get overall totals (regardless of time range)
    overall_stats = db.query(
        func.count(JobListing.id).label('total_jobs'),
        func.sum(cast(JobListing.applied, Integer)).label('total_applied')
    ).first()

    total_jobs = overall_stats.total_jobs or 0
    total_applied = overall_stats.total_applied or 0
    
    # Calculate success rate from overall totals
    success_rate = (total_applied / total_jobs * 100) if total_jobs > 0 else 0

    # Calculate date range for graph data
    end_date = datetime.utcnow()
    if custom_days is not None:
        days = custom_days
    else:
        days = {
            TimeRange.LAST_7_DAYS: 7,
            TimeRange.LAST_30_DAYS: 30,
            TimeRange.LAST_3_MONTHS: 90
        }[time_range]
    
    start_date = end_date - timedelta(days=days)
    
    # Get time-range specific data for the graph
    daily_stats = db.query(
        cast(JobListing.extracted_date, Date).label('date'),
        func.count(JobListing.id).label('jobs_extracted'),
        func.sum(cast(JobListing.applied, Integer)).label('jobs_applied'),
        extract('hour', JobListing.extracted_date).label('hour')
    ).filter(
        JobListing.extracted_date >= start_date,
        JobListing.extracted_date <= end_date
    ).group_by(
        cast(JobListing.extracted_date, Date),
        extract('hour', JobListing.extracted_date)
    ).order_by(
        cast(JobListing.extracted_date, Date),
        extract('hour', JobListing.extracted_date)
    ).all()
    
    # Calculate daily aggregates for the graph
    daily_data = []
    current_date = None
    daily_extracted = 0
    daily_applied = 0
    
    for stat in daily_stats:
        stat_date = stat.date
        
        if current_date is None:
            current_date = stat_date
        
        if current_date != stat_date:
            # Add the previous day's data
            daily_data.append({
                "date": str(current_date),
                "jobs_extracted": daily_extracted,
                "jobs_applied": daily_applied or 0,
            })
            # Reset counters for new day
            current_date = stat_date
            daily_extracted = stat.jobs_extracted
            daily_applied = stat.jobs_applied or 0
        else:
            # Accumulate current day's data
            daily_extracted += stat.jobs_extracted
            daily_applied += stat.jobs_applied or 0
    
    # Add the last day's data
    if current_date is not None:
        daily_data.append({
            "date": str(current_date),
            "jobs_extracted": daily_extracted,
            "jobs_applied": daily_applied or 0,
        })

    # Get period totals (just for the selected time range)
    period_stats = db.query(
        func.count(JobListing.id).label('period_jobs'),
        func.sum(cast(JobListing.applied, Integer)).label('period_applied')
    ).filter(
        JobListing.extracted_date >= start_date,
        JobListing.extracted_date <= end_date
    ).first()
    
    return {
        # Overall statistics (all time)
        "total_jobs": total_jobs,
        "total_applied": total_applied,
        "success_rate": round(success_rate, 2),
        
        # Period statistics (for selected time range)
        "period_jobs": period_stats.period_jobs or 0,
        "period_applied": period_stats.period_applied or 0,
        
        # Graph data
        "daily_stats": daily_data,
        "time_range": time_range.value if not custom_days else f"last_{custom_days}_days"
    } 

@router.get("/recent-applications", response_model=List[RecentApplication])
async def get_recent_applications(
    limit: int = Query(default=5, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get recent job applications, ordered by application date
    """
    recent_apps = db.query(JobListing).filter(
        JobListing.applied == True
    ).order_by(
        desc(JobListing.extracted_date)
    ).limit(limit).all()
    
    return recent_apps

@router.post("/", response_model=JobListingResponse)
async def create_job(
    job: JobListingCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new job listing
    """
    db_job = JobListing(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.get("/{job_id}", response_model=JobListingResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific job listing by ID
    """
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=JobListingResponse)
async def update_job(
    job_id: int,
    job_update: JobListingUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a job listing
    """
    db_job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    for field, value in job_update.dict(exclude_unset=True).items():
        setattr(db_job, field, value)
        
    db.commit()
    db.refresh(db_job)
    return db_job

@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a job listing
    """
    db_job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    db.delete(db_job)
    db.commit()
    return {"message": "Job deleted successfully"}

@router.post("/scrape", response_model=List[JobListingResponse])
async def scrape_jobs(
    query: dict,
    db: Session = Depends(get_db)
):
    """
    Scrape jobs from LinkedIn based on search parameters
    """
    async with LinkedInScraper() as scraper:
        jobs = await scraper.search_jobs(query)
        
        # Save jobs to database
        for job in jobs:
            db.add(job)
        db.commit()
        
        return jobs 

@router.put("/{job_id}/status", response_model=JobListingResponse)
async def update_job_status(
    job_id: int,
    status_update: dict,
    db: Session = Depends(get_db)
):
    """
    Update job application status
    """
    db_job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if "applied" in status_update:
        db_job.applied = status_update["applied"]
        
    db.commit()
    db.refresh(db_job)
    return db_job 