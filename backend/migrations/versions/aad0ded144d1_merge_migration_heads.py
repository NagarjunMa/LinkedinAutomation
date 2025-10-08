"""merge migration heads

Revision ID: aad0ded144d1
Revises: 6422cebae43e, add_resume_status_locking
Create Date: 2025-10-06 22:55:47.079574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aad0ded144d1'
down_revision: Union[str, None] = ('6422cebae43e', 'add_resume_status_locking')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
