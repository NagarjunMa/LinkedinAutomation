"""Persist owner-scoped Career Evidence revisions and decisions."""
from alembic import op

revision = "2026_11_14_career_evidence"
down_revision = "2026_11_14_career_interviews"
branch_labels = None
depends_on = None

TABLES = ("career_evidence_items", "career_evidence_sources", "career_evidence_decisions")


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("""
        CREATE TABLE public.career_evidence_items (
            user_id varchar(100) NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
            evidence_id varchar(36) NOT NULL,
            revision integer NOT NULL CHECK (revision >= 1),
            lifecycle varchar(16) NOT NULL CHECK (lifecycle IN
                ('proposed', 'confirmed', 'rejected', 'contradicted', 'private', 'unavailable')),
            is_private boolean NOT NULL CHECK (lifecycle <> 'private' OR is_private),
            source_count integer NOT NULL CHECK (source_count BETWEEN 1 AND 20),
            ciphertext text NOT NULL,
            PRIMARY KEY (user_id, evidence_id, revision)
        );
        CREATE TABLE public.career_evidence_sources (
            user_id varchar(100) NOT NULL,
            evidence_id varchar(36) NOT NULL,
            revision integer NOT NULL,
            position integer NOT NULL CHECK (position BETWEEN 1 AND 20),
            source_id varchar(36) NOT NULL,
            source_version integer NOT NULL,
            PRIMARY KEY (user_id, evidence_id, revision, position),
            FOREIGN KEY (user_id, evidence_id, revision)
                REFERENCES public.career_evidence_items ON DELETE CASCADE,
            FOREIGN KEY (user_id, source_id, source_version)
                REFERENCES public.career_sources DEFERRABLE INITIALLY DEFERRED
        );
        CREATE INDEX ix_evidence_owned_source ON public.career_evidence_sources (user_id, source_id, source_version);
        CREATE TABLE public.career_evidence_decisions (
            user_id varchar(100) NOT NULL,
            evidence_id varchar(36) NOT NULL,
            resulting_revision integer NOT NULL CHECK (resulting_revision > 1),
            action varchar(24) NOT NULL CHECK (action IN
                ('confirm', 'edit', 'reject', 'mark_private', 'mark_unavailable', 'resolve_contradiction')),
            decided_at timestamptz NOT NULL,
            reason_ciphertext text,
            PRIMARY KEY (user_id, evidence_id, resulting_revision),
            FOREIGN KEY (user_id, evidence_id, resulting_revision)
                REFERENCES public.career_evidence_items ON DELETE CASCADE
        );
        CREATE FUNCTION public.prevent_career_evidence_edit() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Career evidence history is immutable' USING ERRCODE = '23514';
        END;
        $$;
        REVOKE ALL ON FUNCTION public.prevent_career_evidence_edit() FROM PUBLIC;

        CREATE FUNCTION public.purge_deleted_source_evidence() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE affected record;
        BEGIN
            IF NOT EXISTS (SELECT FROM deleted_sources) THEN
                RETURN NULL;
            END IF;
            FOR affected IN
                SELECT DISTINCT l.user_id, l.evidence_id
                FROM public.career_evidence_sources l
                JOIN deleted_sources s
                  ON (l.user_id, l.source_id, l.source_version) = (s.user_id, s.id, s.version)
                ORDER BY l.user_id, l.evidence_id
            LOOP
                -- Serialize with decisions at revision one before deleting the history.
                PERFORM FROM public.career_evidence_items
                WHERE user_id = affected.user_id AND evidence_id = affected.evidence_id AND revision = 1
                FOR UPDATE;
                DELETE FROM public.career_evidence_items
                WHERE user_id = affected.user_id AND evidence_id = affected.evidence_id;
            END LOOP;
            RETURN NULL;
        END;
        $$;
        REVOKE ALL ON FUNCTION public.purge_deleted_source_evidence() FROM PUBLIC;
        CREATE TRIGGER purge_deleted_source_evidence AFTER DELETE ON public.career_sources
        REFERENCING OLD TABLE AS deleted_sources
        FOR EACH STATEMENT EXECUTE FUNCTION public.purge_deleted_source_evidence();
    """)
    for table in TABLES:
        # Private text and all decisions flow through the backend role.
        op.execute(f"""
            ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;
            CREATE POLICY own_{table} ON public.{table} FOR SELECT TO authenticated
            USING (user_id = (select auth.uid())::text);
            CREATE TRIGGER prevent_career_evidence_edit BEFORE UPDATE ON public.{table}
            FOR EACH ROW EXECUTE FUNCTION public.prevent_career_evidence_edit();
            REVOKE ALL ON TABLE public.{table} FROM PUBLIC;
            DO $$ DECLARE api_role record;
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
            END; $$;
        """)


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("LOCK TABLE public.career_evidence_items, public.career_evidence_sources, "
               "public.career_evidence_decisions IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$ BEGIN
            IF current_setting('transaction_isolation') <> 'read committed' THEN
                RAISE EXCEPTION 'Evidence downgrade requires READ COMMITTED';
            END IF;
            IF EXISTS (SELECT FROM public.career_evidence_items) THEN
                RAISE EXCEPTION 'Career evidence must be preserved before downgrading';
            END IF;
        END; $$;
        DROP TRIGGER purge_deleted_source_evidence ON public.career_sources;
        DROP FUNCTION public.purge_deleted_source_evidence();
        DROP TABLE public.career_evidence_decisions, public.career_evidence_sources, public.career_evidence_items;
        DROP FUNCTION public.prevent_career_evidence_edit();
    """)
