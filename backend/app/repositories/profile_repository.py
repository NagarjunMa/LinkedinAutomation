"""Persistence operations for user-owned profiles and settings."""

from sqlalchemy.orm import Session

from app.models import JobApplication, ProfileChangeHistory, UserSettings
from app.models.job import UserProfile
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.resume_evaluation_v2 import ResumeEvaluationV2
from app.services.resume.upload_workflow import STORAGE_READY


class ProfileRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_profile(self, user_id: str) -> UserProfile | None:
        return (
            self.session.query(UserProfile)
            .filter(UserProfile.user_id == user_id)
            .first()
        )

    def latest_ready_resume(self, user_id: str) -> ResumeDocument | None:
        return (
            self.session.query(ResumeDocument)
            .filter(
                ResumeDocument.user_id == user_id,
                ResumeDocument.storage_status == STORAGE_READY,
            )
            .order_by(ResumeDocument.created_at.desc())
            .first()
        )

    def profile_stats(self, user_id: str) -> dict[str, int]:
        total_applications = (
            self.session.query(JobApplication)
            .filter(JobApplication.user_id == user_id)
            .count()
        )
        ready_resumes = self.session.query(ResumeDocument).filter(
            ResumeDocument.user_id == user_id,
            ResumeDocument.storage_status == STORAGE_READY,
        )
        total_resumes = ready_resumes.count()
        total_resume_versions = (
            self.session.query(ResumeVersion)
            .join(ResumeDocument, ResumeVersion.resume_document_id == ResumeDocument.id)
            .filter(
                ResumeDocument.user_id == user_id,
                ResumeDocument.storage_status == STORAGE_READY,
            )
            .count()
        )
        total_resume_evaluations = (
            self.session.query(ResumeEvaluationV2)
            .join(
                ResumeDocument,
                ResumeEvaluationV2.resume_document_id == ResumeDocument.id,
            )
            .filter(
                ResumeEvaluationV2.user_id == user_id,
                ResumeDocument.storage_status == STORAGE_READY,
            )
            .count()
        )
        return {
            "total_applications": total_applications,
            "total_resumes": total_resumes,
            "total_resume_versions": total_resume_versions,
            "total_resume_evaluations": total_resume_evaluations,
        }

    def get_settings(self, user_id: str) -> UserSettings | None:
        return (
            self.session.query(UserSettings)
            .filter(UserSettings.user_id == user_id)
            .first()
        )

    def change_history(
        self,
        user_id: str,
        *,
        limit: int,
    ) -> list[ProfileChangeHistory]:
        return (
            self.session.query(ProfileChangeHistory)
            .filter(ProfileChangeHistory.user_id == user_id)
            .order_by(ProfileChangeHistory.changed_at.desc())
            .limit(limit)
            .all()
        )

    def add(
        self,
        row: UserProfile | UserSettings | ProfileChangeHistory,
    ) -> None:
        self.session.add(row)
