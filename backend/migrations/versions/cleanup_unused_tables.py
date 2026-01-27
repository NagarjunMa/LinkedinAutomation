"""Drop unused analytics, agent, and contact tables

Revision ID: cleanup_unused_tables
Revises:
Create Date: 2024-01-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cleanup_unused_tables'
down_revision = None  # Update this with the actual last migration
branch_labels = None
depends_on = None


def upgrade():
    """Drop unused tables and indexes to simplify database schema"""

    # Drop analytics related tables (over-complex for core features)
    op.execute("DROP TABLE IF EXISTS analytics_insights CASCADE")
    op.execute("DROP TABLE IF EXISTS feature_usage_log CASCADE")
    op.execute("DROP TABLE IF EXISTS analytics_cache CASCADE")
    op.execute("DROP TABLE IF EXISTS user_analytics CASCADE")

    # Drop agent system tables (replaced with consolidated evaluator)
    op.execute("DROP TABLE IF EXISTS resume_agent_results CASCADE")
    op.execute("DROP TABLE IF EXISTS resume_evaluation_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS agent_performance_metrics CASCADE")

    # Drop contact management table (standalone feature)
    op.execute("DROP TABLE IF EXISTS contacts CASCADE")

    # Drop complex indexes that were used by analytics
    op.execute("DROP INDEX IF EXISTS idx_user_analytics_user_updated")
    op.execute("DROP INDEX IF EXISTS idx_analytics_cache_user_expires")
    op.execute("DROP INDEX IF EXISTS idx_insights_user_type_priority")
    op.execute("DROP INDEX IF EXISTS idx_insights_actionable_shown")
    op.execute("DROP INDEX IF EXISTS idx_feature_usage_user_feature_date")

    # Clean up user table relationships
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS analytics_enabled")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS last_analytics_update")


def downgrade():
    """Note: This migration removes tables and data - downgrade not supported"""
    pass  # Cannot recreate dropped tables with data