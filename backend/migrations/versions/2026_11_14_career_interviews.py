"""Persist private interview sessions and ordered messages."""
from alembic import op

revision = "2026_11_14_career_interviews"
down_revision = "2026_11_13_career_sources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("""
        CREATE TABLE public.career_interview_sessions (
            user_id varchar(100) NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
            id varchar(36) NOT NULL,
            target_user_id varchar(100),
            target_id varchar(36),
            candidate_stage varchar(32),
            mode varchar(32) NOT NULL,
            status varchar(16) NOT NULL CHECK (status IN ('active', 'paused', 'completed', 'failed')),
            chapter varchar(128) NOT NULL,
            state_version integer NOT NULL,
            prompt_version varchar(128) NOT NULL,
            turns_remaining integer NOT NULL CHECK (turns_remaining >= 0),
            tokens_remaining integer NOT NULL CHECK (tokens_remaining >= 0),
            message_count integer NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            retention_expires_at timestamptz CHECK (retention_expires_at > created_at),
            PRIMARY KEY (user_id, id),
            CONSTRAINT ck_interview_target_owner CHECK (target_user_id = user_id),
            CONSTRAINT ck_interview_session_version CHECK (state_version > 0 AND message_count >= 0),
            CONSTRAINT fk_interview_owned_target FOREIGN KEY (target_user_id, target_id)
                REFERENCES public.career_targets(user_id, id) MATCH FULL ON DELETE SET NULL
        )
    """)
    op.execute("""
        CREATE INDEX ix_interview_session_target ON public.career_interview_sessions (target_user_id, target_id)
    """)
    op.execute("""
        CREATE FUNCTION public.advance_detached_interview() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            NEW.state_version := OLD.state_version + 1;
            NEW.updated_at := GREATEST(OLD.updated_at, clock_timestamp());
            RETURN NEW;
        END;
        $$
    """)
    op.execute("REVOKE ALL ON FUNCTION public.advance_detached_interview() FROM PUBLIC")
    op.execute("""
        CREATE TRIGGER interview_target_detached BEFORE UPDATE OF target_id ON public.career_interview_sessions
        FOR EACH ROW WHEN (OLD.target_id IS NOT NULL AND NEW.target_id IS NULL)
        EXECUTE FUNCTION public.advance_detached_interview()
    """)
    op.execute("""
        CREATE TABLE public.career_interview_messages (
            user_id varchar(100) NOT NULL,
            session_id varchar(36) NOT NULL,
            position integer NOT NULL,
            key varchar(128) NOT NULL,
            role varchar(16) NOT NULL CHECK (role IN ('user', 'assistant')),
            content_ciphertext text NOT NULL,
            processing_status varchar(16) NOT NULL CHECK (processing_status IN ('pending', 'complete', 'interrupted')),
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (user_id, session_id, position),
            CONSTRAINT fk_interview_message_session FOREIGN KEY (user_id, session_id)
                REFERENCES public.career_interview_sessions(user_id, id) ON DELETE CASCADE,
            CONSTRAINT uq_interview_message_retry UNIQUE (user_id, session_id, role, key),
            CONSTRAINT ck_interview_message_bounds CHECK (position >= 1 AND octet_length(content_ciphertext) BETWEEN 100 AND 22000)
        )
    """)
    op.execute("""
        CREATE FUNCTION public.prevent_interview_message_edit() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF (to_jsonb(NEW) - 'processing_status') IS DISTINCT FROM (to_jsonb(OLD) - 'processing_status') THEN
                RAISE EXCEPTION 'Interview messages are immutable' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("REVOKE ALL ON FUNCTION public.prevent_interview_message_edit() FROM PUBLIC")
    op.execute("""
        CREATE TRIGGER interview_messages_immutable BEFORE UPDATE ON public.career_interview_messages
        FOR EACH ROW EXECUTE FUNCTION public.prevent_interview_message_edit()
    """)
    for table, predicate in (
        ("career_interview_sessions", "(retention_expires_at IS NULL OR retention_expires_at > statement_timestamp())"),
        ("career_interview_messages", """EXISTS (
            SELECT FROM public.career_interview_sessions s
            WHERE s.user_id = career_interview_messages.user_id AND s.id = career_interview_messages.session_id
        )"""),
    ):
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON TABLE public.{table} FROM PUBLIC")
        op.execute(f"""
            DO $$
            DECLARE api_role record;
            BEGIN
                FOR api_role IN SELECT oid, rolname FROM pg_roles
                    WHERE rolname IN ('anon', 'authenticated', 'service_role')
                LOOP
                    EXECUTE format('REVOKE ALL ON TABLE public.{table} FROM %I', api_role.rolname);
                    IF has_table_privilege(api_role.oid, 'public.{table}',
                        'SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER') THEN
                        RAISE EXCEPTION 'Effective API role grant remains on {table}';
                    END IF;
                END LOOP;
            END;
            $$
        """)
        op.execute(f"""
            CREATE POLICY own_{table} ON public.{table} FOR SELECT TO authenticated
            USING (user_id = (select auth.uid())::text AND {predicate})
        """)


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("LOCK TABLE public.career_interview_sessions, public.career_interview_messages IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$ BEGIN
            IF current_setting('transaction_isolation') <> 'read committed' THEN
                RAISE EXCEPTION 'Interview schema downgrade requires READ COMMITTED';
            END IF;
            IF EXISTS (SELECT FROM public.career_interview_sessions)
                OR EXISTS (SELECT FROM public.career_interview_messages) THEN
                RAISE EXCEPTION 'Interview data must be preserved before downgrading';
            END IF;
        END; $$;
    """)
    op.execute("DROP TABLE public.career_interview_messages")
    op.execute("DROP TABLE public.career_interview_sessions")
    op.execute("DROP FUNCTION public.prevent_interview_message_edit()")
    op.execute("DROP FUNCTION public.advance_detached_interview()")
