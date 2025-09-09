from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "linkedin_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.email_monitoring_tasks"]  # Only keep email monitoring tasks
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
    # Removed beat_schedule - no more automated job fetching
)

# Import tasks
from app.tasks import email_monitoring_tasks  # noqa 