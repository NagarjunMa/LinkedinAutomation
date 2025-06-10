from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.job import JobListing
from app.schemas.job import JobListingCreate, JobListingResponse, JobListingUpdate
from app.services.linkedin_scraper import LinkedInScraper

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