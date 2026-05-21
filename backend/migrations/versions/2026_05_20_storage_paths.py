"""add storage_path to resume_documents

Revision ID: 2026_05_20_storage
Revises: 2026_05_20_phase2
Create Date: 2026-05-20
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_05_20_storage"
down_revision = "2026_05_20_phase2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "resume_documents",
        sa.Column("storage_path", sa.String(), nullable=True),
    )
    # file_path remains for backwards-compat; will be dropped after backfill.


def downgrade():
    op.drop_column("resume_documents", "storage_path")
