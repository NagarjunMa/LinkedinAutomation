"""Queries scoped to the verified owner, even on a database role that bypasses RLS."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.interview import InterviewMessageRow as Message, InterviewSessionRow as Interview


class InterviewRepository:
    def __init__(self, session: Session, owner: str):
        self.db = session
        self.owner = owner

    def _active_retention(self):
        return or_(Interview.retention_expires_at.is_(None),
                   Interview.retention_expires_at > func.statement_timestamp())

    def sessions(self):
        return select(Interview).where(
            Interview.user_id == self.owner,
            self._active_retention(),
        ).execution_options(populate_existing=True)

    def get(self, session_id: str, *, lock: bool = False):
        query = self.sessions().where(Interview.id == session_id)
        if not lock:
            return self.db.scalar(query)
        row = self.db.scalar(query.with_for_update())
        # A blocking lock can outlive the eligibility timestamp in the SELECT.
        if row is not None and row.retention_expires_at is not None:
            if row.retention_expires_at <= self.db.scalar(select(func.clock_timestamp())):
                return None
        return row

    def messages(self, session_id: str):
        return select(Message).join(Interview, (Interview.user_id == Message.user_id) & (
            Interview.id == Message.session_id
        )).where(Message.user_id == self.owner, Message.session_id == session_id, self._active_retention())

    def get_retry(self, session_id: str, role: str, key: str):
        # The caller already holds the live session lock. Use that eligibility
        # decision consistently for this write and its idempotency lookup.
        return self.db.scalar(select(Message).where(
            Message.user_id == self.owner, Message.session_id == session_id,
            Message.role == role, Message.key == key,
        ))

    def get_message_at(self, session_id: str, position: int):
        return self.db.get(Message, (self.owner, session_id, position))
