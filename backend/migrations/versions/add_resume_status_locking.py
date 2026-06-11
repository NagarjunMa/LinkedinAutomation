"""Add resume status locking fields

Revision ID: add_resume_status_locking
Revises:
Create Date: 2024-10-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_resume_status_locking'
down_revision = 'add_resume_models_manual'
branch_labels = None
depends_on = None


def upgrade():
    # Add status locking fields to resumes table
    op.add_column('resumes', sa.Column('is_locked', sa.Boolean(), default=False))
    op.add_column('resumes', sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('resumes', sa.Column('locked_by', sa.String(), nullable=True))
    op.add_column('resumes', sa.Column('lock_expires_at', sa.DateTime(timezone=True), nullable=True))

    # Create index for efficient lock queries
    op.create_index('idx_resumes_lock_status', 'resumes', ['is_locked', 'lock_expires_at'])


def downgrade():
    # Remove index
    op.drop_index('idx_resumes_lock_status', table_name='resumes')

    # Remove columns
    op.drop_column('resumes', 'lock_expires_at')
    op.drop_column('resumes', 'locked_by')
    op.drop_column('resumes', 'locked_at')
    op.drop_column('resumes', 'is_locked')
