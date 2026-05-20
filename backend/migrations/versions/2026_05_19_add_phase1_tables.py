"""add phase 1 resume and credit tables

Revision ID: 2026_05_19_phase1
Revises: d9dfe57eecfa, performance_indexes
Create Date: 2026-05-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "2026_05_19_phase1"
down_revision = ("d9dfe57eecfa", "performance_indexes")
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resume_documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),   # 'pdf' | 'docx'
        sa.Column("parsed_json", postgresql.JSONB(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "resume_evaluations_v2",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("resume_document_id", sa.String(), sa.ForeignKey("resume_documents.id"), nullable=False, index=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("bullet_flags", postgresql.JSONB(), nullable=False),
        sa.Column("format_issues", postgresql.JSONB(), nullable=False),
        sa.Column("summary_critique", sa.Text(), nullable=True),
        sa.Column("ats_parseability", sa.Integer(), nullable=False),
        sa.Column("ats_raw_text", sa.Text(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "resume_versions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("resume_document_id", sa.String(), sa.ForeignKey("resume_documents.id"), nullable=False, index=True),
        sa.Column("parent_version_id", sa.String(), nullable=True),
        sa.Column("change_set", postgresql.JSONB(), nullable=False),
        sa.Column("parsed_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "jd_evaluations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("resume_document_id", sa.String(), sa.ForeignKey("resume_documents.id"), nullable=False),
        sa.Column("jd_text", sa.Text(), nullable=False),
        sa.Column("extracted_requirements", postgresql.JSONB(), nullable=False),
        sa.Column("diff_plan", postgresql.JSONB(), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "credit_ledger",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("delta", sa.Integer(), nullable=False),  # +grant / -debit / +refund
        sa.Column("reason", sa.String(), nullable=False),  # 'grant'|'evaluate'|'tailor'|'export'|'refund'
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("external_ref", sa.String(), nullable=True, unique=True),  # Stripe idempotency
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_credit_ledger_user_created", "credit_ledger", ["user_id", "created_at"])


def downgrade():
    op.drop_index("ix_credit_ledger_user_created", "credit_ledger")
    op.drop_table("credit_ledger")
    op.drop_table("jd_evaluations")
    op.drop_table("resume_versions")
    op.drop_table("resume_evaluations_v2")
    op.drop_table("resume_documents")
