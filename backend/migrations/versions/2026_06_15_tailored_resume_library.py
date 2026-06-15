"""add tailored resume library metadata

Revision ID: 2026_06_15_tailored_library
Revises: 2026_05_29_pg_cron
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_06_15_tailored_library"
down_revision = "2026_05_29_pg_cron"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("resume_versions", sa.Column("company_name", sa.String(), nullable=True))
    op.add_column("resume_versions", sa.Column("target_role_title", sa.String(), nullable=True))
    op.add_column("resume_versions", sa.Column("role_category", sa.String(), nullable=True))
    op.add_column("resume_versions", sa.Column("seniority", sa.String(), nullable=True))
    op.add_column("resume_versions", sa.Column("country_hint", sa.String(), nullable=True))
    op.add_column("resume_versions", sa.Column("match_score", sa.Integer(), nullable=True))
    op.add_column("resume_versions", sa.Column("source_jd_text", sa.Text(), nullable=True))
    op.alter_column("resume_exports", "storage_path", existing_type=sa.String(), nullable=True)


def downgrade():
    op.alter_column("resume_exports", "storage_path", existing_type=sa.String(), nullable=False)
    op.drop_column("resume_versions", "source_jd_text")
    op.drop_column("resume_versions", "match_score")
    op.drop_column("resume_versions", "country_hint")
    op.drop_column("resume_versions", "seniority")
    op.drop_column("resume_versions", "role_category")
    op.drop_column("resume_versions", "target_role_title")
    op.drop_column("resume_versions", "company_name")
