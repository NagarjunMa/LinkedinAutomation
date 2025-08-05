from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
# SearchQuery and SearchResult models have been removed - functionality replaced by RSS feeds
from app.utils.logger import logger

router = APIRouter()

@router.get("/")
async def search_endpoint_deprecated():
    """
    Search endpoint has been deprecated.
    SearchQuery and SearchResult models have been removed.
    Use RSS feeds instead for job aggregation.
    """
    raise HTTPException(
        status_code=410,  # Gone
        detail="Search endpoint deprecated. SearchQuery and SearchResult models have been removed. Use RSS feeds instead."
    ) 