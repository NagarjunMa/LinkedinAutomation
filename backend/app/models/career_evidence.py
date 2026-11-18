"""Immutable evidence revisions, source references and decisions."""
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import mapped_column

from app.db.base_class import Base


class EvidenceRow(Base):
    __tablename__ = "career_evidence_items"

    user_id = mapped_column(String(100), primary_key=True)
    evidence_id = mapped_column(String(36), primary_key=True)
    revision = mapped_column(Integer, primary_key=True)
    lifecycle = mapped_column(String(16), nullable=False)
    is_private = mapped_column(Boolean, nullable=False)
    source_count = mapped_column(Integer, nullable=False)
    ciphertext = mapped_column(Text, nullable=False)
    measurement_ciphertext = mapped_column(Text)


class EvidenceSourceRow(Base):
    __tablename__ = "career_evidence_sources"

    user_id = mapped_column(String(100), primary_key=True)
    evidence_id = mapped_column(String(36), primary_key=True)
    revision = mapped_column(Integer, primary_key=True)
    position = mapped_column(Integer, primary_key=True)
    source_id = mapped_column(String(36), nullable=False)
    source_version = mapped_column(Integer, nullable=False)


class EvidenceDecisionRow(Base):
    __tablename__ = "career_evidence_decisions"

    user_id = mapped_column(String(100), primary_key=True)
    evidence_id = mapped_column(String(36), primary_key=True)
    resulting_revision = mapped_column(Integer, primary_key=True)
    action = mapped_column(String(24), nullable=False)
    decided_at = mapped_column(DateTime(timezone=True), nullable=False)
    reason_ciphertext = mapped_column(Text)
