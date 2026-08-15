"""Persistence operations for resume export audit records."""

from sqlalchemy.orm import Session

from app.models.resume_export import ResumeExport


class ResumeExportRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_owned_succeeded(self, export_id: str, user_id: str) -> ResumeExport | None:
        row = self.session.get(ResumeExport, export_id)
        if not row or row.user_id != user_id or row.status != "succeeded":
            return None
        return row

    def add(self, export: ResumeExport) -> None:
        self.session.add(export)
