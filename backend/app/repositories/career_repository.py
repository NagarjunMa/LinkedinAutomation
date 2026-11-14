"""Owner-scoped queries for the Career Evidence persistence service."""
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, undefer

from app.models.career import CareerSourceRow, CareerTargetRow
from app.models.resume_document import ResumeDocument
from app.models.user import User
from app.schemas.career.common import SourceRef
from app.services.resume.upload_workflow import STORAGE_READY


class CareerRepository:
    def __init__(self, session: Session, user_id: str):
        self.session = session
        self.user_id = user_id

    def lock_owner_for_insert(self) -> bool:
        # Account deletion locks the user before cascading to dependent rows.
        owner = select(User.user_id).where(User.user_id == self.user_id)
        return self.session.scalar(owner.with_for_update(read=True, key_share=True)) is not None

    def _sources(self):
        return select(CareerSourceRow).where(CareerSourceRow.user_id == self.user_id)

    def _visible_sources(self):
        ready_resume = select(ResumeDocument.id).where(
            ResumeDocument.user_id == self.user_id,
            ResumeDocument.id == CareerSourceRow.resume_document_id,
            ResumeDocument.storage_status == STORAGE_READY,
        ).exists()
        return self._sources().where(
            or_(CareerSourceRow.retention_expires_at.is_(None),
                CareerSourceRow.retention_expires_at > func.statement_timestamp()),
            or_(CareerSourceRow.resume_document_id.is_(None), ready_resume),
        )

    def get_source(self, source: SourceRef, *, lock=False, include_content=False):
        query = self._visible_sources().where(
            CareerSourceRow.id == source.source_id, CareerSourceRow.version == source.source_version,
        )
        if include_content:
            query = query.options(undefer(CareerSourceRow.content))
        return self.session.scalar(query.with_for_update(read=True) if lock else query)

    def list_sources(self, offset: int, limit: int):
        return self.session.scalars(self._visible_sources().order_by(
            CareerSourceRow.id, CareerSourceRow.version.desc(),
        ).offset(offset).limit(limit))

    def lock_source_history(self, source_id: str):
        # All appends and deletes lock revision 1 before inspecting the series.
        return self.session.scalar(self._sources().where(
            CareerSourceRow.id == source_id, CareerSourceRow.version == 1,
        ).with_for_update())

    def latest_source(self, source_id: str):
        return self.session.scalar(self._sources().where(CareerSourceRow.id == source_id)
                                   .order_by(CareerSourceRow.version.desc()).limit(1))

    def delete_source_history(self, source_id: str):
        self.session.execute(delete(CareerSourceRow).where(
            CareerSourceRow.user_id == self.user_id, CareerSourceRow.id == source_id,
        ))

    def ready_resume(self, document_id: str):
        return self.session.scalar(select(ResumeDocument).where(
            ResumeDocument.user_id == self.user_id,
            ResumeDocument.id == document_id,
            ResumeDocument.storage_status == STORAGE_READY,
        ).with_for_update(read=True))

    def _targets(self):
        return select(CareerTargetRow).where(CareerTargetRow.user_id == self.user_id)

    def get_target(self, target_id: str, *, lock=False):
        query = self._targets().where(CareerTargetRow.id == target_id).execution_options(populate_existing=True)
        return self.session.scalar(query.with_for_update() if lock else query)

    def list_targets(self, offset: int, limit: int):
        return self.session.scalars(self._targets().order_by(CareerTargetRow.id)
                                    .offset(offset).limit(limit).execution_options(populate_existing=True))
