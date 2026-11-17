"""Fence interrupted Career turns and record capacity before model dispatch."""
from alembic import op

revision = "2026_11_16_career_recovery"
down_revision = "2026_11_16_career_turns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("""
        ALTER TABLE public.career_interview_messages
            ADD COLUMN turn_admitted_version integer,
            ADD COLUMN turn_candidate_stage varchar(32),
            ADD COLUMN turn_tokens_reserved integer NOT NULL DEFAULT 0,
            ADD COLUMN turn_tokens_dispatched integer NOT NULL DEFAULT 0,
            ADD CONSTRAINT ck_career_turn_recovery CHECK (
                (turn_admitted_version IS NOT NULL OR
                    (turn_candidate_stage IS NULL AND turn_tokens_reserved = 0))
                AND (turn_admitted_version IS NULL OR
                    (turn_admitted_version > 0 AND role = 'user' AND turn_lease_expires_at IS NOT NULL))
                AND turn_tokens_dispatched BETWEEN 0 AND turn_tokens_reserved
            );

        CREATE OR REPLACE FUNCTION public.prevent_interview_message_edit() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF (to_jsonb(NEW) - ARRAY['processing_status', 'turn_tokens_dispatched'])
                IS DISTINCT FROM (to_jsonb(OLD) - ARRAY['processing_status', 'turn_tokens_dispatched'])
                OR NEW.turn_tokens_dispatched < OLD.turn_tokens_dispatched
                OR (NEW.turn_tokens_dispatched <> OLD.turn_tokens_dispatched
                    AND (OLD.processing_status <> 'pending' OR NEW.processing_status <> 'pending')) THEN
                RAISE EXCEPTION 'Interview messages are immutable' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$;
    """)


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("""
        LOCK TABLE public.career_interview_messages IN ACCESS EXCLUSIVE MODE;
        DO $$ BEGIN
            IF current_setting('transaction_isolation') <> 'read committed' THEN
                RAISE EXCEPTION 'Career recovery downgrade requires READ COMMITTED';
            END IF;
            IF EXISTS (SELECT FROM public.career_interview_messages WHERE turn_admitted_version IS NOT NULL) THEN
                RAISE EXCEPTION 'Career turn admission records must be preserved for recovery';
            END IF;
        END; $$;

        CREATE OR REPLACE FUNCTION public.prevent_interview_message_edit() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF (to_jsonb(NEW) - 'processing_status') IS DISTINCT FROM (to_jsonb(OLD) - 'processing_status') THEN
                RAISE EXCEPTION 'Interview messages are immutable' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$;

        ALTER TABLE public.career_interview_messages
            DROP CONSTRAINT ck_career_turn_recovery,
            DROP COLUMN turn_admitted_version, DROP COLUMN turn_candidate_stage,
            DROP COLUMN turn_tokens_reserved, DROP COLUMN turn_tokens_dispatched;
    """)
