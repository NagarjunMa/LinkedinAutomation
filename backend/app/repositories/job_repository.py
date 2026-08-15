"""Persistence operations for user-owned job application tracking."""

from sqlalchemy import and_, func
from sqlalchemy.orm import Query, Session

from app.models.job import JobApplication, JobListing
from app.schemas.job import APPLIED_APPLICATION_STATUSES


class JobRepository:
    def __init__(self, session: Session):
        self.session = session

    def owned_pairs(self, user_id: str) -> Query:
        return (
            self.session.query(JobListing, JobApplication)
            .join(JobApplication, JobApplication.job_id == JobListing.id)
            .filter(JobApplication.user_id == user_id)
        )

    def list_owned(
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
    ) -> list[tuple[JobListing, JobApplication]]:
        query = self._filtered(
            self.owned_pairs(user_id),
            title=title,
            company=company,
            location=location,
            job_type=job_type,
            experience_level=experience_level,
        )
        applied_filter = JobApplication.application_status.in_(APPLIED_APPLICATION_STATUSES)
        if applied is not None:
            query = query.filter(applied_filter if applied else ~applied_filter)
        if sort_by == "oldest":
            query = query.order_by(JobListing.extracted_date.asc())
        elif sort_by == "posted_newest":
            query = query.order_by(JobListing.posted_date.desc().nullslast())
        elif sort_by == "posted_oldest":
            query = query.order_by(JobListing.posted_date.asc().nullslast())
        else:
            query = query.order_by(JobListing.extracted_date.desc())
        return query.offset(skip).limit(limit).all()

    def count_owned_by_status(
        self,
        user_id: str,
        *,
        title: str | None,
        company: str | None,
        location: str | None,
        job_type: str | None,
        experience_level: str | None,
    ) -> dict[str, int]:
        rows = self._filtered(
            self.owned_pairs(user_id),
            title=title,
            company=company,
            location=location,
            job_type=job_type,
            experience_level=experience_level,
        ).with_entities(
            JobApplication.application_status,
            func.count(JobApplication.id),
        ).group_by(JobApplication.application_status).all()
        counts = {status or "pending": count for status, count in rows}
        counts["total"] = sum(counts.values())
        counts["applied"] = sum(
            counts.get(status, 0) for status in APPLIED_APPLICATION_STATUSES
        )
        return counts

    def get_owned(self, job_id: int, user_id: str) -> tuple[JobListing, JobApplication] | None:
        return self.owned_pairs(user_id).filter(JobListing.id == job_id).first()

    def recent(self, user_id: str, limit: int) -> list[tuple[JobListing, JobApplication]]:
        return (
            self.owned_pairs(user_id)
            .order_by(JobApplication.application_date.desc())
            .limit(limit)
            .all()
        )

    def all_owned(self, user_id: str) -> list[tuple[JobListing, JobApplication]]:
        return self.owned_pairs(user_id).all()

    def applications(
        self,
        user_id: str,
        *,
        status: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[JobApplication], int]:
        query = self.session.query(JobApplication).filter(JobApplication.user_id == user_id)
        if status:
            query = query.filter(JobApplication.application_status == status)
        total = query.count()
        rows = (
            query.order_by(JobApplication.application_date.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return rows, total

    def get_owned_application(self, application_id: int, user_id: str) -> JobApplication | None:
        return (
            self.session.query(JobApplication)
            .filter(JobApplication.id == application_id, JobApplication.user_id == user_id)
            .first()
        )

    def other_owner_count(self, job_id: int, user_id: str) -> int:
        return (
            self.session.query(JobApplication.id)
            .filter(JobApplication.job_id == job_id, JobApplication.user_id != user_id)
            .count()
        )

    def remove_owned_associations(self, job_id: int, user_id: str) -> int:
        return (
            self.session.query(JobApplication)
            .filter(JobApplication.job_id == job_id, JobApplication.user_id == user_id)
            .delete(synchronize_session=False)
        )

    def add(self, row: JobListing | JobApplication) -> None:
        self.session.add(row)

    @staticmethod
    def _filtered(
        query: Query,
        *,
        title: str | None,
        company: str | None,
        location: str | None,
        job_type: str | None,
        experience_level: str | None,
    ) -> Query:
        conditions = []
        if title:
            conditions.append(JobListing.title.ilike(f"%{title}%"))
        if company:
            conditions.append(JobListing.company.ilike(f"%{company}%"))
        if location:
            conditions.append(JobListing.location.ilike(f"%{location}%"))
        if job_type:
            conditions.append(JobListing.job_type == job_type)
        if experience_level:
            conditions.append(JobListing.experience_level == experience_level)
        return query.filter(and_(*conditions)) if conditions else query
