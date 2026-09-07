"""Durable, account-independent records for the PrismPro private preview."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base_class import Base


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"
    __table_args__ = (
        UniqueConstraint("normalized_email", name="uq_waitlist_entries_email"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    normalized_email = Column(String(254), nullable=False)
    career_stage = Column(String(40), nullable=True)
    target_role = Column(String(120), nullable=True)
    communication_challenge = Column(Text, nullable=True)
    consent_granted = Column(Boolean, nullable=False, default=True)
    consent_version = Column(String(32), nullable=False)
    consented_at = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(64), nullable=False, default="public_preview_landing")
    retention_expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
