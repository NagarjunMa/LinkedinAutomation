"""add resume_exports table for phase 2 pdf render

Revision ID: 2026_05_20_phase2
Revises: 2026_05_19_phase1
Create Date: 2026-05-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "2026_05_20_phase2"
down_revision = "2026_05_19_phase1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resume_exports",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("resume_document_id", sa.String(), sa.ForeignKey("resume_documents.id"), nullable=False, index=True),
        sa.Column("resume_version_id", sa.String(), sa.ForeignKey("resume_versions.id"), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=False),     # 'US' | 'IN'
        sa.Column("role_template", sa.String(length=8), nullable=False),  # 'swe' | 'ds' | 'pm'
        sa.Column("storage_path", sa.String(), nullable=False),        # bucket-relative path
        sa.Column("status", sa.String(length=16), nullable=False, server_default="succeeded"),
        sa.Column("render_ms", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("resume_exports")
