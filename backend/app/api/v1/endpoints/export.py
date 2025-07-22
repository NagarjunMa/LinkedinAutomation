from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
# import pandas as pd  # Temporarily disabled due to numpy compatibility issue
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
    # Temporarily disabled due to numpy/pandas compatibility issue
    raise HTTPException(
        status_code=501, 
        detail="Export functionality temporarily disabled due to dependency issues. Will be restored soon."
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
    # Temporarily disabled due to numpy/pandas compatibility issue
    raise HTTPException(
        status_code=501, 
        detail="Export functionality temporarily disabled due to dependency issues. Will be restored soon."
    ) 