"""add evaluation score explanations

Revision ID: f2b8d1c9a710
Revises: 2026_06_15_tailored_library
Create Date: 2026-06-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f2b8d1c9a710"
down_revision = "2026_06_15_tailored_library"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resume_evaluations_v2",
        sa.Column("readiness_label", sa.String(), nullable=False, server_default="needs_work"),
    )
    op.add_column(
        "resume_evaluations_v2",
        sa.Column(
            "score_breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "resume_evaluations_v2",
        sa.Column(
            "score_explanation",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "resume_evaluations_v2",
        sa.Column(
            "top_actions_before_applying",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "resume_evaluations_v2",
        sa.Column("parser_confidence", sa.String(), nullable=False, server_default="medium"),
    )


def downgrade() -> None:
    op.drop_column("resume_evaluations_v2", "parser_confidence")
    op.drop_column("resume_evaluations_v2", "top_actions_before_applying")
    op.drop_column("resume_evaluations_v2", "score_explanation")
    op.drop_column("resume_evaluations_v2", "score_breakdown")
    op.drop_column("resume_evaluations_v2", "readiness_label")
