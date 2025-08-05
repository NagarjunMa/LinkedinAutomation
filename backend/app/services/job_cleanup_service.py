from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.job import JobListing
from app.utils.logger import get_logger

logger = get_logger(__name__)

class JobCleanupService:
    """Service for cleaning up old job listings"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def cleanup_old_jobs(self, days_old: int = 20) -> dict:
        """Delete jobs older than specified days that haven't been applied to"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            old_jobs_query = self.db.query(JobListing).filter(
                and_(
                    JobListing.extracted_date < cutoff_date,
                    JobListing.applied == False
                )
            )
            
            old_jobs_count = old_jobs_query.count()
            if old_jobs_count == 0:
                return {
                    "status": "success",
                    "message": f"No jobs older than {days_old} days found",
                    "deleted_count": 0,
                    "cutoff_date": cutoff_date.isoformat()
                }
            
            deleted_count = old_jobs_query.delete(synchronize_session=False)
            self.db.commit()
            
            return {
                "status": "success",
                "message": f"Successfully deleted {deleted_count} jobs older than {days_old} days",
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during job cleanup: {str(e)}")
            return {
                "status": "error",
                "message": f"Error during cleanup: {str(e)}",
                "deleted_count": 0,
                "cutoff_date": cutoff_date.isoformat() if 'cutoff_date' in locals() else None
            }
    
    def get_cleanup_stats(self, days_old: int = 20) -> dict:
        """Get statistics about jobs that would be cleaned up"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_unapplied_jobs = self.db.query(JobListing).filter(
                and_(
                    JobListing.extracted_date < cutoff_date,
                    JobListing.applied == False
                )
            ).count()
            
            old_applied_jobs = self.db.query(JobListing).filter(
                and_(
                    JobListing.extracted_date < cutoff_date,
                    JobListing.applied == True
                )
            ).count()
            
            total_old_jobs = self.db.query(JobListing).filter(
                JobListing.extracted_date < cutoff_date
            ).count()
            
            return {
                "cutoff_date": cutoff_date.isoformat(),
                "days_old": days_old,
                "old_unapplied_jobs": old_unapplied_jobs,
                "old_applied_jobs": old_applied_jobs,
                "total_old_jobs": total_old_jobs,
                "would_be_deleted": old_unapplied_jobs
            }
            
        except Exception as e:
            logger.error(f"Error getting cleanup stats: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting stats: {str(e)}"
            }
    
    def cleanup_by_user(self, user_id: str, days_old: int = 20) -> dict:
        """Clean up old jobs (no user filtering since JobListing lacks user_id)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            old_jobs_query = self.db.query(JobListing).filter(
                and_(
                    JobListing.extracted_date < cutoff_date,
                    JobListing.applied == False
                )
            )
            
            old_jobs_count = old_jobs_query.count()
            if old_jobs_count == 0:
                return {
                    "status": "success",
                    "message": f"No jobs older than {days_old} days found for cleanup",
                    "deleted_count": 0,
                    "user_id": user_id,
                    "cutoff_date": cutoff_date.isoformat()
                }
            
            deleted_count = old_jobs_query.delete(synchronize_session=False)
            self.db.commit()
            
            return {
                "status": "success",
                "message": f"Successfully deleted {deleted_count} old jobs",
                "deleted_count": deleted_count,
                "user_id": user_id,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during user job cleanup: {str(e)}")
            return {
                "status": "error",
                "message": f"Error during cleanup: {str(e)}",
                "deleted_count": 0,
                "user_id": user_id
            } 