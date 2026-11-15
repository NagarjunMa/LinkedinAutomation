"""Career generation metadata mapped to the Alembic-owned PostgreSQL schema."""

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column

from app.db.base_class import Base


class CareerRunRow(Base):
    __tablename__ = "career_interview_runs"

    user_id = mapped_column(String(100), primary_key=True)
    id = mapped_column(String(36), primary_key=True)
    session_id = mapped_column(String(36))
    ciphertext = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class GeneratedArtifactRow(Base):
    __tablename__ = "career_generated_artifacts"

    user_id = mapped_column(String(100), primary_key=True)
    id = mapped_column(String(36), primary_key=True)
    version = mapped_column(Integer, primary_key=True)
    kind = mapped_column(String(32), nullable=False)
    target_id = mapped_column(String(36))
    requires_run = mapped_column(Boolean, nullable=False)
    generator = mapped_column(JSONB, nullable=False)
    link_count = mapped_column(Integer, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ArtifactRunRow(Base):
    __tablename__ = "career_artifact_runs"

    user_id = mapped_column(String(100), primary_key=True)
    artifact_id = mapped_column(String(36), primary_key=True)
    artifact_version = mapped_column(Integer, primary_key=True)
    run_id = mapped_column(String(36), nullable=False)


class ArtifactClaimRow(Base):
    __tablename__ = "career_artifact_claims"

    user_id = mapped_column(String(100), primary_key=True)
    artifact_id = mapped_column(String(36), primary_key=True)
    artifact_version = mapped_column(Integer, primary_key=True)
    claim_id = mapped_column(String(128), primary_key=True)
    evidence_id = mapped_column(String(36), primary_key=True)
    evidence_revision = mapped_column(Integer, nullable=False)


class ProofArtifactRow(Base):
    __tablename__ = "career_proof_artifacts"

    user_id = mapped_column(String(100), primary_key=True)
    id = mapped_column(String(36), primary_key=True)
    source_id = mapped_column(String(36), nullable=False)
    source_version = mapped_column(Integer, nullable=False)
    evidence_id = mapped_column(String(36), nullable=False)
    evidence_revision = mapped_column(Integer, nullable=False)
    attributes = mapped_column("metadata", JSONB, nullable=False)
