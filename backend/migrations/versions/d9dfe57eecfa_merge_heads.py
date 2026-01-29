"""merge_heads

Revision ID: d9dfe57eecfa
Revises: cleanup_unused_tables, d54bd991f286
Create Date: 2026-01-28 14:42:56.668244

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9dfe57eecfa'
down_revision: Union[str, None] = ('cleanup_unused_tables', 'd54bd991f286')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
