from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.models.job import RSSFeedConfiguration, UserJobPreferences
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Pydantic models for RSS Feed Configuration
class RSSFeedBase(BaseModel):
    name: str
    feed_url: str
    source_type: str = "rss_app"
    location_filter: Optional[str] = None
    keyword_filter: Optional[str] = None
    job_type_filter: Optional[str] = None
    experience_filter: Optional[str] = None
    is_active: bool = True
    refresh_interval: int = 3600
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class RSSFeedCreate(RSSFeedBase):
    pass

class RSSFeedUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    location_filter: Optional[str] = None
    keyword_filter: Optional[str] = None
    job_type_filter: Optional[str] = None
    experience_filter: Optional[str] = None
    refresh_interval: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class RSSFeedResponse(RSSFeedBase):
    id: int
    created_at: datetime
    last_refresh: Optional[datetime] = None
    last_job_count: int = 0
    
    class Config:
        from_attributes = True

class FeedHealthResponse(BaseModel):
    total_feeds: int
    active_feeds: int
    inactive_feeds: int
    total_jobs_last_refresh: int
    feeds_with_issues: int
    last_refresh_time: Optional[datetime] = None

@router.get("/", response_model=List[RSSFeedResponse])
async def get_rss_feeds(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False
):
    """
    Get all RSS feed configurations
    """
    query = db.query(RSSFeedConfiguration)
    
    if active_only:
        query = query.filter(RSSFeedConfiguration.is_active == True)
    
    feeds = query.order_by(desc(RSSFeedConfiguration.created_at)).offset(skip).limit(limit).all()
    return feeds

@router.post("/", response_model=RSSFeedResponse)
async def create_rss_feed(
    feed: RSSFeedCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new RSS feed configuration
    """
    # Check if feed URL already exists
    existing = db.query(RSSFeedConfiguration).filter(
        RSSFeedConfiguration.feed_url == feed.feed_url
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Feed URL already exists")
    
    db_feed = RSSFeedConfiguration(**feed.dict())
    db.add(db_feed)
    db.commit()
    db.refresh(db_feed)
    return db_feed

@router.get("/{feed_id}", response_model=RSSFeedResponse)
async def get_rss_feed(
    feed_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific RSS feed configuration
    """
    feed = db.query(RSSFeedConfiguration).filter(RSSFeedConfiguration.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return feed

@router.put("/{feed_id}", response_model=RSSFeedResponse)
async def update_rss_feed(
    feed_id: int,
    feed_update: RSSFeedUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an RSS feed configuration
    """
    feed = db.query(RSSFeedConfiguration).filter(RSSFeedConfiguration.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    # Update only provided fields
    for field, value in feed_update.dict(exclude_unset=True).items():
        setattr(feed, field, value)
    
    db.commit()
    db.refresh(feed)
    return feed

@router.delete("/{feed_id}")
async def delete_rss_feed(
    feed_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an RSS feed configuration
    """
    feed = db.query(RSSFeedConfiguration).filter(RSSFeedConfiguration.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    db.delete(feed)
    db.commit()
    return {"message": "Feed deleted successfully"}

@router.post("/{feed_id}/toggle", response_model=RSSFeedResponse)
async def toggle_rss_feed(
    feed_id: int,
    db: Session = Depends(get_db)
):
    """
    Toggle RSS feed active status
    """
    feed = db.query(RSSFeedConfiguration).filter(RSSFeedConfiguration.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    feed.is_active = not feed.is_active
    db.commit()
    db.refresh(feed)
    return feed

@router.get("/health/summary", response_model=FeedHealthResponse)
async def get_feed_health(
    db: Session = Depends(get_db)
):
    """
    Get RSS feed health summary
    """
    from sqlalchemy import func
    
    # Get feed statistics
    total_feeds = db.query(func.count(RSSFeedConfiguration.id)).scalar()
    active_feeds = db.query(func.count(RSSFeedConfiguration.id)).filter(
        RSSFeedConfiguration.is_active == True
    ).scalar()
    
    # Get feeds with recent refresh data
    feeds_with_data = db.query(RSSFeedConfiguration).filter(
        RSSFeedConfiguration.last_refresh.isnot(None)
    ).all()
    
    total_jobs_last_refresh = sum(feed.last_job_count for feed in feeds_with_data)
    feeds_with_issues = len([feed for feed in feeds_with_data if feed.last_job_count == 0])
    
    # Get most recent refresh time
    last_refresh_time = db.query(func.max(RSSFeedConfiguration.last_refresh)).scalar()
    
    return FeedHealthResponse(
        total_feeds=total_feeds,
        active_feeds=active_feeds,
        inactive_feeds=total_feeds - active_feeds,
        total_jobs_last_refresh=total_jobs_last_refresh,
        feeds_with_issues=feeds_with_issues,
        last_refresh_time=last_refresh_time
    ) 