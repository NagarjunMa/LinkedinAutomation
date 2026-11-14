"""Private interview session and ordered transcript rows."""
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import mapped_column

from app.db.base_class import Base


class InterviewSessionRow(Base):
    __tablename__ = "career_interview_sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["target_user_id", "target_id"], ["career_targets.user_id", "career_targets.id"],
            match="FULL", ondelete="SET NULL",
            name="fk_interview_owned_target",
        ),
        CheckConstraint("target_user_id = user_id", name="ck_interview_target_owner"),
        CheckConstraint("state_version > 0 AND message_count >= 0", name="ck_interview_session_version"),
        Index("ix_interview_session_target", "target_user_id", "target_id"),
    )

    user_id = mapped_column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    id = mapped_column(String(36), primary_key=True)
    target_user_id = mapped_column(String(100), nullable=True)
    target_id = mapped_column(String(36), nullable=True)
    candidate_stage = mapped_column(String(32), nullable=True)
    mode = mapped_column(String(32), nullable=False)
    status = mapped_column(String(16), nullable=False)
    chapter = mapped_column(String(128), nullable=False)
    state_version = mapped_column(Integer, nullable=False)
    prompt_version = mapped_column(String(128), nullable=False)
    turns_remaining = mapped_column(Integer, nullable=False)
    tokens_remaining = mapped_column(Integer, nullable=False)
    message_count = mapped_column(Integer, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    retention_expires_at = mapped_column(DateTime(timezone=True), nullable=True)


class InterviewMessageRow(Base):
    __tablename__ = "career_interview_messages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "session_id"], ["career_interview_sessions.user_id", "career_interview_sessions.id"],
            ondelete="CASCADE", name="fk_interview_message_session",
        ),
        UniqueConstraint("user_id", "session_id", "role", "key", name="uq_interview_message_retry"),
        CheckConstraint("position >= 1 AND octet_length(content_ciphertext) BETWEEN 100 AND 22000", name="ck_interview_message_bounds"),
    )

    user_id = mapped_column(String(100), primary_key=True)
    session_id = mapped_column(String(36), primary_key=True)
    position = mapped_column(Integer, primary_key=True)
    key = mapped_column(String(128), nullable=False)
    role = mapped_column(String(16), nullable=False)
    content_ciphertext = mapped_column(Text, nullable=False)
    processing_status = mapped_column(String(16), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
