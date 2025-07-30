import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl, validator
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.job import JobListing, JobApplication, UserProfile
from app.services.url_job_extractor import url_job_extractor
from app.services.smart_job_scorer import smart_job_scorer
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# =====================================================
# REQUEST/RESPONSE MODELS
# =====================================================

class JobExtractionRequest(BaseModel):
    url: HttpUrl
    user_id: str
    auto_apply: bool = True
    application_notes: Optional[str] = None

    @validator('url')
    def validate_url(cls, v):
        url_str = str(v)
        if len(url_str) > 2000:
            raise ValueError('URL too long')
        return v

    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('User ID cannot be empty')
        return v.strip()

class BatchJobExtractionRequest(BaseModel):
    urls: List[HttpUrl]
    user_id: str
    auto_apply: bool = True

    @validator('urls')
    def validate_urls(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 URLs allowed per batch')
        return v

class JobExtractionResponse(BaseModel):
    success: bool
    job_id: Optional[int] = None
    application_id: Optional[int] = None
    extracted_job: dict
    compatibility_score: Optional[float] = None
    extraction_confidence: float
    message: str

class BatchJobExtractionResponse(BaseModel):
    success: bool
    total_processed: int
    successful_extractions: int
    failed_extractions: int
    results: List[JobExtractionResponse]

# =====================================================
# API ENDPOINTS
# =====================================================

@router.post("/extract-from-url", response_model=JobExtractionResponse)
async def extract_job_from_url(
    request: JobExtractionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Extract job details from URL and optionally create application entry
    
    This endpoint:
    1. Validates the URL
    2. Extracts job details using Jina AI Reader + OpenAI
    3. Saves job to database
    4. Optionally creates application tracking entry
    5. Triggers background job scoring
    """
    try:
        logger.info(f"Starting job extraction for user {request.user_id} from URL: {request.url}")
        
        # Check if user profile exists (optional - for better extraction context)
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == request.user_id).first()
        user_context = None
        
        if user_profile:
            user_context = {
                "skills": user_profile.programming_languages or [],
                "experience_level": user_profile.career_level or "entry",
                "locations": user_profile.preferred_locations or []
            }
        
        # Extract job details using our service
        job_data = await url_job_extractor.extract_job_details(str(request.url), user_context)
        
        # Check for duplicate jobs (same URL or similar title+company)
        existing_job = db.query(JobListing).filter(
            JobListing.application_url == str(request.url)
        ).first()
        
        if existing_job:
            logger.info(f"Found existing job with same URL: {existing_job.id}")
            
            # Check if user already has application for this job
            existing_application = db.query(JobApplication).filter(
                JobApplication.user_id == request.user_id,
                JobApplication.job_id == existing_job.id
            ).first()
            
            if existing_application:
                return JobExtractionResponse(
                    success=True,
                    job_id=existing_job.id,
                    application_id=existing_application.id,
                    extracted_job=job_data,
                    compatibility_score=None,
                    extraction_confidence=job_data.get("confidence", 0.8),
                    message="Job already exists and you have an existing application"
                )
        
        # Create new JobListing entry if not duplicate
        if not existing_job:
            logger.info(f"Creating new job listing with data: {job_data}")
            
            # Safely handle None values and string operations
            description = job_data.get("description") or ""
            requirements = job_data.get("requirements") or ""
            
            job_listing = JobListing(
                title=job_data.get("title") or "Unknown Position",
                company=job_data.get("company") or "Unknown Company",
                location=job_data.get("location") or "Location not specified",
                description=description[:1000] if description else "",  # Safe string slicing
                requirements=requirements[:500] if requirements else "",  # Safe string slicing
                job_type=job_data.get("job_type") or "Not specified",
                experience_level=job_data.get("experience_level") or "Not specified",
                salary_range=job_data.get("salary_range"),  # Can be None
                skills=job_data.get("skills") or [],  # Default to empty list
                application_url=str(request.url),
                source="url_extraction",
                source_url=str(request.url),
                is_active=True,
                posted_date=datetime.utcnow(),
                extracted_date=datetime.utcnow()
            )
            
            db.add(job_listing)
            db.commit()
            db.refresh(job_listing)
            
            logger.info(f"Created new job listing with ID: {job_listing.id}")
            if job_listing.id is None:
                logger.error("Job listing ID is None after commit/refresh")
                raise ValueError("Failed to create job listing - ID is None")
        else:
            job_listing = existing_job
        
        # Create application entry if requested
        application_id = None
        if request.auto_apply:
            logger.info(f"Creating job application for job_id: {job_listing.id}, user_id: {request.user_id}")
            if job_listing.id is None:
                logger.error("Cannot create application - job_listing.id is None")
                raise ValueError("Cannot create application - job listing has no ID")
                
            job_application = JobApplication(
                user_id=request.user_id,
                job_id=job_listing.id,
                application_status="interested",
                application_source="url_extraction",
                source_url=str(request.url),
                user_notes=request.application_notes or f"Extracted from {job_data.get('company', 'Unknown')} via AI",
                extraction_metadata={
                    "extraction_confidence": job_data.get("confidence", 0.8),
                    "extraction_method": job_data.get("extraction_method", "jina_ai_reader_openai"),
                    "extracted_at": job_data.get("extracted_at")
                }
            )
            db.add(job_application)
            db.commit()
            db.refresh(job_application)
            application_id = job_application.id
            
            logger.info(f"Created application entry with ID: {application_id}")
        
        # Trigger background job scoring (non-blocking)
        compatibility_score = None
        if job_listing.id and user_profile:
            try:
                # For immediate response, we'll use a placeholder score
                # The actual scoring will happen in background
                background_tasks.add_task(
                    trigger_job_scoring_background,
                    job_listing.id,
                    request.user_id
                )
                compatibility_score = 75.0  # Placeholder - will be updated by background task
                
            except Exception as e:
                logger.warning(f"Failed to trigger background scoring: {e}")
        
        return JobExtractionResponse(
            success=True,
            job_id=job_listing.id,
            application_id=application_id,
            extracted_job=job_data,
            compatibility_score=compatibility_score,
            extraction_confidence=job_data.get("confidence", 0.8),
            message=f"Successfully extracted job: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}"
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Extraction failed for {request.url}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to extract job details: {str(e)}"
        )

@router.post("/extract-multiple-urls", response_model=BatchJobExtractionResponse)
async def extract_multiple_jobs_from_urls(
    request: BatchJobExtractionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Extract job details from multiple URLs in batch
    """
    try:
        logger.info(f"Starting batch extraction for user {request.user_id} with {len(request.urls)} URLs")
        
        # Get user context for better extraction
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == request.user_id).first()
        user_context = None
        
        if user_profile:
            user_context = {
                "skills": user_profile.programming_languages or [],
                "experience_level": user_profile.career_level or "entry",
                "locations": user_profile.preferred_locations or []
            }
        
        # Process URLs one by one
        results = []
        successful = 0
        failed = 0
        
        for url in request.urls:
            try:
                # Create individual request
                individual_request = JobExtractionRequest(
                    url=url,
                    user_id=request.user_id,
                    auto_apply=request.auto_apply
                )
                
                # Process individual URL
                result = await extract_job_from_url(individual_request, background_tasks, db)
                results.append(result)
                
                if result.success:
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Failed to process URL {url}: {e}")
                failed_result = JobExtractionResponse(
                    success=False,
                    job_id=None,
                    application_id=None,
                    extracted_job={"title": f"Failed: {str(url)}", "company": "Error", "error": str(e)},
                    compatibility_score=None,
                    extraction_confidence=0.0,
                    message=f"Failed to extract: {str(e)}"
                )
                results.append(failed_result)
                failed += 1
        
        return BatchJobExtractionResponse(
            success=True,
            total_processed=len(request.urls),
            successful_extractions=successful,
            failed_extractions=failed,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Batch extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch extraction failed: {str(e)}")

@router.get("/extraction-stats/{user_id}")
async def get_extraction_stats(user_id: str, db: Session = Depends(get_db)):
    """
    Get extraction statistics for a user
    """
    try:
        # Count extracted jobs
        extracted_jobs = db.query(JobListing).filter(
            JobListing.source == "url_extraction"
        ).count()
        
        # Count user applications from extractions
        user_extractions = db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.application_source == "url_extraction"
        ).count()
        
        return {
            "user_id": user_id,
            "total_extracted_jobs": extracted_jobs,
            "user_extracted_applications": user_extractions,
            "available_for_extraction": True
        }
        
    except Exception as e:
        logger.error(f"Failed to get extraction stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get extraction statistics")

# =====================================================
# BACKGROUND TASK FUNCTIONS
# =====================================================

async def trigger_job_scoring_background(job_id: int, user_id: str):
    """
    Background task to trigger job scoring
    """
    try:
        logger.info(f"Triggering background job scoring for job {job_id} and user {user_id}")
        result = smart_job_scorer.trigger_scoring_for_new_job(job_id)
        logger.info(f"Background scoring triggered: {result}")
    except Exception as e:
        logger.error(f"Background scoring failed: {e}")

@router.post("/test-extraction")
async def test_extraction_endpoint():
    """
    Test endpoint to verify extraction service is working
    """
    try:
        # Test with a known job posting URL
        test_url = "https://stackoverflow.com/jobs/companies/acme-corp"
        
        result = await url_job_extractor.extract_job_details(test_url)
        
        return {
            "success": True,
            "test_url": test_url,
            "extraction_result": result,
            "message": "Extraction service is working"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Extraction service test failed"
        } 