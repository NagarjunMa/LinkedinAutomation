"""add_missing_resume_evaluation_columns

Revision ID: 6422cebae43e
Revises: d74b008448ee
Create Date: 2025-09-10 15:41:53.651545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6422cebae43e'
down_revision: Union[str, None] = 'd74b008448ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to resume_evaluations table
    op.add_column('resume_evaluations', sa.Column('critical_issues', sa.JSON(), nullable=True))
    op.add_column('resume_evaluations', sa.Column('market_positioning', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('resume_evaluations', 'market_positioning')
    op.drop_column('resume_evaluations', 'critical_issues')
