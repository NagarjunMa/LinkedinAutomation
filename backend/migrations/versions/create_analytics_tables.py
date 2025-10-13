"""Create analytics tables for AI-powered user insights

Revision ID: analytics_tables_001
Revises:
Create Date: 2024-10-12 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'analytics_tables_001'
down_revision = None  # Update this with the latest migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Create user_analytics table
    op.create_table('user_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('top_skills', sa.JSON(), nullable=True),
        sa.Column('trending_skills', sa.JSON(), nullable=True),
        sa.Column('recommended_skills', sa.JSON(), nullable=True),
        sa.Column('skills_diversity_score', sa.Float(), nullable=True),
        sa.Column('work_location_preferences', sa.JSON(), nullable=True),
        sa.Column('job_title_distribution', sa.JSON(), nullable=True),
        sa.Column('company_size_preferences', sa.JSON(), nullable=True),
        sa.Column('salary_range_analysis', sa.JSON(), nullable=True),
        sa.Column('application_velocity', sa.Float(), nullable=True),
        sa.Column('application_success_rate', sa.Float(), nullable=True),
        sa.Column('peak_application_days', sa.JSON(), nullable=True),
        sa.Column('application_time_patterns', sa.JSON(), nullable=True),
        sa.Column('ai_insights', sa.JSON(), nullable=True),
        sa.Column('success_patterns', sa.JSON(), nullable=True),
        sa.Column('improvement_suggestions', sa.JSON(), nullable=True),
        sa.Column('weekly_recommendation', sa.Text(), nullable=True),
        sa.Column('competition_level', sa.String(length=20), nullable=True),
        sa.Column('market_demand_score', sa.Float(), nullable=True),
        sa.Column('salary_competitiveness', sa.String(length=20), nullable=True),
        sa.Column('total_applications_analyzed', sa.Integer(), nullable=True),
        sa.Column('analysis_period_start', sa.DateTime(), nullable=True),
        sa.Column('analysis_period_end', sa.DateTime(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('analytics_version', sa.String(length=10), nullable=True),
        sa.Column('generation_time_seconds', sa.Float(), nullable=True),
        sa.Column('ai_confidence_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_analytics_id'), 'user_analytics', ['id'], unique=False)
    op.create_index(op.f('ix_user_analytics_user_id'), 'user_analytics', ['user_id'], unique=False)

    # Create analytics_cache table
    op.create_table('analytics_cache',
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('cache_data', sa.JSON(), nullable=False),
        sa.Column('cache_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('access_count', sa.Integer(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.Column('data_hash', sa.String(length=64), nullable=True),
        sa.Column('cache_size_bytes', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_analytics_cache_user_id'), 'analytics_cache', ['user_id'], unique=False)

    # Create analytics_insights table
    op.create_table('analytics_insights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('analytics_id', sa.Integer(), nullable=False),
        sa.Column('insight_type', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('is_actionable', sa.Boolean(), nullable=True),
        sa.Column('action_required', sa.Text(), nullable=True),
        sa.Column('estimated_impact', sa.String(length=20), nullable=True),
        sa.Column('implementation_difficulty', sa.String(length=20), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('was_acted_upon', sa.Boolean(), nullable=True),
        sa.Column('action_date', sa.DateTime(), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('validation_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('shown_to_user', sa.Boolean(), nullable=True),
        sa.Column('shown_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['analytics_id'], ['user_analytics.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analytics_insights_id'), 'analytics_insights', ['id'], unique=False)
    op.create_index(op.f('ix_analytics_insights_user_id'), 'analytics_insights', ['user_id'], unique=False)

    # Create composite indexes for better query performance
    op.create_index('idx_user_analytics_user_updated', 'user_analytics', ['user_id', sa.text('last_updated DESC')], unique=False)
    op.create_index('idx_analytics_cache_user_expires', 'analytics_cache', ['user_id', 'expires_at'], unique=False)
    op.create_index('idx_insights_user_type_priority', 'analytics_insights', ['user_id', 'insight_type', 'priority'], unique=False)
    op.create_index('idx_insights_actionable_shown', 'analytics_insights', ['is_actionable', 'shown_to_user'], unique=False)


def downgrade():
    # Drop indexes first
    op.drop_index('idx_insights_actionable_shown', table_name='analytics_insights')
    op.drop_index('idx_insights_user_type_priority', table_name='analytics_insights')
    op.drop_index('idx_analytics_cache_user_expires', table_name='analytics_cache')
    op.drop_index('idx_user_analytics_user_updated', table_name='user_analytics')

    # Drop tables
    op.drop_index(op.f('ix_analytics_insights_user_id'), table_name='analytics_insights')
    op.drop_index(op.f('ix_analytics_insights_id'), table_name='analytics_insights')
    op.drop_table('analytics_insights')

    op.drop_index(op.f('ix_analytics_cache_user_id'), table_name='analytics_cache')
    op.drop_table('analytics_cache')

    op.drop_index(op.f('ix_user_analytics_user_id'), table_name='user_analytics')
    op.drop_index(op.f('ix_user_analytics_id'), table_name='user_analytics')
    op.drop_table('user_analytics')