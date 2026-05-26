"""add jd link + accepted_at + template_id to resume_versions

Revision ID: 2026_05_25_jd_links
Revises: 2026_05_20_storage
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_05_25_jd_links"
down_revision = "2026_05_20_storage"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "resume_versions",
        sa.Column("jd_evaluation_id", sa.String(), nullable=True),
    )
    op.add_column(
        "resume_versions",
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "resume_versions",
        sa.Column("template_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_resume_versions_jd_evaluation_id",
        "resume_versions",
        "jd_evaluations",
        ["jd_evaluation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_resume_versions_jd_evaluation_id",
        "resume_versions",
        ["jd_evaluation_id"],
    )


def downgrade():
    op.drop_index("ix_resume_versions_jd_evaluation_id", "resume_versions")
    op.drop_constraint("fk_resume_versions_jd_evaluation_id", "resume_versions", type_="foreignkey")
    op.drop_column("resume_versions", "template_id")
    op.drop_column("resume_versions", "accepted_at")
    op.drop_column("resume_versions", "jd_evaluation_id")
