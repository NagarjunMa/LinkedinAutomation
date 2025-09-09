#!/usr/bin/env python3
"""
Check system status and health - Simplified system without automated job fetching
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models.job import JobListing
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """Check database connection and status"""
    try:
        db = SessionLocal()
        
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

def check_redis():
    """Check Redis connection"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        logger.info("Redis: ✅ Connected")
        return True
    except Exception as e:
        logger.error(f"Redis: ❌ Connection failed - {e}")
        return False

def check_celery():
    """Check Celery status"""
    try:
        from app.core.celery_app import celery_app
        
        # Check if Celery can connect to broker
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            logger.info("Celery: ✅ Workers connected")
            for worker, info in stats.items():
                logger.info(f"  Worker: {worker}")
        else:
            logger.warning("Celery: ⚠️ No workers connected")
        
        return True
        
    except Exception as e:
        logger.error(f"Celery check failed: {e}")
        return False

def main():
    """Main status check function"""
    logger.info("🔍 System Status Check - Simplified Version")
    logger.info("=" * 50)
    logger.info("Note: Automated job fetching has been removed")
    logger.info("Jobs are now extracted on-demand from URLs")
    logger.info("=" * 50)
    
    # Check database
    db_ok = check_database()
    
    # Check Redis
    redis_ok = check_redis()
    
    # Check Celery
    celery_ok = check_celery()
    
    # Summary
    logger.info("\n📊 Summary:")
    logger.info(f"  Database: {'✅' if db_ok else '❌'}")
    logger.info(f"  Redis: {'✅' if redis_ok else '❌'}")
    logger.info(f"  Celery: {'✅' if celery_ok else '❌'}")
    
    if all([db_ok, redis_ok, celery_ok]):
        logger.info("\n🎉 All systems operational!")
        logger.info("System is ready for URL-based job extraction")
    else:
        logger.warning("\n⚠️ Some systems have issues")
        if not redis_ok:
            logger.info("  • Start Redis: redis-server")
        if not celery_ok:
            logger.info("  • Start Celery worker: celery -A app.core.celery_app worker --loglevel=info")
    
    logger.info("\n💡 How to use the system:")
    logger.info("  1. Use the URL extraction endpoint to extract jobs")
    logger.info("  2. Jobs are processed on-demand, no background fetching")
    logger.info("  3. Email monitoring still works for application tracking")

if __name__ == "__main__":
    main() 