from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "linkedin_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.job_extraction_tasks",  # Future AI tasks
        "app.tasks.credit_tasks",          # Monthly credit grant
    ]
)

# AI-optimized Celery configuration for heavy workloads
celery_app.conf.update(
    # Serialization and compression
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_compression="gzip",  # Reduce memory for large AI payloads

    # Timezone settings
    timezone="UTC",
    enable_utc=True,

    # Task tracking and progress
    task_track_started=True,
    task_always_eager=False,
    task_store_eager_result=True,  # Store results for immediate tasks

    # Worker optimization for AI workloads
    worker_prefetch_multiplier=1,  # Prevent memory buildup with large AI tasks
    worker_max_tasks_per_child=50,  # Restart workers to prevent memory leaks
    worker_max_memory_per_child=500000,  # 500MB limit per worker (AI models can be memory-intensive)

    # Task timeouts for AI operations
    task_time_limit=900,  # 15 minutes for heavy AI tasks
    task_soft_time_limit=840,  # 14 minutes soft limit

    # Result backend optimization
    result_expires=3600,  # 1 hour - keep results for status checking
    result_persistent=True,  # Persist results across restarts

    # Task routing for different workload types
    task_routes={
        'app.tasks.job_extraction_tasks.*': {'queue': 'ai_light'},
    },

    # Retry configuration for AI tasks
    task_default_retry_delay=60,  # 1 minute between retries
    task_max_retries=3,  # Maximum retry attempts for failed AI tasks

    # Monitoring and logging
    task_send_events=True,  # Enable events for monitoring
    worker_send_task_events=True,  # Enable task events

    # Security
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
)

# Beat schedule for automated tasks
celery_app.conf.beat_schedule = {
    # Grant 20 credits to every user at midnight UTC on the 1st of each month.
    "credits.grant_monthly": {
        "task": "credits.grant_monthly",
        "schedule": crontab(0, 0, day_of_month="1"),
    },
}
