"""Career source snapshots and target lanes. PostgreSQL owns cross-row integrity."""
from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, Index, UniqueConstraint, func
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column

from app.db.base_class import Base


class CareerSourceRow(Base):
    __tablename__ = "career_sources"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "resume_document_id"],
            ["resume_documents.user_id", "resume_documents.id"],
            ondelete="CASCADE",
            name="fk_career_sources_owned_resume",
        ),
        UniqueConstraint("user_id", "id", "version", "kind", name="uq_career_sources_ref_kind"),
        CheckConstraint("version >= 1", name="ck_career_sources_positive_version"),
        CheckConstraint(
            "kind IN ('resume', 'linkedin_profile_pdf', 'candidate_introduction', "
            "'interview_message', 'public_proof_link', 'job_description')",
            name="ck_career_sources_kind",
        ),
        CheckConstraint("(kind = 'resume') = (resume_document_id IS NOT NULL)", name="ck_career_sources_resume"),
        CheckConstraint("length(content_sha256) = 64", name="ck_career_sources_hash"),
        CheckConstraint("char_length(content) <= 100000", name="ck_career_sources_content_length"),
        CheckConstraint("retention_expires_at > created_at", name="ck_career_sources_retention"),
        Index("ix_career_sources_owned_resume", "user_id", "resume_document_id"),
    )

    user_id = mapped_column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    id = mapped_column(String(36), primary_key=True)
    version = mapped_column(Integer, primary_key=True)
    kind = mapped_column(String(32), nullable=False)
    content = mapped_column(Text, nullable=False, deferred=True)
    content_sha256 = mapped_column(String(64), nullable=False)
    resume_document_id = mapped_column(String, nullable=True)
    extraction_version = mapped_column(String(128), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    retention_expires_at = mapped_column(DateTime(timezone=True), nullable=True)


class CareerTargetRow(Base):
    __tablename__ = "career_targets"
    __table_args__ = (
        ForeignKeyConstraint(
            ["jd_user_id", "jd_source_id", "jd_source_version", "jd_source_kind"],
            ["career_sources.user_id", "career_sources.id", "career_sources.version", "career_sources.kind"],
            match="FULL",
            ondelete="SET NULL",
            name="fk_career_targets_owned_jd",
        ),
        CheckConstraint("jd_user_id = user_id AND jd_source_kind = 'job_description'", name="ck_career_targets_jd_owner"),
        CheckConstraint("status IN ('active', 'archived')", name="ck_career_targets_status"),
        Index("ix_career_targets_jd", "jd_user_id", "jd_source_id", "jd_source_version"),
    )

    user_id = mapped_column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    id = mapped_column(String(36), primary_key=True)
    role_family = mapped_column(String(200), nullable=False)
    seniority = mapped_column(String(200), nullable=False)
    location = mapped_column(String(200), nullable=True)
    desired_work = mapped_column(JSONB, nullable=False)
    exclusions = mapped_column(JSONB, nullable=False)
    jd_user_id = mapped_column(String(100), nullable=True)
    jd_source_id = mapped_column(String(36), nullable=True)
    jd_source_version = mapped_column(Integer, nullable=True)
    jd_source_kind = mapped_column(String(32), nullable=True)
    status = mapped_column(String(8), nullable=False, server_default="active")
