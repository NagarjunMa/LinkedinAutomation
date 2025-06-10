from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.job import SearchQuery, SearchResult
from app.schemas.search import SearchQueryCreate, SearchQueryResponse, SearchResultResponse
from app.services.linkedin_scraper import LinkedInScraper
from app.core.celery_app import celery_app
from app.utils.logger import logger

router = APIRouter()

@router.post("/", response_model=SearchQueryResponse)
async def create_search_query(
    query: SearchQueryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new search query
    """
    db_query = SearchQuery(**query.dict())
    db.add(db_query)
    db.commit()
    db.refresh(db_query)
    return db_query

@router.get("/", response_model=List[SearchQueryResponse])
async def get_search_queries(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all search queries
    """
    queries = db.query(SearchQuery).offset(skip).limit(limit).all()
    return queries

@router.get("/{query_id}", response_model=SearchQueryResponse)
async def get_search_query(
    query_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific search query
    """
    query = db.query(SearchQuery).filter(SearchQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Search query not found")
    return query

@router.post("/{query_id}/execute", response_model=List[SearchResultResponse])
async def execute_search(
    query_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute a search query and return results
    """
    query = db.query(SearchQuery).filter(SearchQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Search query not found")
        
    # Execute search in background
    background_tasks.add_task(execute_search_task, query_id)
    
    # Return existing results
    results = db.query(SearchResult).filter(SearchResult.search_query_id == query_id).all()
    return results

@router.get("/{query_id}/results", response_model=List[SearchResultResponse])
async def get_search_results(
    query_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve results for a specific search query
    """
    results = db.query(SearchResult)\
        .filter(SearchResult.search_query_id == query_id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return results

@router.post("/{query_id}/schedule")
async def schedule_search(
    query_id: int,
    schedule: str,
    db: Session = Depends(get_db)
):
    """
    Schedule a search query to run periodically
    """
    query = db.query(SearchQuery).filter(SearchQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Search query not found")
        
    # Update schedule
    query.schedule = schedule
    db.commit()
    
    # Schedule Celery task
    celery_app.add_periodic_task(
        schedule,
        execute_search_task.s(query_id),
        name=f"search_{query_id}"
    )
    
    return {"message": f"Search scheduled to run {schedule}"}

async def execute_search_task(query_id: int):
    """
    Background task to execute a search query
    """
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        query = db.query(SearchQuery).filter(SearchQuery.id == query_id).first()
        if not query:
            return
            
        # Create scraper instance
        scraper = LinkedInScraper()
        await scraper.initialize()
        
        try:
            # Execute search
            jobs = await scraper.search_jobs(query.__dict__)
            
            # Save results
            for job in jobs:
                result = SearchResult(
                    search_query_id=query_id,
                    job_listing=job,
                    match_score=100  # TODO: Implement proper matching
                )
                db.add(result)
                
            db.commit()
            
        finally:
            # Don't close the browser here, let it persist
            pass
            
    except Exception as e:
        logger.error(f"Error executing search query {query_id}: {str(e)}")
        db.rollback()
        
    finally:
        db.close() 