import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.analytics_intelligence import AnalyticsIntelligenceService
from app.models.user import User
from app.models.job import JobApplication
from app.core.celery_app import celery_app as celery

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3)
def update_user_analytics_task(self, user_id: str, days: int = 30):
    """
    Background task to update analytics for a specific user
    """
    db = SessionLocal()

    try:
        logger.info(f"Starting analytics update for user {user_id}")

        # Create analytics service
        analytics_service = AnalyticsIntelligenceService(db)

        # Generate fresh analytics
        analytics_data = asyncio.run(
            analytics_service.generate_user_analytics(user_id, days)
        )

        if analytics_data.get("metadata", {}).get("status") == "insufficient_data":
            logger.info(f"Insufficient data for analytics generation for user {user_id}")
            return {"status": "insufficient_data", "user_id": user_id}

        logger.info(f"Analytics successfully updated for user {user_id}")

        return {
            "status": "success",
            "user_id": user_id,
            "applications_analyzed": analytics_data.get("metadata", {}).get("total_applications", 0),
            "generation_time": analytics_data.get("metadata", {}).get("generation_time_seconds", 0),
            "insights_count": len(analytics_data.get("insights", []))
        }

    except Exception as e:
        logger.error(f"Analytics update failed for user {user_id}: {str(e)}")

        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying analytics update for user {user_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=300, exc=e)  # Retry after 5 minutes

        return {
            "status": "error",
            "user_id": user_id,
            "error": str(e)
        }

    finally:
        db.close()


@celery.task
def bulk_analytics_update_task(days: int = 30, batch_size: int = 10):
    """
    Update analytics for all active users in batches
    """
    db = SessionLocal()

    try:
        # Get users who have applications in the last X days and need analytics updates
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        active_users = db.query(User).join(
            JobApplication, User.user_id == JobApplication.user_id
        ).filter(
            JobApplication.created_at >= cutoff_date
        ).distinct().all()

        logger.info(f"Found {len(active_users)} active users for analytics update")

        # Process users in batches to avoid overwhelming the system
        results = {
            "total_users": len(active_users),
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "insufficient_data": 0
        }

        for i in range(0, len(active_users), batch_size):
            batch = active_users[i:i + batch_size]

            logger.info(f"Processing batch {i//batch_size + 1}: users {i+1}-{min(i+batch_size, len(active_users))}")

            # Process batch
            for user in batch:
                try:
                    # Queue individual analytics update task
                    task_result = update_user_analytics_task.delay(user.user_id, days)

                    # Wait for completion (with timeout)
                    result = task_result.get(timeout=600)  # 10 minute timeout

                    results["processed"] += 1

                    if result["status"] == "success":
                        results["successful"] += 1
                    elif result["status"] == "insufficient_data":
                        results["insufficient_data"] += 1
                    else:
                        results["failed"] += 1

                except Exception as e:
                    logger.error(f"Batch processing failed for user {user.user_id}: {e}")
                    results["failed"] += 1
                    results["processed"] += 1

            # Small delay between batches to prevent system overload
            if i + batch_size < len(active_users):
                logger.info("Waiting 30 seconds before next batch...")
                import time
                time.sleep(30)

        logger.info(f"Bulk analytics update completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Bulk analytics update failed: {e}")
        return {"status": "error", "error": str(e)}

    finally:
        db.close()


@celery.task
def cleanup_expired_analytics_cache():
    """
    Clean up expired analytics cache entries
    """
    db = SessionLocal()

    try:
        from app.models.analytics import AnalyticsCache

        # Delete expired cache entries
        expired_count = db.query(AnalyticsCache).filter(
            AnalyticsCache.expires_at < datetime.utcnow()
        ).delete()

        db.commit()

        logger.info(f"Cleaned up {expired_count} expired analytics cache entries")

        return {
            "status": "success",
            "expired_entries_removed": expired_count
        }

    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        db.rollback()
        return {"status": "error", "error": str(e)}

    finally:
        db.close()


@celery.task
def analytics_health_check():
    """
    Perform health check on analytics system
    """
    db = SessionLocal()

    try:
        from app.models.analytics import UserAnalytics, AnalyticsCache

        # Count analytics records
        total_analytics = db.query(UserAnalytics).count()
        recent_analytics = db.query(UserAnalytics).filter(
            UserAnalytics.last_updated >= datetime.utcnow() - timedelta(days=7)
        ).count()

        # Count cache entries
        total_cache = db.query(AnalyticsCache).count()
        valid_cache = db.query(AnalyticsCache).filter(
            AnalyticsCache.expires_at > datetime.utcnow()
        ).count()

        # Check for users needing analytics updates
        from app.models.job import JobApplication

        users_needing_update = db.query(User).join(
            JobApplication, User.user_id == JobApplication.user_id
        ).outerjoin(
            UserAnalytics, User.user_id == UserAnalytics.user_id
        ).filter(
            JobApplication.created_at >= datetime.utcnow() - timedelta(days=30),
            or_(
                UserAnalytics.last_updated.is_(None),
                UserAnalytics.last_updated < datetime.utcnow() - timedelta(days=7)
            )
        ).distinct().count()

        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "analytics": {
                "total_records": total_analytics,
                "recent_updates": recent_analytics
            },
            "cache": {
                "total_entries": total_cache,
                "valid_entries": valid_cache,
                "hit_rate": round((valid_cache / max(total_cache, 1)) * 100, 2)
            },
            "pending_updates": users_needing_update
        }

        # Determine if system is healthy
        if recent_analytics == 0 and total_analytics > 0:
            health_status["status"] = "warning"
            health_status["warning"] = "No recent analytics updates"
        elif users_needing_update > 50:
            health_status["status"] = "warning"
            health_status["warning"] = f"{users_needing_update} users need analytics updates"

        logger.info(f"Analytics health check: {health_status['status']}")
        return health_status

    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

    finally:
        db.close()


@celery.task
def send_analytics_digest(user_id: str):
    """
    Send weekly analytics digest to user (if email notifications are enabled)
    """
    # This would integrate with your email system to send analytics summaries
    # For now, just log the action
    logger.info(f"Analytics digest requested for user {user_id}")

    # TODO: Implement email digest functionality
    return {
        "status": "success",
        "user_id": user_id,
        "action": "digest_logged"
    }


# Celery beat schedule for automated analytics updates
def setup_analytics_schedule():
    """
    Setup the Celery beat schedule for analytics tasks
    """
    return {
        # Update analytics for all users every 3 days at 2 AM
        'bulk-analytics-update': {
            'task': 'app.tasks.analytics_tasks.bulk_analytics_update_task',
            'schedule': crontab(hour=2, minute=0, day_of_week='*/3'),
            'kwargs': {'days': 30, 'batch_size': 10}
        },

        # Clean up expired cache every day at 3 AM
        'cleanup-analytics-cache': {
            'task': 'app.tasks.analytics_tasks.cleanup_expired_analytics_cache',
            'schedule': crontab(hour=3, minute=0),
        },

        # Health check every 6 hours
        'analytics-health-check': {
            'task': 'app.tasks.analytics_tasks.analytics_health_check',
            'schedule': crontab(minute=0, hour='*/6'),
        }
    }


# Add to your main Celery configuration
if hasattr(celery.conf, 'beat_schedule'):
    celery.conf.beat_schedule.update(setup_analytics_schedule())
else:
    celery.conf.beat_schedule = setup_analytics_schedule()