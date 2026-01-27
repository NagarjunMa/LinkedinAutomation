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

# Beat schedule for automated tasks
# Email scanning tasks disabled after refactoring
celery_app.conf.beat_schedule = {
    # Email tasks have been archived
    # Add other scheduled tasks here as needed
}

# Import tasks
# Email tasks disabled after refactoring
# from app.tasks import email_monitoring_tasks, email_scanning_tasks  # noqa 