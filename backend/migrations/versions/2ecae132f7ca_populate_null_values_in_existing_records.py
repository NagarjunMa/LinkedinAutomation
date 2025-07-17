"""populate_null_values_in_existing_records

Revision ID: 2ecae132f7ca
Revises: 75324d949dc5
Create Date: 2025-07-16 17:08:52.638429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '2ecae132f7ca'
down_revision: Union[str, None] = '75324d949dc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update existing records with NULL values
    # Set applied = False for all existing records
    op.execute(text("UPDATE job_listings SET applied = FALSE WHERE applied IS NULL"))
    
    # Set extracted_date = posted_date for existing records (fallback to current timestamp if posted_date is also NULL)
    op.execute(text("""
        UPDATE job_listings 
        SET extracted_date = COALESCE(posted_date, NOW()) 
        WHERE extracted_date IS NULL
    """))


def downgrade() -> None:
    # Reverse the changes by setting values back to NULL
    op.execute(text("UPDATE job_listings SET applied = NULL WHERE applied = FALSE"))
    op.execute(text("UPDATE job_listings SET extracted_date = NULL"))
