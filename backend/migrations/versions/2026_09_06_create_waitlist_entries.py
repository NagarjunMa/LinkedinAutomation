"""create private-preview waitlist entries

Revision ID: 2026_09_06_waitlist
Revises: c4e7a2f91b30
Create Date: 2026-09-06
"""

from alembic import op
import sqlalchemy as sa


revision = "2026_09_06_waitlist"
down_revision = "c4e7a2f91b30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "waitlist_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("normalized_email", sa.String(length=254), nullable=False),
        sa.Column("career_stage", sa.String(length=40), nullable=True),
        sa.Column("target_role", sa.String(length=120), nullable=True),
        sa.Column("communication_challenge", sa.Text(), nullable=True),
        sa.Column("consent_granted", sa.Boolean(), nullable=False),
        sa.Column("consent_version", sa.String(length=32), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("retention_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_email", name="uq_waitlist_entries_email"),
    )
    op.create_index(
        "ix_waitlist_entries_retention_expires_at",
        "waitlist_entries",
        ["retention_expires_at"],
        unique=False,
    )

    # This table is written only by the FastAPI database connection. It is not
    # a browser-facing Supabase Data API resource.
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE public.waitlist_entries ENABLE ROW LEVEL SECURITY")
        op.execute("REVOKE ALL ON TABLE public.waitlist_entries FROM PUBLIC")
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                    EXECUTE 'REVOKE ALL ON TABLE public.waitlist_entries FROM anon';
                END IF;
                IF EXISTS (
                    SELECT 1 FROM pg_roles WHERE rolname = 'authenticated'
                ) THEN
                    EXECUTE 'REVOKE ALL ON TABLE public.waitlist_entries FROM authenticated';
                END IF;
            END
            $$
            """
        )


def downgrade() -> None:
    op.drop_index(
        "ix_waitlist_entries_retention_expires_at",
        table_name="waitlist_entries",
    )
    op.drop_table("waitlist_entries")
