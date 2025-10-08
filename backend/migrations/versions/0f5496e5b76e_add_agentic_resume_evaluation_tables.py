"""add_agentic_resume_evaluation_tables

Revision ID: 0f5496e5b76e
Revises: 481c941a4959
Create Date: 2025-09-10 13:44:31.019858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f5496e5b76e'
down_revision: Union[str, None] = '481c941a4959'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agent results table
    op.create_table('resume_agent_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('evaluation_id', sa.String(), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('agent_results', sa.JSON(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), default=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create agent performance metrics table
    op.create_table('agent_performance_metrics',
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('total_executions', sa.Integer(), default=0),
        sa.Column('success_rate', sa.Float(), default=1.0),
        sa.Column('avg_execution_time_ms', sa.Float(), nullable=True),
        sa.Column('last_execution', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('last_updated', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('agent_name')
    )
    
    # Create evaluation sessions table for tracking complete evaluations
    op.create_table('resume_evaluation_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('resume_id', sa.String(), nullable=False),
        sa.Column('evaluation_type', sa.String(50), default='agentic'),
        sa.Column('overall_score', sa.Integer(), nullable=True),
        sa.Column('executive_summary', sa.Text(), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('successful_agents', sa.Integer(), default=0),
        sa.Column('total_agents', sa.Integer(), default=0),
        sa.Column('confidence_percentage', sa.Float(), nullable=True),
        sa.Column('evaluation_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for performance
    op.create_index('ix_resume_agent_results_evaluation_id', 'resume_agent_results', ['evaluation_id'])
    op.create_index('ix_resume_agent_results_agent_name', 'resume_agent_results', ['agent_name'])
    op.create_index('ix_resume_agent_results_created_at', 'resume_agent_results', ['created_at'])
    op.create_index('ix_resume_evaluation_sessions_user_id', 'resume_evaluation_sessions', ['user_id'])
    op.create_index('ix_resume_evaluation_sessions_resume_id', 'resume_evaluation_sessions', ['resume_id'])
    op.create_index('ix_resume_evaluation_sessions_created_at', 'resume_evaluation_sessions', ['created_at'])
    
    # Add foreign key constraints
    op.create_foreign_key('resume_agent_results_evaluation_id_fkey', 'resume_agent_results', 'resume_evaluation_sessions', ['evaluation_id'], ['id'])
    op.create_foreign_key('resume_evaluation_sessions_user_id_fkey', 'resume_evaluation_sessions', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key('resume_evaluation_sessions_resume_id_fkey', 'resume_evaluation_sessions', 'resumes', ['resume_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('resume_evaluation_sessions_resume_id_fkey', 'resume_evaluation_sessions', type_='foreignkey')
    op.drop_constraint('resume_evaluation_sessions_user_id_fkey', 'resume_evaluation_sessions', type_='foreignkey')
    op.drop_constraint('resume_agent_results_evaluation_id_fkey', 'resume_agent_results', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('ix_resume_evaluation_sessions_created_at', 'resume_evaluation_sessions')
    op.drop_index('ix_resume_evaluation_sessions_resume_id', 'resume_evaluation_sessions')
    op.drop_index('ix_resume_evaluation_sessions_user_id', 'resume_evaluation_sessions')
    op.drop_index('ix_resume_agent_results_created_at', 'resume_agent_results')
    op.drop_index('ix_resume_agent_results_agent_name', 'resume_agent_results')
    op.drop_index('ix_resume_agent_results_evaluation_id', 'resume_agent_results')
    
    # Drop tables
    op.drop_table('resume_evaluation_sessions')
    op.drop_table('agent_performance_metrics')
    op.drop_table('resume_agent_results')
