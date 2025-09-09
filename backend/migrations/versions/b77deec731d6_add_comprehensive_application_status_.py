"""add_comprehensive_application_status_fields

Revision ID: b77deec731d6
Revises: manual_google_oauth_migration
Create Date: 2025-08-13 18:25:04.610366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b77deec731d6'
down_revision: Union[str, None] = 'manual_google_oauth_migration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new comprehensive application status fields to job_listings table
    op.add_column('job_listings', sa.Column('application_status', sa.String(50), nullable=True))
    op.add_column('job_listings', sa.Column('application_notes', sa.Text(), nullable=True))
    op.add_column('job_listings', sa.Column('application_context', sa.Text(), nullable=True))
    op.add_column('job_listings', sa.Column('compatibility_score', sa.Float(), nullable=True))
    op.add_column('job_listings', sa.Column('ai_insights', sa.Text(), nullable=True))
    
    # Set default values for existing records
    op.execute("UPDATE job_listings SET application_status = 'pending' WHERE application_status IS NULL")
    op.execute("UPDATE job_listings SET application_status = 'applied' WHERE applied = true AND application_status IS NULL")


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('job_listings', 'ai_insights')
    op.drop_column('job_listings', 'compatibility_score')
    op.drop_column('job_listings', 'application_context')
    op.drop_column('job_listings', 'application_notes')
    op.drop_column('job_listings', 'application_status')
