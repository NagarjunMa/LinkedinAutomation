"""Add enhanced evaluation fields to resume_evaluations table

Revision ID: add_enhanced_evaluation_fields
Revises: 
Create Date: 2025-01-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_enhanced_evaluation_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add enhanced evaluation fields to resume_evaluations table"""
    # Add new columns for enhanced evaluation
    op.add_column('resume_evaluations', sa.Column('critical_issues', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('resume_evaluations', sa.Column('market_positioning', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Update existing score columns to support 0-100 range instead of weighted ranges
    op.alter_column('resume_evaluations', 'ats_compliance_score', 
                   existing_type=sa.Integer(), 
                   type_=sa.Integer(), 
                   nullable=False)
    op.alter_column('resume_evaluations', 'content_quality_score', 
                   existing_type=sa.Integer(), 
                   type_=sa.Integer(), 
                   nullable=False)
    op.alter_column('resume_evaluations', 'experience_points_score', 
                   existing_type=sa.Integer(), 
                   type_=sa.Integer(), 
                   nullable=False)
    op.alter_column('resume_evaluations', 'job_relevance_score', 
                   existing_type=sa.Integer(), 
                   type_=sa.Integer(), 
                   nullable=False)
    op.alter_column('resume_evaluations', 'quality_checks_score', 
                   existing_type=sa.Integer(), 
                   type_=sa.Integer(), 
                   nullable=False)


def downgrade():
    """Remove enhanced evaluation fields from resume_evaluations table"""
    # Remove new columns
    op.drop_column('resume_evaluations', 'market_positioning')
    op.drop_column('resume_evaluations', 'critical_issues')
    
    # Note: We don't downgrade the score column changes as they're compatible
