from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.job import SearchQuery, SearchResult
from app.schemas.search import SearchQueryCreate, SearchQueryUpdate, SearchQueryResponse, SearchResultResponse
# LinkedIn scraper removed - using job aggregator in tasks instead
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

@router.put("/{query_id}", response_model=SearchQueryResponse)
async def update_search_query(
    query_id: int,
    query_update: SearchQueryUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a search query
    """
    query = db.query(SearchQuery).filter(SearchQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Search query not found")
    
    # Update fields that were provided
    update_data = query_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(query, field, value)
    
    db.commit()
    db.refresh(query)
    return query

@router.delete("/{query_id}")
async def delete_search_query(
    query_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a search query
    """
    query = db.query(SearchQuery).filter(SearchQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Search query not found")
    
    # Delete associated results first
    db.query(SearchResult).filter(SearchResult.search_query_id == query_id).delete()
    
    # Delete the query
    db.delete(query)
    db.commit()
    
    return {"message": "Search query deleted successfully"}

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
    Background task to execute a search query using job aggregator
    Note: This function is deprecated - use app.tasks.search_tasks.execute_search_task instead
    """
    # This function is now handled by the celery task in app.tasks.search_tasks
    # Redirect to the proper task
    from app.tasks.search_tasks import execute_search_task as celery_execute_search_task
    celery_execute_search_task(query_id) 