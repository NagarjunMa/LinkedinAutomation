from app.core.celery_app import celery_app
from app.db.rls_session import SessionLocal
from app.services.job_cleanup_service import JobCleanupService
from app.utils.logger import get_logger

logger = get_logger(__name__)

@celery_app.task
def cleanup_old_jobs_task(days_old: int = 20):
    """Automatically clean up old job listings"""
    try:
        db = SessionLocal()
        try:
            cleanup_service = JobCleanupService(db)
            result = cleanup_service.cleanup_old_jobs(days_old)
            return result
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        return {"status": "error", "message": f"Task error: {str(e)}"}

@celery_app.task
def cleanup_user_jobs_task(user_id: str, days_old: int = 20):
    """Clean up old jobs for a specific user"""
    try:
        db = SessionLocal()
        try:
            cleanup_service = JobCleanupService(db)
            result = cleanup_service.cleanup_by_user(user_id, days_old)
            return result
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in user cleanup task: {str(e)}")
        return {"status": "error", "user_id": user_id, "message": f"Task error: {str(e)}"}

@celery_app.task
def get_cleanup_stats_task(days_old: int = 20):
    """Get cleanup statistics"""
    try:
        db = SessionLocal()
        try:
            cleanup_service = JobCleanupService(db)
            return cleanup_service.get_cleanup_stats(days_old)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in cleanup stats task: {str(e)}")
        return {"status": "error", "message": f"Task error: {str(e)}"} 