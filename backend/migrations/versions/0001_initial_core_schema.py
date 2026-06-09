"""Create legacy core tables required by historical migrations.

Revision ID: initial_core_schema
Revises:
Create Date: 2026-06-09

"""
from alembic import op
import sqlalchemy as sa


revision = "initial_core_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("user_id", name="users_user_id_key"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)

    op.create_table(
        "job_listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("job_type", sa.String(length=50), nullable=True),
        sa.Column("experience_level", sa.String(length=50), nullable=True),
        sa.Column("salary_range", sa.String(length=100), nullable=True),
        sa.Column("application_url", sa.String(length=512), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("posted_date", sa.DateTime(), nullable=True),
        sa.Column("job_metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_listings_title", "job_listings", ["title"], unique=False)
    op.create_index("ix_job_listings_company", "job_listings", ["company"], unique=False)
    op.create_index("idx_job_listings_user_id", "job_listings", ["user_id"], unique=False)

    op.create_table(
        "search_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("match_score", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "job_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("application_status", sa.String(length=50), nullable=True),
        sa.Column("application_source", sa.String(length=100), nullable=True),
        sa.Column("application_date", sa.DateTime(), nullable=True),
        sa.Column("external_application_id", sa.String(length=255), nullable=True),
        sa.Column("application_url", sa.String(length=1000), nullable=True),
        sa.Column("user_notes", sa.Text(), nullable=True),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("interview_date", sa.DateTime(), nullable=True),
        sa.Column("company_response", sa.Boolean(), nullable=True),
        sa.Column("response_date", sa.DateTime(), nullable=True),
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["job_listings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_job_applications_user_id", "job_applications", ["user_id"], unique=False)

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user_profiles_user_id", "user_profiles", ["user_id"], unique=False)

    op.create_table(
        "user_gmail_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=True),
        sa.Column("arcade_user_id", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_gmail_connections_user_id", "user_gmail_connections", ["user_id"], unique=False)
    op.create_index(
        "ix_user_gmail_connections_arcade_user_id",
        "user_gmail_connections",
        ["arcade_user_id"],
        unique=True,
    )

    op.create_table(
        "email_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_email_events_user_id", "email_events", ["user_id"], unique=False)

    op.create_table(
        "email_sync_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_email_sync_logs_user_id", "email_sync_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_email_sync_logs_user_id", table_name="email_sync_logs")
    op.drop_table("email_sync_logs")
    op.drop_index("idx_email_events_user_id", table_name="email_events")
    op.drop_table("email_events")
    op.drop_index("ix_user_gmail_connections_arcade_user_id", table_name="user_gmail_connections")
    op.drop_index("idx_gmail_connections_user_id", table_name="user_gmail_connections")
    op.drop_table("user_gmail_connections")
    op.drop_index("idx_user_profiles_user_id", table_name="user_profiles")
    op.drop_table("user_profiles")
    op.drop_index("idx_job_applications_user_id", table_name="job_applications")
    op.drop_table("job_applications")
    op.drop_table("search_results")
    op.drop_index("idx_job_listings_user_id", table_name="job_listings")
    op.drop_index("ix_job_listings_company", table_name="job_listings")
    op.drop_index("ix_job_listings_title", table_name="job_listings")
    op.drop_table("job_listings")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
