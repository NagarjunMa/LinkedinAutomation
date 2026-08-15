"""Application orchestration for user-owned job tracking."""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.application.errors import (
    ApplicationError,
    AuthorizationError,
    InvalidOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.application.job_views import (
    application_response,
    is_applied,
    job_response,
    recent_application_response,
)
from app.models.job import JobApplication, JobListing
from app.repositories.job_repository import JobRepository
from app.schemas.job import (
    ApplicationStatus,
    JobApplicationStatusUpdate,
    JobListingCreate,
    JobListingResponse,
    JobListingUpdate,
    JobStats,
    PaginatedJobApplications,
    TimeRange,
)


logger = logging.getLogger(__name__)


class JobApplicationService:
    def __init__(self, session: Session):
        self.session = session
        self.jobs = JobRepository(session)

    def list_jobs(
        self,
        user_id: str,
        *,
        skip: int,
        limit: int,
        title: str | None,
        company: str | None,
        location: str | None,
        job_type: str | None,
        experience_level: str | None,
        sort_by: str,
        applied: bool | None,
    ) -> list[JobListingResponse]:
        rows = self.jobs.list_owned(
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
        return [job_response(job, application) for job, application in rows]

    def counts(
        self,
        user_id: str,
        *,
        title: str | None,
        company: str | None,
        location: str | None,
        job_type: str | None,
        experience_level: str | None,
    ) -> dict[str, int]:
        counts = self.jobs.count_owned_by_status(
            user_id,
            title=title,
            company=company,
            location=location,
            job_type=job_type,
            experience_level=experience_level,
        )
        total = counts["total"]
        applied = counts["applied"]
        return {
            "total": total,
            "applied": applied,
            "pending": total - applied,
            "total_jobs": total,
            "applied_count": applied,
            "pending_count": total - applied,
            "want_to_apply_count": counts.get("want_to_apply", 0),
            "maybe_later_count": counts.get("maybe_later", 0),
            "not_interested_count": counts.get("not_interested", 0),
        }

    def stats(
        self,
        user_id: str,
        *,
        time_range: TimeRange,
        custom_days: int | None,
    ) -> JobStats:
        rows = self.jobs.all_owned(user_id)
        total_jobs = len(rows)
        total_applied = sum(is_applied(application) for _, application in rows)
        days = custom_days or {
            TimeRange.LAST_7_DAYS: 7,
            TimeRange.LAST_30_DAYS: 30,
            TimeRange.LAST_3_MONTHS: 90,
        }[time_range]
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        daily: dict[str, dict[str, int]] = {}
        period_jobs = 0
        period_applied = 0
        for job, application in rows:
            extracted_at = _as_utc(job.extracted_date)
            if not extracted_at or not start <= extracted_at <= end:
                continue
            period_jobs += 1
            applied = is_applied(application)
            period_applied += int(applied)
            day = extracted_at.date().isoformat()
            bucket = daily.setdefault(day, {"jobs_extracted": 0, "jobs_applied": 0})
            bucket["jobs_extracted"] += 1
            bucket["jobs_applied"] += int(applied)
        return JobStats(
            total_jobs=total_jobs,
            total_applied=total_applied,
            success_rate=round(total_applied / total_jobs * 100, 2) if total_jobs else 0,
            period_jobs=period_jobs,
            period_applied=period_applied,
            daily_stats=[{"date": day, **daily[day]} for day in sorted(daily)],
            time_range=f"last_{days}_days" if custom_days else time_range.value,
        )

    def recent(self, user_id: str, limit: int) -> list[dict[str, Any]]:
        return [
            recent_application_response(job, application)
            for job, application in self.jobs.recent(user_id, limit)
        ]

    def create(self, user_id: str, request: JobListingCreate) -> JobListingResponse:
        job = JobListing(**request.model_dump())
        self.jobs.add(job)
        try:
            self.session.flush()
            application = JobApplication(
                user_id=user_id,
                job_id=job.id,
                application_status="applied" if request.applied else "interested",
                application_source="manual",
                source_url=job.source_url,
            )
            self.jobs.add(application)
            self._commit("create job")
            self.session.refresh(job)
            self.session.refresh(application)
        except ApplicationError:
            raise
        except Exception as exc:
            self._rollback_failure("create job", exc)
        return job_response(job, application)

    def get(self, job_id: int, user_id: str) -> JobListingResponse:
        job, application = self._owned_job(job_id, user_id)
        return job_response(job, application)

    def update(
        self,
        job_id: int,
        user_id: str,
        request: JobListingUpdate,
    ) -> JobListingResponse:
        job, application = self._owned_job(job_id, user_id)
        if self.jobs.other_owner_count(job_id, user_id):
            raise ResourceConflictError("Shared job details cannot be edited")
        values = request.model_dump(exclude_unset=True)
        applied = values.pop("applied", None)
        for field, value in values.items():
            setattr(job, field, value)
        if applied is not None:
            self._set_applied(application, applied)
        self._commit("update job")
        self.session.refresh(job)
        self.session.refresh(application)
        return job_response(job, application)

    def delete(self, job_id: int, user_id: str) -> dict[str, str]:
        job, _ = self._owned_job(job_id, user_id)
        has_other_owners = self.jobs.other_owner_count(job_id, user_id) > 0
        self.jobs.remove_owned_associations(job_id, user_id)
        if not has_other_owners:
            self.session.delete(job)
        self._commit("delete tracked job")
        return {"message": "Job deleted successfully"}

    def set_applied(self, job_id: int, user_id: str, applied: bool) -> JobListingResponse:
        job, application = self._owned_job(job_id, user_id)
        self._set_applied(application, applied)
        self._commit("update applied status")
        self.session.refresh(application)
        return job_response(job, application)

    def set_application_status(
        self,
        job_id: int,
        user_id: str,
        request: JobApplicationStatusUpdate,
    ) -> dict[str, Any]:
        _, application = self._owned_job(job_id, user_id)
        now = datetime.now(timezone.utc)
        application.application_status = request.status.value
        application.user_notes = request.notes
        application.updated_at = now
        metadata = dict(application.extraction_metadata or {})
        metadata.update({"status_update_method": "modal", "updated_at": now.isoformat()})
        if request.context is not None:
            metadata["application_context"] = request.context
        application.extraction_metadata = metadata
        if is_applied(application):
            application.application_date = request.date or now
        self._commit("update application status")
        self.session.refresh(application)
        return {
            "success": True,
            "message": f"Job application status updated to {application.application_status}",
            "job_id": job_id,
            "application_id": application.id,
            "status": application.application_status,
            "updated_at": application.updated_at.isoformat() if application.updated_at else None,
        }

    def apply(
        self,
        job_id: int,
        *,
        submitted_user_id: str,
        current_user_id: str,
        application_source: str,
        notes: str,
    ) -> dict[str, Any]:
        if submitted_user_id != current_user_id:
            raise AuthorizationError("User mismatch")
        _, application = self._owned_job(job_id, current_user_id)
        if application.application_status == "applied":
            return {"message": "Already applied to this job", "application_id": application.id}
        application.application_status = "applied"
        application.application_date = datetime.now(timezone.utc)
        application.application_source = application_source
        application.user_notes = notes
        application.updated_at = datetime.now(timezone.utc)
        self._commit("track application")
        self.session.refresh(application)
        return {
            "message": "Application tracked successfully",
            "application_id": application.id,
            "status": "applied",
        }

    def list_applications(
        self,
        user_id: str,
        *,
        status: ApplicationStatus | None,
        page: int,
        limit: int,
    ) -> PaginatedJobApplications:
        applications, total = self.jobs.applications(
            user_id,
            status=status.value if status else None,
            page=page,
            limit=limit,
        )
        return PaginatedJobApplications(
            applications=[application_response(row) for row in applications],
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit,
        )

    def update_application(
        self,
        application_id: int,
        user_id: str,
        *,
        status: ApplicationStatus,
        notes: str,
        follow_up_date: str,
    ) -> dict[str, Any]:
        application = self.jobs.get_owned_application(application_id, user_id)
        if not application:
            raise ResourceNotFoundError("Application not found")
        normalized_status = status.value
        parsed_follow_up = None
        if follow_up_date:
            try:
                parsed_follow_up = date.fromisoformat(follow_up_date)
            except ValueError as exc:
                raise InvalidOperationError("follow_up_date must use YYYY-MM-DD") from exc
        application.application_status = normalized_status
        application.updated_at = datetime.now(timezone.utc)
        if notes:
            application.user_notes = notes
        if parsed_follow_up:
            application.follow_up_date = parsed_follow_up
        if normalized_status in {"interview_scheduled", "interviewed", "rejected", "hired"}:
            application.company_response = True
            application.response_date = application.response_date or datetime.now(timezone.utc)
        self._commit("update tracked application")
        return {
            "message": "Application status updated",
            "application_id": application.id,
            "new_status": normalized_status,
        }

    def _owned_job(self, job_id: int, user_id: str) -> tuple[JobListing, JobApplication]:
        owned = self.jobs.get_owned(job_id, user_id)
        if not owned:
            raise ResourceNotFoundError("Job not found")
        return owned

    def _commit(self, operation: str) -> None:
        try:
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            logger.error(
                "Job application operation failed: %s",
                type(exc).__name__,
                extra={"operation": operation},
            )
            raise ApplicationError("Unable to update job applications") from exc

    def _rollback_failure(self, operation: str, exc: Exception) -> None:
        self.session.rollback()
        logger.error(
            "Job application operation failed: %s",
            type(exc).__name__,
            extra={"operation": operation},
        )
        raise ApplicationError("Unable to update job applications") from exc

    @staticmethod
    def _set_applied(application: JobApplication, applied: bool) -> None:
        application.application_status = "applied" if applied else "interested"
        if applied:
            application.application_date = datetime.now(timezone.utc)
        application.updated_at = datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
