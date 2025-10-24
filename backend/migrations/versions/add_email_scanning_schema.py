"""Add email scanning schema

Revision ID: email_scanning_001
Revises: profile_settings_001
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'email_scanning_001'
down_revision = 'profile_settings_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add email scanning preferences to user_settings table
    op.add_column('profile_settings', sa.Column('email_scan_frequency', sa.String(), default='daily'))
    op.add_column('profile_settings', sa.Column('email_scan_time', sa.Time(), default='03:00:00'))
    op.add_column('profile_settings', sa.Column('email_scan_timezone', sa.String(), default='America/New_York'))
    op.add_column('profile_settings', sa.Column('last_full_scan', sa.DateTime(timezone=True), nullable=True))
    op.add_column('profile_settings', sa.Column('last_urgent_scan', sa.DateTime(timezone=True), nullable=True))
    op.add_column('profile_settings', sa.Column('email_tracking_enabled', sa.Boolean(), default=True))

    # Create email_scan_history table
    op.create_table('email_scan_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('scan_type', sa.String(), nullable=False),  # 'full' or 'urgent'
        sa.Column('emails_processed', sa.Integer(), default=0),
        sa.Column('status_updates_made', sa.Integer(), default=0),
        sa.Column('urgent_emails_found', sa.Integer(), default=0),
        sa.Column('scan_started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('scan_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_scan_history_user_id'), 'email_scan_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_email_scan_history_scan_type'), 'email_scan_history', ['scan_type'], unique=False)
    op.create_index(op.f('ix_email_scan_history_scan_started_at'), 'email_scan_history', ['scan_started_at'], unique=False)

    # Create processed_emails table
    op.create_table('processed_emails',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('email_from', sa.String(), nullable=True),
        sa.Column('email_subject', sa.String(), nullable=True),
        sa.Column('email_body', sa.Text(), nullable=True),
        sa.Column('email_type', sa.String(), nullable=True),  # confirmation, interview_invitation, rejection, offer
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('status_update_applied', sa.Boolean(), default=False),
        sa.Column('parsed_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['job_listings.id'], nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_processed_emails_user_id'), 'processed_emails', ['user_id'], unique=False)
    op.create_index(op.f('ix_processed_emails_job_id'), 'processed_emails', ['job_id'], unique=False)
    op.create_index(op.f('ix_processed_emails_email_type'), 'processed_emails', ['email_type'], unique=False)
    op.create_index(op.f('ix_processed_emails_received_at'), 'processed_emails', ['received_at'], unique=False)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_processed_emails_received_at'), table_name='processed_emails')
    op.drop_index(op.f('ix_processed_emails_email_type'), table_name='processed_emails')
    op.drop_index(op.f('ix_processed_emails_job_id'), table_name='processed_emails')
    op.drop_index(op.f('ix_processed_emails_user_id'), table_name='processed_emails')
    op.drop_table('processed_emails')

    op.drop_index(op.f('ix_email_scan_history_scan_started_at'), table_name='email_scan_history')
    op.drop_index(op.f('ix_email_scan_history_scan_type'), table_name='email_scan_history')
    op.drop_index(op.f('ix_email_scan_history_user_id'), table_name='email_scan_history')
    op.drop_table('email_scan_history')

    # Remove columns from profile_settings
    op.drop_column('profile_settings', 'email_tracking_enabled')
    op.drop_column('profile_settings', 'last_urgent_scan')
    op.drop_column('profile_settings', 'last_full_scan')
    op.drop_column('profile_settings', 'email_scan_timezone')
    op.drop_column('profile_settings', 'email_scan_time')
    op.drop_column('profile_settings', 'email_scan_frequency')
