from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO
from app.db.session import get_db
from app.models.job import JobListing, SearchResult
from app.schemas.export import ExportFormat

router = APIRouter()

@router.post("/jobs")
async def export_jobs(
    job_ids: List[int],
    format: ExportFormat,
    db: Session = Depends(get_db)
):
    """
    Export selected jobs to CSV or Excel
    """
    jobs = db.query(JobListing).filter(JobListing.id.in_(job_ids)).all()
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found")
        
    # Convert to DataFrame
    df = pd.DataFrame([{
        "Title": job.title,
        "Company": job.company,
        "Location": job.location,
        "Job Type": job.job_type,
        "Experience Level": job.experience_level,
        "Description": job.description,
        "Requirements": job.requirements,
        "Salary Range": job.salary_range,
        "Posted Date": job.posted_date,
        "Application URL": job.application_url,
        "Source URL": job.source_url
    } for job in jobs])
    
    # Create file in memory
    output = BytesIO()
    
    if format == ExportFormat.CSV:
        df.to_csv(output, index=False)
        media_type = "text/csv"
        filename = "jobs.csv"
    else:  # Excel
        df.to_excel(output, index=False)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "jobs.xlsx"
        
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/search-results/{query_id}")
async def export_search_results(
    query_id: int,
    format: ExportFormat,
    db: Session = Depends(get_db)
):
    """
    Export search results to CSV or Excel
    """
    results = db.query(SearchResult)\
        .filter(SearchResult.search_query_id == query_id)\
        .all()
        
    if not results:
        raise HTTPException(status_code=404, detail="No search results found")
        
    # Convert to DataFrame
    df = pd.DataFrame([{
        "Title": result.job_listing.title,
        "Company": result.job_listing.company,
        "Location": result.job_listing.location,
        "Job Type": result.job_listing.job_type,
        "Experience Level": result.job_listing.experience_level,
        "Description": result.job_listing.description,
        "Requirements": result.job_listing.requirements,
        "Salary Range": result.job_listing.salary_range,
        "Posted Date": result.job_listing.posted_date,
        "Application URL": result.job_listing.application_url,
        "Source URL": result.job_listing.source_url,
        "Match Score": result.match_score
    } for result in results])
    
    # Create file in memory
    output = BytesIO()
    
    if format == ExportFormat.CSV:
        df.to_csv(output, index=False)
        media_type = "text/csv"
        filename = f"search_results_{query_id}.csv"
    else:  # Excel
        df.to_excel(output, index=False)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"search_results_{query_id}.xlsx"
        
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    ) 