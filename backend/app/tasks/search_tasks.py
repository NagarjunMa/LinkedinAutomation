from celery import shared_task
from app.core.celery_app import celery_app
from app.services.job_aggregator import JobAggregator
from app.services.job_scorer import job_scorer
from app.db.session import SessionLocal
from app.models.job import SearchQuery, SearchResult, JobListing, RSSFeedConfiguration, UserProfile
import logging
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@shared_task
def execute_search_task(query_id: int):
    """
    DEPRECATED: Legacy search query task - no longer used
    """
    logger.info(f"Legacy search task called for query {query_id} - skipping (search queries disabled)")
    return

@shared_task
def refresh_rss_feeds_direct():
    """
    NEW: Direct RSS feed processing - fetches from all active RSS feeds once
    Much more efficient than the old search query approach
    """
    db = SessionLocal()
    try:
        logger.info("Starting direct RSS feed refresh...")
        
        # Get all active RSS feed configurations
        active_feeds = db.query(RSSFeedConfiguration).filter(
            RSSFeedConfiguration.is_active == True
        ).all()
        
        logger.info(f"Processing {len(active_feeds)} active RSS feeds")
        
        if not active_feeds:
            logger.warning("No active RSS feeds found")
            return
        
        # Use job aggregator to fetch jobs from all feeds
        aggregator = JobAggregator()
        
        # Create a dummy query to trigger all RSS feeds
        dummy_query = {
            "title": "Software Engineer",
            "location": "United States", 
            "keywords": "software,engineering,development",
            "enhanced_search": True
        }
        
        # Run async search in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            jobs = loop.run_until_complete(aggregator.search_jobs(dummy_query))
        finally:
            loop.close()
        
        logger.info(f"Found {len(jobs)} total jobs from all RSS feeds")
        
        # Save jobs to database (skip duplicates)
        saved_count = 0
        duplicate_count = 0
        
        for job in jobs:
            # Check if job already exists (by title, company, location)
            existing = db.query(JobListing).filter(
                JobListing.title == job.title,
                JobListing.company == job.company,
                JobListing.location == job.location
            ).first()
            
            if not existing:
                # Save new job
                db_job = JobListing(
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    description=job.description,
                    requirements=job.requirements,
                    job_type=job.job_type,
                    experience_level=job.experience_level,
                    salary_range=job.salary_range,
                    skills=job.skills,
                    application_url=job.application_url,
                    source=job.source,
                    source_url=job.source_url,
                    is_active=job.is_active,
                    posted_date=job.posted_date,
                    extracted_date=job.extracted_date,
                    applied=job.applied
                )
                db.add(db_job)
                saved_count += 1
            else:
                duplicate_count += 1
        
        db.commit()
        logger.info(f"RSS Feed Refresh Complete: {saved_count} new jobs saved, {duplicate_count} duplicates skipped")
        
        return {
            "total_found": len(jobs),
            "new_saved": saved_count, 
            "duplicates_skipped": duplicate_count
        }
        
    except Exception as e:
        logger.error(f"Error in direct RSS feed refresh: {str(e)}")
        db.rollback()
        raise
        
    finally:
        db.close()

@shared_task
def refresh_all_active_searches():
    """
    UPDATED: Now uses direct RSS feed processing instead of search queries
    """
    logger.info("Starting refresh - using direct RSS feed processing")
    
    # Call the new direct RSS feed task
    result = refresh_rss_feeds_direct()
    
    logger.info("Direct RSS feed refresh completed")
    return result

@shared_task
def cleanup_old_results():
    """
    Celery task to clean up old search results
    """
    db = SessionLocal()
    try:
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

# =====================================================
# AI-POWERED JOB SCORING TASKS
# =====================================================

@shared_task
def score_jobs_for_all_users():
    """
    Daily task to score new jobs for all users with profiles
    This runs after refresh_all_active_searches to score the new jobs
    """
    logger.info("Starting AI job scoring for all users...")
    
    try:
        # Run async job scoring
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(job_scorer.score_all_users_daily())
        finally:
            loop.close()
        
        logger.info(f"AI job scoring complete: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in AI job scoring task: {str(e)}")
        return {"error": str(e), "users_processed": 0, "total_scores_generated": 0}

@shared_task
def score_jobs_for_user_task(user_id: str, job_limit: int = 50, days_back: int = 1):
    """
    Score jobs for a specific user (can be triggered manually or by events)
    """
    logger.info(f"Starting AI job scoring for user {user_id}...")
    
    try:
        # Run async job scoring for single user
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            scored_jobs = loop.run_until_complete(
                job_scorer.score_jobs_for_user(user_id, job_limit, days_back)
            )
        finally:
            loop.close()
        
        result = {
            "user_id": user_id,
            "jobs_scored": len(scored_jobs),
            "high_scores": len([j for j in scored_jobs if j['compatibility_score'] >= 80]),
            "medium_scores": len([j for j in scored_jobs if 60 <= j['compatibility_score'] < 80])
        }
        
        logger.info(f"AI job scoring complete for user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error scoring jobs for user {user_id}: {str(e)}")
        return {"error": str(e), "user_id": user_id, "jobs_scored": 0}

@shared_task 
def generate_daily_digests():
    """
    Generate daily job digest emails for all users
    Should run after job scoring is complete
    """
    logger.info("Starting daily digest generation...")
    
    db = SessionLocal()
    try:
        # Get all users with profiles
        active_users = db.query(UserProfile).all()
        
        results = {
            "users_processed": 0,
            "digests_generated": 0,
            "errors": 0
        }
        
        for user_profile in active_users:
            try:
                # Get top matches for user
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    top_matches = loop.run_until_complete(
                        job_scorer.get_top_matches_for_user(user_profile.user_id, limit=10, min_score=70.0)
                    )
                finally:
                    loop.close()
                
                if top_matches:
                    # TODO: Generate and send digest email using AI service
                    # For now, just log that we would send a digest
                    logger.info(f"Would send digest to {user_profile.user_id} with {len(top_matches)} top matches")
                    results["digests_generated"] += 1
                
                results["users_processed"] += 1
                
            except Exception as e:
                logger.error(f"Error generating digest for user {user_profile.user_id}: {str(e)}")
                results["errors"] += 1
        
        logger.info(f"Daily digest generation complete: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in daily digest generation: {str(e)}")
        return {"users_processed": 0, "digests_generated": 0, "errors": 1}
    finally:
        db.close()

@shared_task
def cleanup_old_job_scores():
    """
    Clean up old job scores to keep database efficient
    Removes scores older than 30 days for jobs that are no longer active
    """
    db = SessionLocal()
    try:
        from app.models.job import JobScore
        
        # Find old scores for inactive jobs
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_scores = db.query(JobScore).join(JobListing).filter(
            JobScore.scored_at < cutoff_date,
            JobListing.is_active == False
        ).all()
        
        for score in old_scores:
            db.delete(score)
        
        db.commit()
        logger.info(f"Cleaned up {len(old_scores)} old job scores")
        
        return {"scores_cleaned": len(old_scores)}
        
    except Exception as e:
        logger.error(f"Error cleaning up old job scores: {str(e)}")
        db.rollback()
        return {"error": str(e), "scores_cleaned": 0}
    finally:
        db.close() 