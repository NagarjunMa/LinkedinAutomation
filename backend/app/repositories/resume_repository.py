"""Persistence operations for resume documents, versions, and evaluations."""

from sqlalchemy.orm import Session

from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.resume_evaluation_v2 import ResumeEvaluationV2
from app.services.resume.upload_workflow import STORAGE_READY


class ResumeRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_owned(self, resume_document_id: str, user_id: str) -> ResumeDocument | None:
        row = self.session.get(ResumeDocument, resume_document_id)
        return row if row and row.user_id == user_id else None

    def get_owned_ready(self, resume_document_id: str, user_id: str) -> ResumeDocument | None:
        row = self.get_owned(resume_document_id, user_id)
        return row if row and row.storage_status == STORAGE_READY else None

    def list_ready(self, user_id: str) -> list[ResumeDocument]:
        return (
            self.session.query(ResumeDocument)
            .filter(
                ResumeDocument.user_id == user_id,
                ResumeDocument.storage_status == STORAGE_READY,
            )
            .order_by(ResumeDocument.created_at.desc())
            .all()
        )

    def latest_evaluations(
        self,
        user_id: str,
        resume_document_ids: list[str],
    ) -> dict[str, ResumeEvaluationV2]:
        if not resume_document_ids:
            return {}
        rows = (
            self.session.query(ResumeEvaluationV2)
            .filter(
                ResumeEvaluationV2.user_id == user_id,
                ResumeEvaluationV2.resume_document_id.in_(resume_document_ids),
            )
            .order_by(ResumeEvaluationV2.created_at.desc())
            .all()
        )
        latest: dict[str, ResumeEvaluationV2] = {}
        for row in rows:
            latest.setdefault(row.resume_document_id, row)
        return latest

    def latest_evaluation(
        self,
        resume_document_id: str,
        user_id: str,
    ) -> ResumeEvaluationV2 | None:
        return (
            self.session.query(ResumeEvaluationV2)
            .filter(
                ResumeEvaluationV2.user_id == user_id,
                ResumeEvaluationV2.resume_document_id == resume_document_id,
            )
            .order_by(ResumeEvaluationV2.created_at.desc())
            .first()
        )

    def get_version(self, version_id: str) -> ResumeVersion | None:
        return self.session.get(ResumeVersion, version_id)

    def get_owned_version(
        self,
        version_id: str,
        user_id: str,
    ) -> tuple[ResumeVersion, ResumeDocument] | None:
        version = self.get_version(version_id)
        if not version:
            return None
        document = self.get_owned_ready(version.resume_document_id, user_id)
        return (version, document) if document else None

    def list_owned_tailored(
        self,
        user_id: str,
    ) -> list[tuple[ResumeVersion, ResumeDocument]]:
        return (
            self.session.query(ResumeVersion, ResumeDocument)
            .join(ResumeDocument, ResumeVersion.resume_document_id == ResumeDocument.id)
            .filter(
                ResumeDocument.user_id == user_id,
                ResumeDocument.storage_status == STORAGE_READY,
                ResumeVersion.jd_evaluation_id.isnot(None),
            )
            .order_by(ResumeVersion.created_at.desc())
            .all()
        )

    def add_evaluation(self, evaluation: ResumeEvaluationV2) -> None:
        self.session.add(evaluation)

    def add_version(self, version: ResumeVersion) -> None:
        self.session.add(version)
