"""merge_heads

Revision ID: d54bd991f286
Revises: email_scanning_001, e6c7d60b7492
Create Date: 2025-10-20 19:29:14.190079

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd54bd991f286'
down_revision: Union[str, None] = ('email_scanning_001', 'e6c7d60b7492')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
