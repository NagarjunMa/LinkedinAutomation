"""Add referral system tables

Revision ID: referral_system_001
Revises: aad0ded144d1, analytics_tables_001
Create Date: 2025-10-13 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = 'referral_system_001'
down_revision = ('aad0ded144d1', 'analytics_tables_001')  # Multiple heads merge
branch_labels = None
depends_on = None


def upgrade():
    # Create referral_contacts table
    op.create_table('referral_contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('contact_name', sa.String(), nullable=False),
        sa.Column('contact_email', sa.String(), nullable=False),
        sa.Column('company', sa.String(), nullable=False),
        sa.Column('position', sa.String(), nullable=True),
        sa.Column('contact_relationship', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_referral_contacts_id'), 'referral_contacts', ['id'], unique=False)
    op.create_index(op.f('ix_referral_contacts_user_id'), 'referral_contacts', ['user_id'], unique=False)

    # Create referral_email_drafts table
    op.create_table('referral_email_drafts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('email_body', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=True),
        sa.Column('template_used', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['referral_contacts.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['job_listings.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_referral_email_drafts_id'), 'referral_email_drafts', ['id'], unique=False)
    op.create_index(op.f('ix_referral_email_drafts_user_id'), 'referral_email_drafts', ['user_id'], unique=False)
    op.create_index(op.f('ix_referral_email_drafts_job_id'), 'referral_email_drafts', ['job_id'], unique=False)
    op.create_index(op.f('ix_referral_email_drafts_contact_id'), 'referral_email_drafts', ['contact_id'], unique=False)

    # Create referral_emails_sent table
    op.create_table('referral_emails_sent',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('draft_id', sa.Integer(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True),
        sa.Column('response_received', sa.Boolean(), nullable=False, default=False),
        sa.Column('response_date', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['referral_contacts.id'], ),
        sa.ForeignKeyConstraint(['draft_id'], ['referral_email_drafts.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['job_listings.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_referral_emails_sent_id'), 'referral_emails_sent', ['id'], unique=False)
    op.create_index(op.f('ix_referral_emails_sent_user_id'), 'referral_emails_sent', ['user_id'], unique=False)
    op.create_index(op.f('ix_referral_emails_sent_job_id'), 'referral_emails_sent', ['job_id'], unique=False)
    op.create_index(op.f('ix_referral_emails_sent_contact_id'), 'referral_emails_sent', ['contact_id'], unique=False)
    op.create_index(op.f('ix_referral_emails_sent_draft_id'), 'referral_emails_sent', ['draft_id'], unique=False)

    # Create performance indexes for common queries
    op.create_index('idx_referral_contacts_user_email', 'referral_contacts', ['user_id', 'contact_email'], unique=False)
    op.create_index('idx_referral_drafts_user_job_contact', 'referral_email_drafts', ['user_id', 'job_id', 'contact_id'], unique=False)
    op.create_index('idx_referral_sent_user_date', 'referral_emails_sent', ['user_id', sa.text('sent_at DESC')], unique=False)
    op.create_index('idx_referral_analytics_date_response', 'referral_emails_sent', ['sent_at', 'response_received'], unique=False)


def downgrade():
    # Drop indexes first
    op.drop_index('idx_referral_analytics_date_response', table_name='referral_emails_sent')
    op.drop_index('idx_referral_sent_user_date', table_name='referral_emails_sent')
    op.drop_index('idx_referral_drafts_user_job_contact', table_name='referral_email_drafts')
    op.drop_index('idx_referral_contacts_user_email', table_name='referral_contacts')

    # Drop referral_emails_sent table
    op.drop_index(op.f('ix_referral_emails_sent_draft_id'), table_name='referral_emails_sent')
    op.drop_index(op.f('ix_referral_emails_sent_contact_id'), table_name='referral_emails_sent')
    op.drop_index(op.f('ix_referral_emails_sent_job_id'), table_name='referral_emails_sent')
    op.drop_index(op.f('ix_referral_emails_sent_user_id'), table_name='referral_emails_sent')
    op.drop_index(op.f('ix_referral_emails_sent_id'), table_name='referral_emails_sent')
    op.drop_table('referral_emails_sent')

    # Drop referral_email_drafts table
    op.drop_index(op.f('ix_referral_email_drafts_contact_id'), table_name='referral_email_drafts')
    op.drop_index(op.f('ix_referral_email_drafts_job_id'), table_name='referral_email_drafts')
    op.drop_index(op.f('ix_referral_email_drafts_user_id'), table_name='referral_email_drafts')
    op.drop_index(op.f('ix_referral_email_drafts_id'), table_name='referral_email_drafts')
    op.drop_table('referral_email_drafts')

    # Drop referral_contacts table
    op.drop_index(op.f('ix_referral_contacts_user_id'), table_name='referral_contacts')
    op.drop_index(op.f('ix_referral_contacts_id'), table_name='referral_contacts')
    op.drop_table('referral_contacts')