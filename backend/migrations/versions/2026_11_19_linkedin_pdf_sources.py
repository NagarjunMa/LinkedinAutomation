"""Track private PDF objects and encrypted immutable LinkedIn snapshots."""

from alembic import op

revision = "2026_11_19_linkedin_pdf"
down_revision = "2026_11_18_evidence_measurement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("""
        CREATE TABLE public.linkedin_pdf_uploads (
            user_id varchar(100) NOT NULL,
            source_id varchar(36) NOT NULL,
            version integer NOT NULL,
            object_id varchar(36) NOT NULL UNIQUE,
            pdf_sha256 varchar(64) NOT NULL CHECK (length(pdf_sha256) = 64),
            document_ciphertext text NOT NULL,
            state varchar(9) NOT NULL CHECK (state IN ('pending', 'ready', 'deleting', 'canceling')),
            PRIMARY KEY (user_id, source_id, version),
            FOREIGN KEY (user_id, source_id, version)
                REFERENCES public.career_sources (user_id, id, version) ON DELETE RESTRICT
        );
        CREATE TRIGGER linkedin_pdf_content_immutable
            BEFORE UPDATE OF user_id, source_id, version, object_id, pdf_sha256, document_ciphertext
            ON public.linkedin_pdf_uploads FOR EACH ROW EXECUTE FUNCTION public.prevent_career_source_update();
        ALTER TABLE public.linkedin_pdf_uploads ENABLE ROW LEVEL SECURITY;
        CREATE POLICY own_linkedin_pdf_uploads ON public.linkedin_pdf_uploads
            FOR ALL TO authenticated USING (user_id = (select auth.uid())::text)
            WITH CHECK (user_id = (select auth.uid())::text);
        REVOKE ALL ON TABLE public.linkedin_pdf_uploads FROM PUBLIC, authenticated;
        DO $$
        DECLARE api_role record;
        BEGIN
            FOR api_role IN SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'service_role') LOOP
                EXECUTE format('REVOKE ALL ON TABLE public.linkedin_pdf_uploads FROM %I', api_role.rolname);
            END LOOP;
            IF EXISTS (
                SELECT FROM pg_roles WHERE rolname IN ('anon', 'authenticated', 'service_role')
                AND has_table_privilege(oid, 'public.linkedin_pdf_uploads',
                    'SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER')
            ) THEN
                RAISE EXCEPTION 'Effective API role grant remains on LinkedIn PDF uploads';
            END IF;
            IF to_regclass('storage.buckets') IS NOT NULL THEN
                IF EXISTS (SELECT FROM storage.buckets WHERE id = 'resume' AND public) THEN
                    RAISE EXCEPTION 'LinkedIn PDF uploads require a private resume bucket';
                END IF;
            END IF;
            IF to_regclass('storage.objects') IS NOT NULL THEN
                IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid = to_regclass('storage.objects')) THEN
                    RAISE EXCEPTION 'LinkedIn PDF Storage requires row-level security';
                END IF;
                CREATE POLICY prismpro_linkedin_pdf_backend_read ON storage.objects AS RESTRICTIVE
                    FOR SELECT TO anon, authenticated
                    USING (bucket_id IS DISTINCT FROM 'resume'
                           OR split_part(name, '/', 2) NOT LIKE 'linkedin-%');
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("LOCK TABLE public.linkedin_pdf_uploads IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$
        BEGIN
            IF current_setting('transaction_isolation') <> 'read committed' THEN
                RAISE EXCEPTION 'LinkedIn PDF downgrade requires READ COMMITTED';
            END IF;
            IF EXISTS (SELECT FROM public.linkedin_pdf_uploads) THEN
                RAISE EXCEPTION 'LinkedIn PDF objects must be preserved; pause uploads and retain this schema';
            END IF;
            IF to_regclass('storage.objects') IS NOT NULL THEN
                DROP POLICY IF EXISTS prismpro_linkedin_pdf_backend_read ON storage.objects;
            END IF;
        END $$;
    """)
    op.execute("DROP TABLE public.linkedin_pdf_uploads")
