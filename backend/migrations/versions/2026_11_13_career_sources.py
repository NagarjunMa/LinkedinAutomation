"""Add private, owned Career Sources and Career Targets."""
from alembic import op

revision = "2026_11_13_career_sources"
down_revision = "2026_11_11_profile_truncate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("CREATE UNIQUE INDEX uq_resume_documents_owner_id ON public.resume_documents (user_id, id)")
    op.execute("""
        CREATE TABLE public.career_sources (
            user_id varchar(100) NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
            id varchar(36) NOT NULL,
            version integer NOT NULL CONSTRAINT ck_career_sources_positive_version CHECK (version >= 1),
            kind varchar(32) NOT NULL CONSTRAINT ck_career_sources_kind CHECK (
                kind IN ('resume', 'linkedin_profile_pdf', 'candidate_introduction',
                         'interview_message', 'public_proof_link', 'job_description')
            ),
            content text NOT NULL CONSTRAINT ck_career_sources_content_length CHECK (char_length(content) <= 100000),
            content_sha256 varchar(64) NOT NULL CONSTRAINT ck_career_sources_hash CHECK (length(content_sha256) = 64),
            resume_document_id varchar,
            extraction_version varchar(128),
            created_at timestamptz NOT NULL DEFAULT now(),
            retention_expires_at timestamptz,
            PRIMARY KEY (user_id, id, version),
            CONSTRAINT uq_career_sources_ref_kind UNIQUE (user_id, id, version, kind),
            CONSTRAINT ck_career_sources_resume CHECK ((kind = 'resume') = (resume_document_id IS NOT NULL)),
            CONSTRAINT ck_career_sources_retention CHECK (retention_expires_at > created_at),
            CONSTRAINT fk_career_sources_owned_resume FOREIGN KEY (user_id, resume_document_id)
                REFERENCES public.resume_documents(user_id, id) ON DELETE CASCADE
        )
    """)
    op.execute("CREATE INDEX ix_career_sources_owned_resume ON public.career_sources (user_id, resume_document_id)")
    op.execute("""
        CREATE TABLE public.career_targets (
            user_id varchar(100) NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
            id varchar(36) NOT NULL,
            role_family varchar(200) NOT NULL,
            seniority varchar(200) NOT NULL,
            location varchar(200),
            desired_work jsonb NOT NULL,
            exclusions jsonb NOT NULL,
            jd_user_id varchar(100),
            jd_source_id varchar(36),
            jd_source_version integer,
            jd_source_kind varchar(32),
            status varchar(8) NOT NULL DEFAULT 'active' CONSTRAINT ck_career_targets_status CHECK (
                status IN ('active', 'archived')
            ),
            PRIMARY KEY (user_id, id),
            CONSTRAINT ck_career_targets_jd_owner CHECK (jd_user_id = user_id AND jd_source_kind = 'job_description'),
            CONSTRAINT fk_career_targets_owned_jd FOREIGN KEY (jd_user_id, jd_source_id, jd_source_version, jd_source_kind)
                REFERENCES public.career_sources(user_id, id, version, kind) MATCH FULL ON DELETE SET NULL
        )
    """)
    op.execute("CREATE INDEX ix_career_targets_jd ON public.career_targets (jd_user_id, jd_source_id, jd_source_version)")
    op.execute("""
        CREATE FUNCTION public.prevent_career_source_update() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Career source snapshots are immutable' USING ERRCODE = '23514';
        END;
        $$
    """)
    op.execute("REVOKE ALL ON FUNCTION public.prevent_career_source_update() FROM PUBLIC")
    op.execute("""
        CREATE TRIGGER career_sources_immutable BEFORE UPDATE ON public.career_sources
        FOR EACH ROW EXECUTE FUNCTION public.prevent_career_source_update()
    """)
    for table in ("career_sources", "career_targets"):
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON TABLE public.{table} FROM PUBLIC, authenticated")
        op.execute(f"""
            DO $$
            DECLARE
                api_role record;
            BEGIN
                FOR api_role IN SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'service_role')
                LOOP
                    EXECUTE format('REVOKE ALL ON TABLE public.{table} FROM %I', api_role.rolname);
                END LOOP;
                IF EXISTS (
                    SELECT FROM pg_roles WHERE rolname IN ('anon', 'authenticated', 'service_role')
                    AND has_table_privilege(oid, 'public.{table}',
                        'SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER')
                ) THEN
                    RAISE EXCEPTION 'Effective API role grant remains on {table}';
                END IF;
            END;
            $$
        """)
        op.execute(f"""
            CREATE POLICY own_{table} ON public.{table} FOR ALL TO authenticated
            USING (user_id = (select auth.uid())::text)
            WITH CHECK (user_id = (select auth.uid())::text)
        """)


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("LOCK TABLE public.career_sources, public.career_targets IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$
        BEGIN
            IF current_setting('transaction_isolation') <> 'read committed' THEN
                RAISE EXCEPTION 'Career schema downgrade requires READ COMMITTED';
            END IF;
            IF EXISTS (SELECT FROM public.career_sources) OR EXISTS (SELECT FROM public.career_targets) THEN
                RAISE EXCEPTION 'Career data must be preserved before downgrading';
            END IF;
        END;
        $$
    """)
    op.execute("DROP TABLE public.career_targets")
    op.execute("DROP TABLE public.career_sources")
    op.execute("DROP FUNCTION public.prevent_career_source_update()")
    op.execute("DROP INDEX public.uq_resume_documents_owner_id")
