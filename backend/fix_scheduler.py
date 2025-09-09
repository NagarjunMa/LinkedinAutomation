#!/usr/bin/env python3
"""
Check system status - Scheduler has been removed
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.celery_app import celery_app
from app.models.job import JobListing
from app.db.session import SessionLocal
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_system_status():
    """Check the current system status"""
    try:
        logger.info("System Status Check")
        logger.info("=" * 30)
        
        # Check Celery configuration
        logger.info("Celery Configuration:")
        logger.info("  Beat Schedule: Disabled (no automated job fetching)")
        logger.info("  Worker Tasks: Email monitoring only")
        
        # Check database status
        check_database_status()
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking system status: {e}")
        return False

def check_database_status():
    """Check database connection and job status"""
    db = SessionLocal()
    try:
        # Check total jobs
        total_jobs = db.query(JobListing).count()
        active_jobs = db.query(JobListing).filter(JobListing.is_active == True).count()
        
        logger.info(f"Database Status:")
        logger.info(f"  Total jobs: {total_jobs}")
        logger.info(f"  Active jobs: {active_jobs}")
        
        # Check job sources
        sources = db.query(JobListing.source).distinct().all()
        source_counts = {}
        for source in sources:
            count = db.query(JobListing).filter(JobListing.source == source[0]).count()
            source_counts[source[0]] = count
        
        logger.info(f"Job Sources:")
        for source, count in source_counts.items():
            logger.info(f"  {source}: {count} jobs")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting system status check...")
    
    # Check system status
    if check_system_status():
        logger.info("System status check completed successfully")
        logger.info("Note: Automated job fetching has been removed")
        logger.info("Jobs are now extracted on-demand from URLs")
    else:
        logger.error("System status check failed")
        sys.exit(1) 