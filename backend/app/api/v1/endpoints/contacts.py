from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import asyncio

from app.db.rls_session import get_db, set_current_user
from app.models import Contact, JobListing
from app.services.contact_discovery import ContactDiscoveryService
from app.services.apollo_client import ApolloClient
from app.utils.logger import get_logger
from app.core.auth import get_authenticated_user_id

logger = get_logger(__name__)
router = APIRouter()

@router.get("/job/{job_id}")
async def get_job_contacts(
    job_id: int,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Get contacts for a specific job"""
    try:
        set_current_user(user_id)
        
        # Check if job exists
        job = db.query(JobListing).filter(JobListing.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get contacts for the job
        discovery_service = ContactDiscoveryService(db)
        contacts = discovery_service.get_job_contacts(job_id)
        
        return {
            "job_id": job_id,
            "job_title": job.title,
            "company": job.company,
            "contacts": contacts
        }
        
    except Exception as e:
        logger.error(f"Error getting contacts for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving contacts")

@router.post("/job/{job_id}/discover")
async def discover_job_contacts(
    job_id: int,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Discover contacts for a specific job (DISABLED - no background tasks)"""
    try:
        set_current_user(user_id)
        
        # Check if job exists
        job = db.query(JobListing).filter(JobListing.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Background task functionality disabled
        logger.info(f"Contact discovery disabled for job {job_id} - no background tasks available")
        
        return {
            "status": "disabled",
            "message": f"Contact discovery disabled - background tasks not available",
            "job_id": job_id,
            "reason": "Background task system removed during cleanup"
        }
        
    except Exception as e:
        logger.error(f"Error in contact discovery for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Error in contact discovery")

@router.get("/usage")
async def get_apollo_usage(
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Get Apollo.io API usage statistics"""
    try:
        set_current_user(user_id)
        
        # Get usage stats
        apollo_client = ApolloClient(db)
        usage_stats = apollo_client.get_usage_stats()
        
        return {
            "status": "success",
            "usage": usage_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting Apollo usage stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving usage statistics")

@router.get("/company/{company_name}")
async def get_company_contacts(
    company_name: str,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Get all contacts for a specific company"""
    try:
        set_current_user(user_id)
        
        # Get contacts for the company
        contacts = db.query(Contact).filter(
            Contact.company.ilike(f"%{company_name}%")
        ).all()
        
        # Group by type
        grouped_contacts = {
            "recruiters": [],
            "engineers": []
        }
        
        for contact in contacts:
            if contact.type == "recruiter":
                grouped_contacts["recruiters"].append({
                    "id": str(contact.id),
                    "name": contact.name,
                    "title": contact.title,
                    "email": contact.email,
                    "linkedin_url": contact.linkedin_url,
                    "location": contact.location,
                    "confidence_score": contact.confidence_score
                })
            elif contact.type == "engineer":
                grouped_contacts["engineers"].append({
                    "id": str(contact.id),
                    "name": contact.name,
                    "title": contact.title,
                    "email": contact.email,
                    "linkedin_url": contact.linkedin_url,
                    "location": contact.location,
                    "confidence_score": contact.confidence_score
                })
        
        return {
            "company": company_name,
            "contacts": grouped_contacts,
            "total_contacts": len(contacts)
        }
        
    except Exception as e:
        logger.error(f"Error getting contacts for company {company_name}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving company contacts")

@router.post("/company/{company_name}/refresh")
async def refresh_company_contacts(
    company_name: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Refresh contacts for a specific company (DISABLED - no background tasks)"""
    try:
        set_current_user(user_id)
        
        # Background task functionality disabled
        logger.info(f"Contact refresh disabled for company {company_name} - no background tasks available")
        
        return {
            "status": "disabled",
            "message": f"Contact refresh disabled - background tasks not available",
            "company": company_name,
            "reason": "Background task system removed during cleanup"
        }
        
    except Exception as e:
        logger.error(f"Error in contact refresh for company {company_name}: {e}")
        raise HTTPException(status_code=500, detail="Error in contact refresh")

@router.get("/stats")
async def get_contact_stats(
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Get contact discovery statistics"""
    try:
        set_current_user(user_id)
        
        # Get total contacts
        total_contacts = db.query(Contact).count()
        
        # Get contacts by type
        recruiters = db.query(Contact).filter(Contact.type == "recruiter").count()
        engineers = db.query(Contact).filter(Contact.type == "engineer").count()
        
        # Get jobs with contacts
        jobs_with_contacts = db.query(JobListing).join(
            JobListing.contacts
        ).distinct().count()
        
        # Get total jobs
        total_jobs = db.query(JobListing).count()
        
        return {
            "total_contacts": total_contacts,
            "recruiters": recruiters,
            "engineers": engineers,
            "jobs_with_contacts": jobs_with_contacts,
            "total_jobs": total_jobs,
            "coverage_percentage": (jobs_with_contacts / total_jobs * 100) if total_jobs > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting contact stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving contact statistics")

@router.get("/search")
async def search_contacts(
    query: str = Query(..., description="Search query for contacts"),
    contact_type: Optional[str] = Query(None, description="Filter by contact type"),
    company: Optional[str] = Query(None, description="Filter by company"),
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Search contacts by name, title, or company"""
    try:
        set_current_user(user_id)
        
        # Build query
        contacts_query = db.query(Contact)
        
        # Add search filters
        if query:
            contacts_query = contacts_query.filter(
                (Contact.name.ilike(f"%{query}%")) |
                (Contact.title.ilike(f"%{query}%")) |
                (Contact.company.ilike(f"%{query}%"))
            )
        
        if contact_type:
            contacts_query = contacts_query.filter(Contact.type == contact_type)
        
        if company:
            contacts_query = contacts_query.filter(Contact.company.ilike(f"%{company}%"))
        
        # Execute query
        contacts = contacts_query.limit(50).all()
        
        # Format results
        results = []
        for contact in contacts:
            results.append({
                "id": str(contact.id),
                "name": contact.name,
                "title": contact.title,
                "company": contact.company,
                "email": contact.email,
                "linkedin_url": contact.linkedin_url,
                "location": contact.location,
                "type": contact.type,
                "confidence_score": contact.confidence_score
            })
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching contacts: {e}")
        raise HTTPException(status_code=500, detail="Error searching contacts") 