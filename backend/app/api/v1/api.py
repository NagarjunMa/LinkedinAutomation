from fastapi import APIRouter
from app.api.v1.endpoints import (
    jobs, profiles, job_extraction, resumes, user_profiles,
    simple_referrals, activity, logs
)

api_router = APIRouter()

# Core feature endpoints only
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(job_extraction.router, prefix="/jobs", tags=["job-extraction"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(user_profiles.router, prefix="/user-profiles", tags=["user-profiles"])
api_router.include_router(simple_referrals.router, prefix="/simple-referrals", tags=["simple-referrals"])
api_router.include_router(activity.router, prefix="/activity", tags=["activity"])
api_router.include_router(logs.router, prefix="/logs", tags=["logging"]) 