"""
Educational Information API Endpoints

Endpoints for managing comprehensive educational information including
education records, certifications, online courses, and academic projects.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.education import (
    EducationRecordCreate,
    EducationRecordUpdate,
    EducationRecordResponse,
    CertificationCreate,
    CertificationResponse,
    OnlineCourseCreate,
    OnlineCourseResponse,
    AcademicProjectCreate,
    AcademicProjectResponse,
    EducationalProfileResponse,
    EducationJobMatchAnalysis
)
from app.services.education_service import EducationService
from app.core.enhanced_logging import log_business_event
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{user_id}/education-records", response_model=EducationRecordResponse)
def create_education_record(
    user_id: str,
    education_data: EducationRecordCreate,
    db: Session = Depends(get_db)
) -> EducationRecordResponse:
    """
    Create a new education record for a user.

    This endpoint allows users to add detailed educational information
    including degrees, institutions, academic performance, and skills gained.
    """
    try:
        education_service = EducationService(db)
        education_record = education_service.create_education_record(user_id, education_data)

        # Log business event
        log_business_event(
            "education_record_created",
            user_id,
            {
                "institution": education_data.institution_name,
                "degree_type": education_data.degree_type,
                "field_of_study": education_data.field_of_study
            }
        )

        return education_record

    except Exception as e:
        logger.error(f"Failed to create education record for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/education-records", response_model=List[EducationRecordResponse])
def get_education_records(
    user_id: str,
    db: Session = Depends(get_db),
    is_current: Optional[bool] = Query(None, description="Filter by current enrollment status"),
    degree_type: Optional[str] = Query(None, description="Filter by degree type"),
    field_of_study: Optional[str] = Query(None, description="Filter by field of study")
) -> List[EducationRecordResponse]:
    """
    Get all education records for a user with optional filtering.
    """
    try:
        education_service = EducationService(db)
        records = education_service.get_education_records(
            user_id,
            is_current=is_current,
            degree_type=degree_type,
            field_of_study=field_of_study
        )
        return records

    except Exception as e:
        logger.error(f"Failed to get education records for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/education-records/{record_id}", response_model=EducationRecordResponse)
def get_education_record(
    user_id: str,
    record_id: str,
    db: Session = Depends(get_db)
) -> EducationRecordResponse:
    """
    Get a specific education record by ID.
    """
    try:
        education_service = EducationService(db)
        record = education_service.get_education_record_by_id(user_id, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Education record not found")
        return record

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get education record {record_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}/education-records/{record_id}", response_model=EducationRecordResponse)
def update_education_record(
    user_id: str,
    record_id: str,
    education_data: EducationRecordUpdate,
    db: Session = Depends(get_db)
) -> EducationRecordResponse:
    """
    Update an existing education record.
    """
    try:
        education_service = EducationService(db)
        record = education_service.update_education_record(user_id, record_id, education_data)
        if not record:
            raise HTTPException(status_code=404, detail="Education record not found")

        log_business_event(
            "education_record_updated",
            user_id,
            {"record_id": record_id}
        )

        return record

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update education record {record_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}/education-records/{record_id}")
def delete_education_record(
    user_id: str,
    record_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Delete an education record.
    """
    try:
        education_service = EducationService(db)
        success = education_service.delete_education_record(user_id, record_id)
        if not success:
            raise HTTPException(status_code=404, detail="Education record not found")

        log_business_event(
            "education_record_deleted",
            user_id,
            {"record_id": record_id}
        )

        return {"message": "Education record deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete education record {record_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Certifications endpoints
@router.post("/{user_id}/certifications", response_model=CertificationResponse)
def create_certification(
    user_id: str,
    cert_data: CertificationCreate,
    db: Session = Depends(get_db)
) -> CertificationResponse:
    """
    Create a new certification record.
    """
    try:
        education_service = EducationService(db)
        certification = education_service.create_certification(user_id, cert_data)

        log_business_event(
            "certification_created",
            user_id,
            {
                "certification_name": cert_data.name,
                "issuing_org": cert_data.issuing_organization
            }
        )

        return certification

    except Exception as e:
        logger.error(f"Failed to create certification for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/certifications", response_model=List[CertificationResponse])
def get_certifications(
    user_id: str,
    db: Session = Depends(get_db),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    certification_type: Optional[str] = Query(None, description="Filter by certification type")
) -> List[CertificationResponse]:
    """
    Get all certifications for a user.
    """
    try:
        education_service = EducationService(db)
        certifications = education_service.get_certifications(
            user_id,
            is_active=is_active,
            certification_type=certification_type
        )
        return certifications

    except Exception as e:
        logger.error(f"Failed to get certifications for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Online Courses endpoints
@router.post("/{user_id}/online-courses", response_model=OnlineCourseResponse)
def create_online_course(
    user_id: str,
    course_data: OnlineCourseCreate,
    db: Session = Depends(get_db)
) -> OnlineCourseResponse:
    """
    Create a new online course record.
    """
    try:
        education_service = EducationService(db)
        course = education_service.create_online_course(user_id, course_data)

        log_business_event(
            "online_course_created",
            user_id,
            {
                "course_name": course_data.course_name,
                "provider": course_data.provider
            }
        )

        return course

    except Exception as e:
        logger.error(f"Failed to create online course for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/online-courses", response_model=List[OnlineCourseResponse])
def get_online_courses(
    user_id: str,
    db: Session = Depends(get_db),
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    provider: Optional[str] = Query(None, description="Filter by provider")
) -> List[OnlineCourseResponse]:
    """
    Get all online courses for a user.
    """
    try:
        education_service = EducationService(db)
        courses = education_service.get_online_courses(
            user_id,
            is_completed=is_completed,
            provider=provider
        )
        return courses

    except Exception as e:
        logger.error(f"Failed to get online courses for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Academic Projects endpoints
@router.post("/{user_id}/academic-projects", response_model=AcademicProjectResponse)
def create_academic_project(
    user_id: str,
    project_data: AcademicProjectCreate,
    db: Session = Depends(get_db)
) -> AcademicProjectResponse:
    """
    Create a new academic project record.
    """
    try:
        education_service = EducationService(db)
        project = education_service.create_academic_project(user_id, project_data)

        log_business_event(
            "academic_project_created",
            user_id,
            {
                "project_name": project_data.project_name,
                "project_type": project_data.project_type
            }
        )

        return project

    except Exception as e:
        logger.error(f"Failed to create academic project for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/academic-projects", response_model=List[AcademicProjectResponse])
def get_academic_projects(
    user_id: str,
    db: Session = Depends(get_db),
    project_type: Optional[str] = Query(None, description="Filter by project type")
) -> List[AcademicProjectResponse]:
    """
    Get all academic projects for a user.
    """
    try:
        education_service = EducationService(db)
        projects = education_service.get_academic_projects(user_id, project_type=project_type)
        return projects

    except Exception as e:
        logger.error(f"Failed to get academic projects for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Comprehensive profile endpoints
@router.get("/{user_id}/educational-profile", response_model=EducationalProfileResponse)
def get_educational_profile(
    user_id: str,
    db: Session = Depends(get_db)
) -> EducationalProfileResponse:
    """
    Get complete educational profile for a user including all education records,
    certifications, courses, and projects with AI-calculated scores.
    """
    try:
        education_service = EducationService(db)
        profile = education_service.get_comprehensive_educational_profile(user_id)
        return profile

    except Exception as e:
        logger.error(f"Failed to get educational profile for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/analyze-job-match", response_model=EducationJobMatchAnalysis)
def analyze_education_job_match(
    user_id: str,
    job_title: str,
    job_description: str,
    job_requirements: str,
    db: Session = Depends(get_db)
) -> EducationJobMatchAnalysis:
    """
    Analyze how well user's educational background matches a specific job.

    This endpoint uses AI to evaluate education-job compatibility and provides
    detailed scoring, skill gap analysis, and recommendations.
    """
    try:
        education_service = EducationService(db)
        analysis = education_service.analyze_education_job_match(
            user_id,
            job_title,
            job_description,
            job_requirements
        )

        log_business_event(
            "education_job_match_analyzed",
            user_id,
            {
                "job_title": job_title,
                "match_score": analysis.education_match_score
            }
        )

        return analysis

    except Exception as e:
        logger.error(f"Failed to analyze education job match for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))