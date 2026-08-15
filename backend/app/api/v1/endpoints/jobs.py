"""HTTP adapters for authenticated job application tracking."""

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query

from app.api.dependencies import get_job_application_service
from app.api.error_mapping import to_http_exception
from app.application.errors import ApplicationError
from app.application.job_service import JobApplicationService
from app.core.auth import get_authenticated_user_id
from app.schemas.job import (
    ApplicationStatus,
    JobAppliedUpdate,
    JobApplicationStatusUpdate,
    JobListingCreate,
    JobListingResponse,
    JobListingUpdate,
    JobStats,
    PaginatedJobApplications,
    TimeRange,
)


router = APIRouter()
_LEGACY_SCRAPE_DETAIL = "This legacy scrape endpoint is no longer supported"
_LEGACY_CLEANUP_DETAIL = "This legacy cleanup endpoint is no longer supported"


@router.get("/", response_model=list[JobListingResponse])
def get_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    title: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    sort_by: str = "newest",
    applied: Optional[bool] = None,
    user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    return service.list_jobs(
        user_id,
        skip=skip,
        limit=limit,
        title=title,
        company=company,
        location=location,
        job_type=job_type,
        experience_level=experience_level,
        sort_by=sort_by,
        applied=applied,
    )


@router.get("/counts")
def get_job_counts(
    title: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    return service.counts(
        user_id,
        title=title,
        company=company,
        location=location,
        job_type=job_type,
        experience_level=experience_level,
    )


@router.get("/stats", response_model=JobStats)
def get_job_stats(
    time_range: TimeRange = Query(default=TimeRange.LAST_30_DAYS),
    custom_days: Optional[int] = Query(default=None, ge=1, le=365),
    user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    return service.stats(user_id, time_range=time_range, custom_days=custom_days)


@router.get("/recent-applications")
def get_recent_applications(
    limit: int = Query(default=5, ge=1, le=50),
    user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    return service.recent(user_id, limit)


@router.post("/", response_model=JobListingResponse)
def create_job(
    job: JobListingCreate,
    user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    try:
        return service.create(user_id, job)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.post("/scrape", include_in_schema=False)
def scrape_jobs(_query: dict):
    raise HTTPException(status_code=410, detail=_LEGACY_SCRAPE_DETAIL)


@router.post("/applications/{job_id}/apply")
def apply_to_job(
    job_id: int,
    user_id: str = Form(..., max_length=100),
    application_source: str = Form("direct", max_length=100),
    notes: str = Form("", max_length=5000),
    current_user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    try:
        return service.apply(
            job_id,
            submitted_user_id=user_id,
            current_user_id=current_user_id,
            application_source=application_source,
            notes=notes,
        )
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.get("/applications/{user_id}", response_model=PaginatedJobApplications)
def get_user_applications(
    user_id: str,
    status: Optional[ApplicationStatus] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    return service.list_applications(
        current_user_id,
        status=status,
        page=page,
        limit=limit,
    )


@router.put("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    status: ApplicationStatus = Form(...),
    notes: str = Form("", max_length=5000),
    follow_up_date: str = Form("", max_length=10),
    user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    try:
        return service.update_application(
            application_id,
            user_id,
            status=status,
            notes=notes,
            follow_up_date=follow_up_date,
        )
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.get("/cleanup/stats", include_in_schema=False)
def get_cleanup_stats(
    days_old: int = Query(default=20, ge=1, le=365),
):
    del days_old
    raise HTTPException(status_code=410, detail=_LEGACY_CLEANUP_DETAIL)


@router.post("/cleanup/execute", include_in_schema=False)
def execute_cleanup(
    days_old: int = Query(default=20, ge=1, le=365),
):
    del days_old
    raise HTTPException(status_code=410, detail=_LEGACY_CLEANUP_DETAIL)


@router.post("/cleanup/execute-all", include_in_schema=False)
def execute_cleanup_all(
    days_old: int = Query(default=20, ge=1, le=365),
):
    del days_old
    raise HTTPException(status_code=410, detail=_LEGACY_CLEANUP_DETAIL)


@router.get("/{job_id}", response_model=JobListingResponse)
def get_job(
    job_id: int,
    user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    try:
        return service.get(job_id, user_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.put("/{job_id}", response_model=JobListingResponse)
def update_job(
    job_id: int,
    job_update: JobListingUpdate,
    user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    try:
        return service.update(job_id, user_id, job_update)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    try:
        return service.delete(job_id, user_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.put("/{job_id}/status", response_model=JobListingResponse)
def update_job_status(
    job_id: int,
    status_update: JobAppliedUpdate,
    user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    try:
        return service.set_applied(job_id, user_id, status_update.applied)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.put("/{job_id}/application-status")
def update_job_application_status(
    job_id: int,
    status_update: JobApplicationStatusUpdate,
    user_id: str = Depends(get_authenticated_user_id),
    service: JobApplicationService = Depends(get_job_application_service),
):
    try:
        return service.set_application_status(job_id, user_id, status_update)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc
