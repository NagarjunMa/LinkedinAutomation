from fastapi import APIRouter
from app.api.v1.endpoints import jobs, export, analytics, profiles, job_extraction, email_agent, contacts, resumes, application_stats, search, analytics_intelligence, referral, user_profiles, activity, email_scanning, application_questions, email

api_router = APIRouter()

api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(analytics_intelligence.router, prefix="/analytics-intelligence", tags=["analytics-intelligence"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(job_extraction.router, prefix="/jobs", tags=["job-extraction"])
api_router.include_router(email_agent.router, prefix="/email-agent", tags=["email-agent"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(application_stats.router, prefix="/stats", tags=["application-stats"])
api_router.include_router(referral.router, prefix="/referral", tags=["referral"])
api_router.include_router(user_profiles.router, prefix="/user-profiles", tags=["user-profiles"])
api_router.include_router(activity.router, prefix="/activity", tags=["activity"])
api_router.include_router(email_scanning.router, prefix="/email-scanning", tags=["email-scanning"])
api_router.include_router(application_questions.router, prefix="/application-questions", tags=["application-questions"])
api_router.include_router(email.router, prefix="/email", tags=["email"]) 