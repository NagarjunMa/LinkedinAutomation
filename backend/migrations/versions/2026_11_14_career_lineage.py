"""Persist private career run and artifact lineage metadata."""

from alembic import op

revision = "2026_11_14_career_lineage"
down_revision = "2026_11_14_career_evidence"
branch_labels = None
depends_on = None

TABLES = (
    "career_interview_runs", "career_generated_artifacts", "career_artifact_runs",
    "career_artifact_claims", "career_proof_artifacts",
)


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("""
        CREATE TABLE public.career_interview_runs (
            user_id varchar(100) NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
            id varchar(36) NOT NULL,
            session_id varchar(36),
            ciphertext text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (user_id, id),
            FOREIGN KEY (user_id, session_id) REFERENCES public.career_interview_sessions ON DELETE CASCADE
        );
        CREATE INDEX ix_career_run_session ON public.career_interview_runs (user_id, session_id);
        CREATE TABLE public.career_generated_artifacts (
            user_id varchar(100) NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
            id varchar(36) NOT NULL,
            version integer NOT NULL CHECK (version >= 1),
            kind varchar(32) NOT NULL CHECK (kind IN (
                'resume', 'linkedin_recommendations', 'interview_story_bank', 'hiring_manager_brief', 'learning_plan'
            )),
            target_id varchar(36),
            requires_run boolean NOT NULL,
            generator jsonb NOT NULL,
            link_count integer NOT NULL CHECK (link_count BETWEEN 1 AND 500),
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (user_id, id, version),
            FOREIGN KEY (user_id, target_id) REFERENCES public.career_targets ON DELETE CASCADE
        );
        CREATE INDEX ix_career_artifact_target ON public.career_generated_artifacts (user_id, target_id);
        CREATE TABLE public.career_artifact_runs (
            user_id varchar(100) NOT NULL,
            artifact_id varchar(36) NOT NULL,
            artifact_version integer NOT NULL,
            run_id varchar(36) NOT NULL,
            PRIMARY KEY (user_id, artifact_id, artifact_version),
            FOREIGN KEY (user_id, artifact_id, artifact_version)
                REFERENCES public.career_generated_artifacts ON DELETE CASCADE,
            FOREIGN KEY (user_id, run_id) REFERENCES public.career_interview_runs ON DELETE CASCADE
        );
        CREATE INDEX ix_career_artifact_run ON public.career_artifact_runs (user_id, run_id);
        CREATE TABLE public.career_artifact_claims (
            user_id varchar(100) NOT NULL,
            artifact_id varchar(36) NOT NULL,
            artifact_version integer NOT NULL,
            claim_id varchar(128) NOT NULL,
            evidence_id varchar(36) NOT NULL,
            evidence_revision integer NOT NULL,
            PRIMARY KEY (user_id, artifact_id, artifact_version, claim_id, evidence_id),
            FOREIGN KEY (user_id, artifact_id, artifact_version)
                REFERENCES public.career_generated_artifacts ON DELETE CASCADE,
            FOREIGN KEY (user_id, evidence_id, evidence_revision)
                REFERENCES public.career_evidence_items ON DELETE CASCADE
        );
        CREATE INDEX ix_career_claim_evidence ON public.career_artifact_claims (user_id, evidence_id, evidence_revision);
        CREATE TABLE public.career_proof_artifacts (
            user_id varchar(100) NOT NULL,
            id varchar(36) NOT NULL,
            source_id varchar(36) NOT NULL,
            source_version integer NOT NULL,
            source_kind varchar(32) NOT NULL DEFAULT 'public_proof_link' CHECK (source_kind = 'public_proof_link'),
            evidence_id varchar(36) NOT NULL,
            evidence_revision integer NOT NULL,
            metadata jsonb NOT NULL,
            PRIMARY KEY (user_id, id),
            FOREIGN KEY (user_id, source_id, source_version, source_kind)
                REFERENCES public.career_sources (user_id, id, version, kind) ON DELETE CASCADE,
            FOREIGN KEY (user_id, evidence_id, evidence_revision)
                REFERENCES public.career_evidence_items ON DELETE CASCADE
        );
        CREATE INDEX ix_career_proof_source ON public.career_proof_artifacts
            (user_id, source_id, source_version, source_kind);
        CREATE INDEX ix_career_proof_evidence ON public.career_proof_artifacts (user_id, evidence_id, evidence_revision);
    """)
    for table in TABLES:
        op.execute(f"""
            ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;
            CREATE POLICY own_{table} ON public.{table} FOR SELECT TO authenticated
            USING (user_id = (select auth.uid())::text);
            CREATE TRIGGER prevent_career_lineage_edit BEFORE UPDATE ON public.{table}
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
    tables = ", ".join(f"public.{table}" for table in reversed(TABLES))
    op.execute(f"LOCK TABLE {tables} IN ACCESS EXCLUSIVE MODE")
    populated = " OR ".join(f"EXISTS (SELECT FROM public.{table})" for table in TABLES)
    op.execute(f"""
        DO $$ BEGIN
            IF current_setting('transaction_isolation') <> 'read committed' THEN
                RAISE EXCEPTION 'Career lineage downgrade requires READ COMMITTED';
            END IF;
            IF {populated} THEN
                RAISE EXCEPTION 'Career lineage must be preserved before downgrading';
            END IF;
        END; $$;
        DROP TABLE {tables};
    """)
