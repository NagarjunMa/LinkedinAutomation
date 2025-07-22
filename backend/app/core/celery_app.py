from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "linkedin_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.search_tasks", "app.tasks.scoring_tasks"]
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
    beat_schedule={
        # Refresh all active search queries every 60 minutes
        'refresh-job-feeds': {
            'task': 'app.tasks.search_tasks.refresh_all_active_searches',
            'schedule': 3600.0,  # 60 minutes in seconds
        },
        # Clean up old job results every 24 hours
        'cleanup-old-results': {
            'task': 'app.tasks.search_tasks.cleanup_old_results',
            'schedule': 86400.0,  # 24 hours in seconds
        },
        # Clean up old job scores every 24 hours
        'cleanup-old-scores': {
            'task': 'app.tasks.scoring_tasks.cleanup_old_job_scores',
            'schedule': 86400.0,  # 24 hours in seconds
        },
        # AI job scoring for all users (runs 30 minutes after job fetching)
        'ai-job-scoring': {
            'task': 'app.tasks.search_tasks.score_jobs_for_all_users',
            'schedule': 3600.0,  # 60 minutes (30 min offset from job fetching)
        },
        # Generate daily digests (runs 1 hour after job scoring)
        'daily-digests': {
            'task': 'app.tasks.search_tasks.generate_daily_digests',
            'schedule': 86400.0,  # Once per day
        },
        # Clean up old job scores weekly
        'cleanup-old-scores': {
            'task': 'app.tasks.search_tasks.cleanup_old_job_scores',
            'schedule': 604800.0,  # 7 days in seconds
        },
    },
    beat_schedule_filename='celerybeat-schedule',
)

# Import tasks
from app.tasks import search_tasks  # noqa 