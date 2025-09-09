"""Add resume models

Revision ID: add_resume_models
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_resume_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create resumes table
    op.create_table('resumes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('evaluation_status', sa.String(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ai_model_version', sa.String(), nullable=True),
        sa.Column('processing_time', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resumes_id'), 'resumes', ['id'], unique=False)
    
    # Create resume_evaluations table
    op.create_table('resume_evaluations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('resume_id', sa.String(), nullable=False),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('ats_compliance_score', sa.Integer(), nullable=False),
        sa.Column('content_quality_score', sa.Integer(), nullable=False),
        sa.Column('experience_points_score', sa.Integer(), nullable=False),
        sa.Column('job_relevance_score', sa.Integer(), nullable=False),
        sa.Column('quality_checks_score', sa.Integer(), nullable=False),
        sa.Column('strengths', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('improvements', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('detailed_feedback', sa.Text(), nullable=True),
        sa.Column('ats_compatibility', sa.String(), nullable=False),
        sa.Column('keyword_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('ai_model_version', sa.String(), nullable=True),
        sa.Column('evaluation_prompt', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_evaluations_id'), 'resume_evaluations', ['id'], unique=False)
    
    # Add foreign key constraints
    op.create_foreign_key(None, 'resumes', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key(None, 'resume_evaluations', 'resumes', ['resume_id'], ['id'])


def downgrade():
    # Remove foreign key constraints
    op.drop_constraint(None, 'resume_evaluations', type_='foreignkey')
    op.drop_constraint(None, 'resumes', type_='foreignkey')
    
    # Drop tables
    op.drop_index(op.f('ix_resume_evaluations_id'), table_name='resume_evaluations')
    op.drop_table('resume_evaluations')
    op.drop_index(op.f('ix_resumes_id'), table_name='resumes')
    op.drop_table('resumes')
