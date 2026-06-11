"""Add performance indexes for job listings and applications

Revision ID: performance_indexes
Revises: enhanced_profile_fields
Create Date: 2026-02-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'performance_indexes'
down_revision = 'enhanced_profile_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add performance-critical indexes for job listings

    # Index for extracted_date DESC - critical for dashboard queries
    op.create_index(
        'idx_job_listings_extracted_date_desc',
        'job_listings',
        [sa.text('extracted_date DESC')],
        unique=False
    )

    # Legacy job ownership moved from job_listings.user_id to job_applications.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'job_listings' AND column_name = 'user_id'
            ) THEN
                CREATE INDEX IF NOT EXISTS idx_job_listings_user_applied_date
                ON job_listings (user_id, applied, extracted_date DESC)
                WHERE user_id IS NOT NULL;
            END IF;
        END $$;
        """
    )

    # Index for application status filtering
    op.create_index(
        'idx_job_listings_status_date',
        'job_listings',
        ['application_status', sa.text('extracted_date DESC')],
        unique=False
    )

    # Composite index for job applications - optimizes joins
    op.create_index(
        'idx_job_applications_user_job_date',
        'job_applications',
        ['user_id', 'job_id', sa.text('application_date DESC')],
        unique=False
    )

    # Index for compatibility score filtering (AI matching)
    op.create_index(
        'idx_job_listings_compatibility_score',
        'job_listings',
        [sa.text('compatibility_score DESC NULLS LAST')],
        unique=False,
        postgresql_where=sa.text('compatibility_score IS NOT NULL')
    )

    # Index for location-based queries
    op.create_index(
        'idx_job_listings_location',
        'job_listings',
        ['location'],
        unique=False,
        postgresql_where=sa.text('location IS NOT NULL')
    )

    # Index for company-based queries
    op.create_index(
        'idx_job_listings_company',
        'job_listings',
        ['company'],
        unique=False,
        postgresql_where=sa.text('company IS NOT NULL')
    )


def downgrade():
    # Remove performance indexes
    op.drop_index('idx_job_listings_company', table_name='job_listings')
    op.drop_index('idx_job_listings_location', table_name='job_listings')
    op.drop_index('idx_job_listings_compatibility_score', table_name='job_listings')
    op.drop_index('idx_job_applications_user_job_date', table_name='job_applications')
    op.drop_index('idx_job_listings_status_date', table_name='job_listings')
    op.execute("DROP INDEX IF EXISTS idx_job_listings_user_applied_date")
    op.drop_index('idx_job_listings_extracted_date_desc', table_name='job_listings')
