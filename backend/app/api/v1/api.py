from fastapi import APIRouter, Depends
from app.api.v1.endpoints import jobs, profiles, user_profiles, logs
from app.api.v1.endpoints import resumes_v2
from app.api.v1.endpoints import jd
from app.api.v1.endpoints import credits
from app.api.v1.endpoints import exports
from app.api.v1.endpoints import tailored_resumes
from app.api.v1.endpoints import webhooks
from app.api.v1.endpoints import admin_metrics
from app.api.v1.endpoints import analytics
from app.core.config import settings
from app.core.auth import require_path_user_matches_current, get_current_user_id

api_router = APIRouter()

# Core feature endpoints only
api_router.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(require_path_user_matches_current)],
)
api_router.include_router(
    profiles.router,
    prefix="/profiles",
    tags=["profiles"],
    dependencies=[Depends(require_path_user_matches_current)],
)
if settings.ENABLE_LEGACY_JOB_EXTRACTION:
    from app.api.v1.endpoints import job_extraction

    api_router.include_router(
        job_extraction.router,
        prefix="/jobs",
        tags=["job-extraction"],
        dependencies=[Depends(get_current_user_id)],
    )
api_router.include_router(resumes_v2.router, prefix="/resumes", tags=["resumes-v2"])
api_router.include_router(
    user_profiles.router,
    prefix="/user-profiles",
    tags=["user-profiles"],
    dependencies=[Depends(require_path_user_matches_current)],
)
api_router.include_router(logs.router, prefix="/logs", tags=["logging"])
# Phase-1 new routes
api_router.include_router(jd.router)
api_router.include_router(credits.router)
# Phase-2 new routes
api_router.include_router(exports.router)
api_router.include_router(tailored_resumes.router)
# Phase-4 new routes. Billing is dormant for the freemium launch.
if settings.ENABLE_BILLING:
    api_router.include_router(webhooks.router)
api_router.include_router(admin_metrics.router)
api_router.include_router(analytics.router)
