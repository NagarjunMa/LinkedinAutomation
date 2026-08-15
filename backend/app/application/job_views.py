"""Stable API projections for job application records."""

from typing import Any

from app.models.job import JobApplication, JobListing
from app.schemas.job import APPLIED_APPLICATION_STATUSES, JobListingResponse


def is_applied(application: JobApplication) -> bool:
    return application.application_status in APPLIED_APPLICATION_STATUSES


def job_response(job: JobListing, application: JobApplication) -> JobListingResponse:
    payload = {column.name: getattr(job, column.name) for column in JobListing.__table__.columns}
    payload.update(
        applied=is_applied(application),
        applied_date=application.application_date if is_applied(application) else None,
        application_status=application.application_status,
        application_notes=application.user_notes,
        application_context=(application.extraction_metadata or {}).get("application_context"),
    )
    return JobListingResponse.model_validate(payload)


def recent_application_response(
    job: JobListing,
    application: JobApplication,
) -> dict[str, Any]:
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location or "Remote",
        "applied_date": application.application_date.isoformat()
        if application.application_date
        else None,
        "extracted_date": job.extracted_date.isoformat() if job.extracted_date else None,
        "status": (application.application_status or "applied").title(),
        "source_url": job.source_url,
        "application_source": application.application_source,
    }


def application_response(application: JobApplication) -> dict[str, Any]:
    job = application.job_listing
    return {
        "id": application.id,
        "user_id": application.user_id,
        "job_id": application.job_id,
        "application_status": application.application_status or "pending",
        "application_source": application.application_source,
        "application_date": application.application_date,
        "source_url": application.source_url,
        "user_notes": application.user_notes,
        "extraction_metadata": application.extraction_metadata
        or {"extraction_confidence": 0.9, "extraction_method": job.source or "dashboard"},
        "follow_up_date": application.follow_up_date,
        "company_response": bool(application.company_response),
        "response_date": application.response_date,
        "job_listing": job_response(job, application),
    }
