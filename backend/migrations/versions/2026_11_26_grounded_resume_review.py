"""Persist encrypted versioned résumé findings beside legacy evaluations."""

from alembic import op
import sqlalchemy as sa

revision = "2026_11_26_resume_review"
down_revision = "2026_11_19_linkedin_pdf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.add_column("resume_evaluations_v2", sa.Column("grounded_review_ciphertext", sa.Text(), nullable=True))


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("LOCK TABLE resume_evaluations_v2 IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM resume_evaluations_v2 WHERE grounded_review_ciphertext IS NOT NULL) THEN
                RAISE EXCEPTION 'Cannot downgrade while grounded résumé reviews exist';
            END IF;
        END $$;
    """)
    op.drop_column("resume_evaluations_v2", "grounded_review_ciphertext")
