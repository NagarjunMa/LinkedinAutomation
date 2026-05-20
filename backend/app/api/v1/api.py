from fastapi import APIRouter
from app.api.v1.endpoints import (
    jobs, profiles, job_extraction, resumes, user_profiles, logs
)
from app.api.v1.endpoints import resumes_v2
from app.api.v1.endpoints import jd
from app.api.v1.endpoints import credits

api_router = APIRouter()

# Core feature endpoints only
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(job_extraction.router, prefix="/jobs", tags=["job-extraction"])
# resumes_v2 is registered BEFORE the legacy resumes router so its overlapping
# routes (e.g. POST /upload) take precedence during routing.
api_router.include_router(resumes_v2.router, prefix="/resumes", tags=["resumes-v2"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(user_profiles.router, prefix="/user-profiles", tags=["user-profiles"])
api_router.include_router(logs.router, prefix="/logs", tags=["logging"])
# Phase-1 new routes
api_router.include_router(jd.router)
api_router.include_router(credits.router)
