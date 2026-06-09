"""add_missing_resume_evaluation_columns

Revision ID: 481c941a4959
Revises: add_resume_models_manual
Create Date: 2025-09-04 21:08:07.812453

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '481c941a4959'
down_revision: Union[str, None] = 'add_resume_models_manual'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to resume_evaluations table
    op.add_column('resume_evaluations', sa.Column('experience_points_score', sa.Integer(), nullable=True))
    op.add_column('resume_evaluations', sa.Column('job_relevance_score', sa.Integer(), nullable=True))
    op.add_column('resume_evaluations', sa.Column('quality_checks_score', sa.Integer(), nullable=True))
    op.add_column('resume_evaluations', sa.Column('critical_issues', sa.JSON(), nullable=True))
    op.add_column('resume_evaluations', sa.Column('market_positioning', sa.JSON(), nullable=True))
    op.add_column('resume_evaluations', sa.Column('evaluation_prompt', sa.Text(), nullable=True))
    
    # Update the data type of existing columns to match the model.
    op.execute("ALTER TABLE resume_evaluations ALTER COLUMN overall_score TYPE INTEGER USING overall_score::integer")
    op.execute("ALTER TABLE resume_evaluations ALTER COLUMN ats_compliance_score TYPE INTEGER USING ats_compliance_score::integer")
    op.execute("ALTER TABLE resume_evaluations ALTER COLUMN content_quality_score TYPE INTEGER USING content_quality_score::integer")

    # Update strengths and improvements to be JSON instead of ARRAY.
    op.execute("ALTER TABLE resume_evaluations ALTER COLUMN strengths TYPE JSON USING to_json(strengths)")
    op.execute("ALTER TABLE resume_evaluations ALTER COLUMN improvements TYPE JSON USING to_json(improvements)")
    
    # Make the new integer columns NOT NULL after adding them
    op.alter_column('resume_evaluations', 'experience_points_score', nullable=False)
    op.alter_column('resume_evaluations', 'job_relevance_score', nullable=False)
    op.alter_column('resume_evaluations', 'quality_checks_score', nullable=False)


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('resume_evaluations', 'evaluation_prompt')
    op.drop_column('resume_evaluations', 'market_positioning')
    op.drop_column('resume_evaluations', 'critical_issues')
    op.drop_column('resume_evaluations', 'quality_checks_score')
    op.drop_column('resume_evaluations', 'job_relevance_score')
    op.drop_column('resume_evaluations', 'experience_points_score')
    
    # Revert column types back to original
    op.alter_column('resume_evaluations', 'overall_score', type_=sa.Float())
    op.alter_column('resume_evaluations', 'ats_compliance_score', type_=sa.Float())
    op.alter_column('resume_evaluations', 'content_quality_score', type_=sa.Float())
    
    # Revert strengths and improvements back to ARRAY
    op.alter_column('resume_evaluations', 'strengths', type_=sa.ARRAY(sa.String()))
    op.alter_column('resume_evaluations', 'improvements', type_=sa.ARRAY(sa.String()))
