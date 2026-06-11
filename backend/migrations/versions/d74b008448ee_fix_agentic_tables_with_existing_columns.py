"""fix_agentic_tables_with_existing_columns

Revision ID: d74b008448ee
Revises: 0f5496e5b76e
Create Date: 2025-09-10 13:49:49.040789

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'd74b008448ee'
down_revision: Union[str, None] = '0f5496e5b76e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The previous revision already creates these tables. This generated
    # follow-up attempted to create them again, which breaks clean migrations.
    pass


def downgrade() -> None:
    pass
