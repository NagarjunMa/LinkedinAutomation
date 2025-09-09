"""add resume models

Revision ID: add_resume_models_manual
Revises: b77deec731d6
Create Date: 2025-08-21 00:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_resume_models_manual'
down_revision = 'b77deec731d6'
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
        sa.Column('uploaded_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('evaluation_status', sa.String(), nullable=True),
        sa.Column('evaluation_result', sa.JSON(), nullable=True),
        sa.Column('evaluated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('ai_model_version', sa.String(), nullable=True),
        sa.Column('processing_time', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create resume_evaluations table
    op.create_table('resume_evaluations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('resume_id', sa.String(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('ats_compliance_score', sa.Float(), nullable=False),
        sa.Column('content_quality_score', sa.Float(), nullable=False),
        sa.Column('formatting_score', sa.Float(), nullable=False),
        sa.Column('strengths', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('improvements', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('detailed_feedback', sa.String(), nullable=False),
        sa.Column('ats_compatibility', sa.String(), nullable=False),
        sa.Column('keyword_analysis', sa.JSON(), nullable=False),
        sa.Column('evaluated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('ai_model_version', sa.String(), nullable=True),
        sa.Column('processing_time', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add foreign key constraints
    op.create_foreign_key('resumes_user_id_fkey', 'resumes', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key('resume_evaluations_resume_id_fkey', 'resume_evaluations', 'resumes', ['resume_id'], ['id'])
    
    # Create indexes
    op.create_index('ix_resumes_user_id', 'resumes', ['user_id'])
    op.create_index('ix_resumes_evaluation_status', 'resumes', ['evaluation_status'])
    op.create_index('ix_resume_evaluations_resume_id', 'resume_evaluations', ['resume_id'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_resume_evaluations_resume_id', 'resume_evaluations')
    op.drop_index('ix_resumes_evaluation_status', 'resumes')
    op.drop_index('ix_resumes_user_id', 'resumes')
    
    # Drop foreign key constraints
    op.drop_constraint('resume_evaluations_resume_id_fkey', 'resume_evaluations', type_='foreignkey')
    op.drop_constraint('resumes_user_id_fkey', 'resumes', type_='foreignkey')
    
    # Drop tables
    op.drop_table('resume_evaluations')
    op.drop_table('resumes')
