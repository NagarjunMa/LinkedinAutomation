from fastapi import APIRouter
from app.api.v1.endpoints import jobs, export, analytics, profiles, job_extraction, email_agent, contacts, resumes

api_router = APIRouter()
 
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
# api_router.include_router(search.router, prefix="/search", tags=["search"])  # REMOVED: Search queries disabled
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(job_extraction.router, prefix="/jobs", tags=["job-extraction"])
api_router.include_router(email_agent.router, prefix="/email-agent", tags=["email-agent"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"]) 