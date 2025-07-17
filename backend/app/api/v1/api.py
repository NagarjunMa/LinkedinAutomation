from fastapi import APIRouter
from app.api.v1.endpoints import jobs, search, export, analytics

api_router = APIRouter()
 
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"]) 