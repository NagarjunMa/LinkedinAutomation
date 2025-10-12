from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, String
from app.db.rls_session import get_db, set_current_user
from app.models.job import JobListing
from app.schemas.job import JobListingResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[JobListingResponse])
async def search_jobs(
    q: str = Query(..., description="Search query for jobs, companies, or domains"),
    user_id: str = Query(default="demo_user", description="User ID for RLS context"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Search jobs by company name, job title, or domain.
    
    This endpoint performs a comprehensive search across:
    - Job title (case-insensitive partial match)
    - Company name (case-insensitive partial match) 
    - Location (case-insensitive partial match)
    - Skills (JSON array search)
    - Description (case-insensitive partial match)
    
    The search is optimized for finding relevant jobs based on user input.
    """
    try:
        # Set the current user context for RLS
        set_current_user(user_id)
        
        # Clean and prepare search query
        search_query = q.strip()
        if not search_query:
            return []
        
        # Create base query
        query = db.query(JobListing).filter(JobListing.is_active == True)
        
        # Build search conditions using OR logic across multiple fields
        search_conditions = []
        
        # Search in job title
        search_conditions.append(JobListing.title.ilike(f"%{search_query}%"))
        
        # Search in company name
        search_conditions.append(JobListing.company.ilike(f"%{search_query}%"))
        
        # Search in location
        search_conditions.append(JobListing.location.ilike(f"%{search_query}%"))
        
        # Search in job description
        search_conditions.append(JobListing.description.ilike(f"%{search_query}%"))
        
        # Search in requirements
        search_conditions.append(JobListing.requirements.ilike(f"%{search_query}%"))
        
        # Search in skills (JSON array) - Convert to text for compatibility
        # This searches the JSON representation as text
        search_conditions.append(
            func.cast(JobListing.skills, String).ilike(f"%{search_query}%")
        )
        
        # Apply the search conditions with OR logic
        query = query.filter(or_(*search_conditions))
        
        # Order by recency for now (simplified)
        query = query.order_by(JobListing.extracted_date.desc())
        
        # Apply pagination
        jobs = query.offset(skip).limit(limit).all()
        
        logger.info(f"Search query '{search_query}' returned {len(jobs)} results for user {user_id}")
        
        return jobs
        
    except Exception as e:
        logger.error(f"Error searching jobs: {str(e)}")
        logger.error(f"Search query: '{search_query}'")
        logger.error(f"User ID: {user_id}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error performing job search: {str(e)}")

@router.get("/suggestions", response_model=List[str])
async def get_search_suggestions(
    q: str = Query(..., description="Partial search query for suggestions"),
    user_id: str = Query(default="demo_user", description="User ID for RLS context"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of suggestions"),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions based on partial input.
    
    Returns suggestions from:
    - Company names
    - Job titles
    - Locations
    """
    try:
        # Set the current user context for RLS
        set_current_user(user_id)
        
        search_query = q.strip()
        if len(search_query) < 2:
            return []
        
        suggestions = set()
        
        # Get company name suggestions
        company_suggestions = db.query(JobListing.company).filter(
            and_(
                JobListing.is_active == True,
                JobListing.company.ilike(f"%{search_query}%")
            )
        ).distinct().limit(limit).all()
        
        for company in company_suggestions:
            suggestions.add(company[0])
        
        # Get job title suggestions
        title_suggestions = db.query(JobListing.title).filter(
            and_(
                JobListing.is_active == True,
                JobListing.title.ilike(f"%{search_query}%")
            )
        ).distinct().limit(limit).all()
        
        for title in title_suggestions:
            suggestions.add(title[0])
        
        # Get location suggestions
        location_suggestions = db.query(JobListing.location).filter(
            and_(
                JobListing.is_active == True,
                JobListing.location.ilike(f"%{search_query}%"),
                JobListing.location.isnot(None)
            )
        ).distinct().limit(limit).all()
        
        for location in location_suggestions:
            if location[0]:
                suggestions.add(location[0])
        
        # Convert to list and sort
        result = sorted(list(suggestions))[:limit]
        
        logger.info(f"Generated {len(result)} suggestions for query '{search_query}'")
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting search suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting search suggestions")

@router.get("/stats")
async def get_search_stats(
    user_id: str = Query(default="demo_user", description="User ID for RLS context"),
    db: Session = Depends(get_db)
):
    """
    Get search statistics for the user.
    """
    try:
        # Set the current user context for RLS
        set_current_user(user_id)
        
        # Get total job count
        total_jobs = db.query(JobListing).filter(JobListing.is_active == True).count()
        
        # Get unique companies count
        unique_companies = db.query(JobListing.company).filter(
            JobListing.is_active == True
        ).distinct().count()
        
        # Get unique locations count
        unique_locations = db.query(JobListing.location).filter(
            and_(
                JobListing.is_active == True,
                JobListing.location.isnot(None)
            )
        ).distinct().count()
        
        return {
            "total_jobs": total_jobs,
            "unique_companies": unique_companies,
            "unique_locations": unique_locations
        }
        
    except Exception as e:
        logger.error(f"Error getting search stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting search statistics")