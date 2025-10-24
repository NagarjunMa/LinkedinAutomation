"""Add user profile and settings tables

Revision ID: profile_settings_001
Revises: referral_system_001
Create Date: 2025-10-13 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'profile_settings_001'
down_revision = 'referral_system_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create profile_info table
    op.create_table('profile_info',
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('target_job_titles', sa.JSON(), nullable=True),
        sa.Column('preferred_locations', sa.JSON(), nullable=True),
        sa.Column('minimum_salary', sa.Integer(), nullable=True),
        sa.Column('experience_level', sa.String(), nullable=True),
        sa.Column('graduation_date', sa.Date(), nullable=True),
        sa.Column('university', sa.String(), nullable=True),
        sa.Column('background_summary', sa.Text(), nullable=True),
        sa.Column('email_signature', sa.Text(), nullable=True),
        sa.Column('primary_resume_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_profile_info_user_id'), 'profile_info', ['user_id'], unique=False)
    op.create_index(op.f('ix_profile_info_email'), 'profile_info', ['email'], unique=True)

    # Create profile_settings table
    op.create_table('profile_settings',
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('email_notifications', sa.JSON(), nullable=True),
        sa.Column('notification_frequency', sa.String(), nullable=True),
        sa.Column('email_forwarding_enabled', sa.String(), nullable=True),
        sa.Column('forwarding_address', sa.String(), nullable=True),
        sa.Column('last_email_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_retention_days', sa.Integer(), nullable=True),
        sa.Column('analytics_enabled', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_profile_settings_user_id'), 'profile_settings', ['user_id'], unique=False)

    # Create profile_change_history table
    op.create_table('profile_change_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('field_changed', sa.String(), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_profile_change_history_id'), 'profile_change_history', ['id'], unique=False)
    op.create_index(op.f('ix_profile_change_history_user_id'), 'profile_change_history', ['user_id'], unique=False)

    # Create performance indexes
    op.create_index('idx_profile_info_user_updated', 'profile_info', ['user_id', sa.text('updated_at DESC')], unique=False)
    op.create_index('idx_profile_history_user_date', 'profile_change_history', ['user_id', sa.text('changed_at DESC')], unique=False)


def downgrade():
    # Drop indexes first
    op.drop_index('idx_profile_history_user_date', table_name='profile_change_history')
    op.drop_index('idx_profile_info_user_updated', table_name='profile_info')

    # Drop profile_change_history table
    op.drop_index(op.f('ix_profile_change_history_user_id'), table_name='profile_change_history')
    op.drop_index(op.f('ix_profile_change_history_id'), table_name='profile_change_history')
    op.drop_table('profile_change_history')

    # Drop profile_settings table
    op.drop_index(op.f('ix_profile_settings_user_id'), table_name='profile_settings')
    op.drop_table('profile_settings')

    # Drop profile_info table
    op.drop_index(op.f('ix_profile_info_email'), table_name='profile_info')
    op.drop_index(op.f('ix_profile_info_user_id'), table_name='profile_info')
    op.drop_table('profile_info')