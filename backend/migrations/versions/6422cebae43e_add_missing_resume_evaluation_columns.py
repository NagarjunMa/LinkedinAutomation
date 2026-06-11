"""add_missing_resume_evaluation_columns

Revision ID: 6422cebae43e
Revises: d74b008448ee
Create Date: 2025-09-10 15:41:53.651545

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6422cebae43e'
down_revision: Union[str, None] = 'd74b008448ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE resume_evaluations ADD COLUMN IF NOT EXISTS critical_issues JSON")
    op.execute("ALTER TABLE resume_evaluations ADD COLUMN IF NOT EXISTS market_positioning JSON")


def downgrade() -> None:
    op.execute("ALTER TABLE resume_evaluations DROP COLUMN IF EXISTS market_positioning")
    op.execute("ALTER TABLE resume_evaluations DROP COLUMN IF EXISTS critical_issues")
