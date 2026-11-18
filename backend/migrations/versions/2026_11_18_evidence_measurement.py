"""Store owner-provided measurement metadata without changing legacy evidence payloads."""
from alembic import op
import sqlalchemy as sa

revision = "2026_11_18_evidence_measurement"
down_revision = "2026_11_16_career_recovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.add_column("career_evidence_items", sa.Column("measurement_ciphertext", sa.Text()), schema="public")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("LOCK TABLE public.career_evidence_items IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$ BEGIN
            IF current_setting('transaction_isolation') <> 'read committed' THEN
                RAISE EXCEPTION 'Evidence measurement downgrade requires READ COMMITTED';
            END IF;
            IF EXISTS (SELECT FROM public.career_evidence_items WHERE measurement_ciphertext IS NOT NULL) THEN
                RAISE EXCEPTION 'Career evidence measurements must be preserved before downgrading';
            END IF;
        END; $$;
    """)
    op.drop_column("career_evidence_items", "measurement_ciphertext", schema="public")
