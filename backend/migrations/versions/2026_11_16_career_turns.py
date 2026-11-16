"""Record immutable admission and slot metadata on encrypted Career messages."""

from alembic import op

revision = "2026_11_16_career_turns"
down_revision = "2026_11_14_career_lineage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("""
        ALTER TABLE public.career_interview_messages
            ADD COLUMN turn_lease_expires_at timestamptz,
            ADD COLUMN turn_slot varchar(128),
            ADD CONSTRAINT ck_career_turn_message_role CHECK (
                (turn_lease_expires_at IS NULL OR (role = 'user' AND turn_lease_expires_at > created_at))
                AND (turn_slot IS NULL OR role = 'assistant')
            );
        CREATE INDEX ix_career_turn_admission ON public.career_interview_messages (user_id, created_at)
            WHERE turn_lease_expires_at IS NOT NULL;
    """)


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("""
        LOCK TABLE public.career_interview_messages IN ACCESS EXCLUSIVE MODE;
        DO $$ BEGIN
            IF current_setting('transaction_isolation') <> 'read committed' THEN
                RAISE EXCEPTION 'Career turn downgrade requires READ COMMITTED';
            END IF;
            IF EXISTS (SELECT FROM public.career_interview_messages
                WHERE turn_lease_expires_at IS NOT NULL OR turn_slot IS NOT NULL) THEN
                RAISE EXCEPTION 'Career turn admission records must be preserved';
            END IF;
        END; $$;
        DROP INDEX public.ix_career_turn_admission;
        ALTER TABLE public.career_interview_messages
            DROP CONSTRAINT ck_career_turn_message_role,
            DROP COLUMN turn_slot, DROP COLUMN turn_lease_expires_at;
    """)
