from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "linkedin_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.email_monitoring_tasks", "app.tasks.email_scanning_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_always_eager=False,
    worker_prefetch_multiplier=1,
)

# Beat schedule for automated email scanning tasks
celery_app.conf.beat_schedule = {
    # Urgent email check every 2 hours
    'check-urgent-emails': {
        'task': 'app.tasks.email_scanning_tasks.check_urgent_emails',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
    },
    
    # User-scheduled full scans - check every 30 minutes
    'process-scheduled-email-scans': {
        'task': 'app.tasks.email_scanning_tasks.process_scheduled_scans',
        'schedule': crontab(minute='*/30'),  # Check every 30 min
    },
    
    # Health monitoring every hour
    'monitor-email-scanning-health': {
        'task': 'app.tasks.email_scanning_tasks.monitor_email_scanning_health',
        'schedule': crontab(minute=0),  # Every hour
    },
}

# Import tasks
from app.tasks import email_monitoring_tasks, email_scanning_tasks  # noqa 