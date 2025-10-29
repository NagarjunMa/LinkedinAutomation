"""
Database migration to add Supabase caching and task queue tables.
This migration creates the necessary tables for PostgreSQL-based caching system
that replaces Redis dependency.

Tables created:
- cache_entries: Key-value cache storage with TTL support
- task_queue: Background task queue for Celery replacement
- session_store: User session storage
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    """Create Supabase caching system tables"""

    # Cache entries table for key-value storage with TTL
    op.create_table(
        'cache_entries',
        sa.Column('key', sa.String(255), primary_key=True),
        sa.Column('value', sa.Text(), nullable=False, comment='JSON serialized cache data'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='Cache expiration timestamp'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('access_count', sa.Integer(), default=0, comment='Number of times cache was accessed'),
        sa.Column('last_accessed', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('tags', postgresql.JSON(), default=[], comment='Tags for bulk cache invalidation')
    )

    # Create indexes for cache performance
    op.create_index('idx_cache_expires_at', 'cache_entries', ['expires_at'])
    op.create_index('idx_cache_last_accessed', 'cache_entries', ['last_accessed'])

    # Task queue table for background job processing
    op.create_table(
        'task_queue',
        sa.Column('id', sa.String(255), primary_key=True, comment='Unique task identifier'),
        sa.Column('task_name', sa.String(255), nullable=False, comment='Registered task function name'),
        sa.Column('args', postgresql.JSON(), default=[], comment='Task function arguments'),
        sa.Column('kwargs', postgresql.JSON(), default={}, comment='Task function keyword arguments'),
        sa.Column('status', sa.String(50), default='PENDING', comment='Task status: PENDING, RUNNING, SUCCESS, FAILURE'),
        sa.Column('result', sa.Text(), nullable=True, comment='JSON serialized task result'),
        sa.Column('error', sa.Text(), nullable=True, comment='Error message if task failed'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, comment='Number of retry attempts'),
        sa.Column('priority', sa.Integer(), default=5, comment='Task priority: 1=highest, 10=lowest'),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True, comment='When to execute the task')
    )

    # Create indexes for task queue performance
    op.create_index('idx_task_status', 'task_queue', ['status'])
    op.create_index('idx_task_priority_created', 'task_queue', ['priority', 'created_at'])
    op.create_index('idx_task_scheduled_for', 'task_queue', ['scheduled_for'])
    op.create_index('idx_task_name', 'task_queue', ['task_name'])

    # Session store table for user sessions
    op.create_table(
        'session_store',
        sa.Column('session_id', sa.String(255), primary_key=True),
        sa.Column('data', sa.Text(), nullable=False, comment='JSON serialized session data'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='Session expiration timestamp'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create index for session cleanup
    op.create_index('idx_session_expires_at', 'session_store', ['expires_at'])

def downgrade():
    """Remove Supabase caching system tables"""
    op.drop_table('session_store')
    op.drop_table('task_queue')
    op.drop_table('cache_entries')