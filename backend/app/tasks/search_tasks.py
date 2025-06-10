from celery import shared_task
from app.core.celery_app import celery_app
from app.services.linkedin_scraper import LinkedInScraper
from app.db.session import SessionLocal
from app.models.job import SearchQuery, SearchResult
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@shared_task
def execute_search_task(query_id: int):
    """
    Celery task to execute a search query
    """
    db = SessionLocal()
    try:
        query = db.query(SearchQuery).filter(SearchQuery.id == query_id).first()
        if not query:
            logger.error(f"Search query {query_id} not found")
            return
            
        # Execute search
        scraper = LinkedInScraper()
        jobs = scraper.search_jobs(query.__dict__)
        
        # Save results
        for job in jobs:
            result = SearchResult(
                search_query_id=query_id,
                job_listing=job,
                match_score=100  # TODO: Implement proper matching
            )
            db.add(result)
            
        # Update last run time
        query.last_run = datetime.utcnow()
        db.commit()
        
        logger.info(f"Successfully executed search query {query_id}")
        
    except Exception as e:
        logger.error(f"Error executing search query {query_id}: {str(e)}")
        db.rollback()
        
    finally:
        db.close()

@shared_task
def cleanup_old_results():
    """
    Celery task to clean up old search results
    """
    db = SessionLocal()
    try:
        # Delete results older than 30 days
        old_results = db.query(SearchResult)\
            .filter(SearchResult.created_at < datetime.utcnow() - timedelta(days=30))\
            .all()
            
        for result in old_results:
            db.delete(result)
            
        db.commit()
        logger.info(f"Cleaned up {len(old_results)} old search results")
        
    except Exception as e:
        logger.error(f"Error cleaning up old results: {str(e)}")
        db.rollback()
        
    finally:
        db.close() 