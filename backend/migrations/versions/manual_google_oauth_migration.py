"""Update Gmail connection for Google OAuth

Revision ID: manual_google_oauth_migration
Revises: 821de56cfafb
Create Date: 2025-07-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'manual_google_oauth_migration'
down_revision: Union[str, None] = '821de56cfafb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to user_gmail_connections table
    op.add_column('user_gmail_connections', sa.Column('google_user_id', sa.VARCHAR(length=255), nullable=True))
    op.add_column('user_gmail_connections', sa.Column('access_token', sa.TEXT(), nullable=True))
    op.add_column('user_gmail_connections', sa.Column('refresh_token', sa.TEXT(), nullable=True))
    op.add_column('user_gmail_connections', sa.Column('token_expiry', postgresql.TIMESTAMP(), nullable=True))
    
    # Create index for google_user_id
    op.create_index('ix_user_gmail_connections_google_user_id', 'user_gmail_connections', ['google_user_id'], unique=True)
    
    # Make arcade_user_id nullable (we'll keep it for backward compatibility)
    op.alter_column('user_gmail_connections', 'arcade_user_id', nullable=True)


def downgrade() -> None:
    # Remove new columns
    op.drop_index('ix_user_gmail_connections_google_user_id', table_name='user_gmail_connections')
    op.drop_column('user_gmail_connections', 'token_expiry')
    op.drop_column('user_gmail_connections', 'refresh_token')
    op.drop_column('user_gmail_connections', 'access_token')
    op.drop_column('user_gmail_connections', 'google_user_id')
    
    # Make arcade_user_id not nullable again
    op.alter_column('user_gmail_connections', 'arcade_user_id', nullable=False) 