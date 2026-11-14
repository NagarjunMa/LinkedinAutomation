"""Persist and resume interviews without invoking a model."""
from datetime import datetime, timezone
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from app.application.errors import ExternalServiceError, InvalidOperationError, ResourceConflictError, ResourceNotFoundError
from app.core.config import settings
from app.models.interview import InterviewMessageRow as Message, InterviewSessionRow as Interview
from app.repositories.career_repository import CareerRepository
from app.repositories.interview_repository import InterviewRepository
from app.schemas.career.common import Timestamp
from app.schemas.career.interview_persistence import MessageInput, MessageRole, MessageView, SessionInput, SessionView


class InterviewService:
    def __init__(self, db: Session, owner: str):
        self.db = db
        self.owner = owner
        self.repo = InterviewRepository(db, owner)

    def create(self, data: SessionInput, *, retention_expires_at: Timestamp | None = None) -> SessionView:
        career = CareerRepository(self.db, self.owner)
        if not career.lock_owner_for_insert():
            raise ResourceNotFoundError("Account not found")
        if data.target_id:
            target = career.get_target(data.target_id, lock=True)
            if not target or target.status != "active":
                raise ResourceNotFoundError("Active target not found")
        now = datetime.now(timezone.utc)
        if retention_expires_at and retention_expires_at <= now:
            raise InvalidOperationError("Interview retention has already expired")
        row = Interview(
            user_id=self.owner, id=str(uuid4()), target_user_id=self.owner if data.target_id else None,
            **data.model_dump(), status="active",
            chapter="introduction", state_version=1, prompt_version="unassigned",
            turns_remaining=0, tokens_remaining=0, message_count=0,
            created_at=now, updated_at=now, retention_expires_at=retention_expires_at,
        )
        self.db.add(row)
        result = _state(row)
        self.db.commit()
        return result

    def list_sessions(self, *, offset: int = 0, limit: int = 50) -> list[SessionView]:
        _page(offset, limit)
        rows = self.db.scalars(self.repo.sessions().order_by(Interview.id).offset(offset).limit(limit))
        return [_state(row) for row in rows]

    def get(self, session_id: str) -> SessionView:
        return _state(self._owned(session_id))

    def resume(self, session_id: str) -> SessionView:
        row = self._owned(session_id, lock=True)
        if row.status not in ("active", "paused"):
            raise ResourceConflictError("Interview cannot be resumed")
        if row.status == "paused":
            row.status = "active"
            self._advance(row)
        result = _state(row)
        self.db.commit()
        return result

    def messages(self, session_id: str, *, offset: int = 0, limit: int = 50) -> list[MessageView]:
        _page(offset, limit)
        self._owned(session_id)
        rows = self.db.scalars(self.repo.messages(session_id).order_by(Message.position).offset(offset).limit(limit))
        messages = rows.all()
        if not messages:
            return []
        cipher = _transcript_cipher()
        return [_message_view(row, _read_transcript(cipher, row)) for row in messages]

    def append(self, session_id: str, data: MessageInput, *, role: MessageRole = "user") -> MessageView:
        # Follow the same owner-before-dependents lock order as account deletion.
        if not CareerRepository(self.db, self.owner).lock_owner_for_insert():
            raise ResourceNotFoundError("Interview not found")
        row = self._owned(session_id, lock=True)
        cipher = _transcript_cipher()
        previous = self.repo.get_retry(session_id, role, data.key)
        if previous:
            content = _read_transcript(cipher, previous)
            if content != data.content:
                raise ResourceConflictError("Message key was reused with different content")
            result = _message_view(previous, content)
            self.db.commit()
            return result
        if row.status != "active":
            raise ResourceConflictError("Interview is not active")
        if row.message_count:
            # Under the session lock, reject a misconfigured backend before adding mixed-key rows.
            last = self.repo.get_message_at(session_id, row.message_count)
            if last is None:
                raise ExternalServiceError("Interview transcript could not be opened")
            _read_transcript(cipher, last)
        row.message_count += 1
        self._advance(row)
        message = Message(
            user_id=self.owner, session_id=session_id, position=row.message_count, key=data.key,
            content_ciphertext=cipher.encrypt(data.content.encode("utf-8")).decode("ascii"),
            role=role, processing_status="pending" if role == "user" else "complete", created_at=row.updated_at,
        )
        result = _message_view(message, data.content)
        self.db.add(message)
        self.db.commit()
        return result

    def _owned(self, session_id: str, *, lock: bool = False) -> Interview:
        row = self.repo.get(session_id, lock=lock)
        if row is None:
            raise ResourceNotFoundError("Interview not found")
        return row

    @staticmethod
    def _advance(row: Interview) -> None:
        row.state_version += 1
        row.updated_at = datetime.now(timezone.utc)


def _transcript_cipher() -> Fernet:
    key = settings.CAREER_TRANSCRIPT_KEY
    if key:
        try:
            return Fernet(key.get_secret_value())
        except ValueError:
            pass
    raise ExternalServiceError("Interview transcript storage is unavailable")


def _read_transcript(cipher: Fernet, row: Message) -> str:
    try:
        return cipher.decrypt(row.content_ciphertext).decode("utf-8")
    except (InvalidToken, UnicodeError):
        raise ExternalServiceError("Interview transcript could not be opened") from None


def _message_view(row: Message, content: str) -> MessageView:
    return MessageView(
        key=row.key, content=content, position=row.position, role=row.role,
        processing_status=row.processing_status, created_at=row.created_at,
    )


def _page(offset: int, limit: int) -> None:
    if offset < 0 or not 1 <= limit <= 100:
        raise InvalidOperationError("Invalid page")


def _state(row: Interview) -> SessionView:
    return SessionView(
        schema_version=1, owner_id=row.user_id, session_id=row.id, target_id=row.target_id,
        candidate_stage=row.candidate_stage, mode=row.mode, status=row.status, chapter=row.chapter,
        state_version=row.state_version, prompt_version=row.prompt_version,
        turns_remaining=row.turns_remaining, tokens_remaining=row.tokens_remaining,
        created_at=row.created_at, updated_at=row.updated_at, retention_expires_at=row.retention_expires_at,
    )
