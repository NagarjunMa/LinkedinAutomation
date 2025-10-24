"""Add enhanced profile fields

Revision ID: enhanced_profile_fields
Revises: profile_settings_tables
Create Date: 2025-10-13 23:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enhanced_profile_fields'
down_revision = 'profile_settings_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to profile_info table
    op.add_column('profile_info', sa.Column('referral_template', sa.Text(), nullable=True))
    op.add_column('profile_info', sa.Column('work_experiences', sa.JSON(), nullable=True))
    op.add_column('profile_info', sa.Column('education_history', sa.JSON(), nullable=True))


def downgrade():
    # Remove new columns from profile_info table
    op.drop_column('profile_info', 'education_history')
    op.drop_column('profile_info', 'work_experiences')
    op.drop_column('profile_info', 'referral_template')