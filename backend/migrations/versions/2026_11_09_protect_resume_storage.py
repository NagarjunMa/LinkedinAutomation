"""Enforce backend-only writes for the private resume bucket."""

from alembic import op


revision = "2026_11_09_resume_storage"
down_revision = "2026_11_09_user_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF to_regclass('storage.objects') IS NULL THEN
                RETURN;
            END IF;
            IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid = 'storage.objects'::regclass) THEN
                RAISE EXCEPTION 'Resume Storage requires row-level security';
            END IF;

            DROP POLICY IF EXISTS prismpro_resume_backend_insert ON storage.objects;
            CREATE POLICY prismpro_resume_backend_insert ON storage.objects AS RESTRICTIVE
                FOR INSERT TO anon, authenticated
                WITH CHECK (bucket_id IS DISTINCT FROM 'resume');

            DROP POLICY IF EXISTS prismpro_resume_backend_update ON storage.objects;
            CREATE POLICY prismpro_resume_backend_update ON storage.objects AS RESTRICTIVE
                FOR UPDATE TO anon, authenticated
                USING (bucket_id IS DISTINCT FROM 'resume')
                WITH CHECK (bucket_id IS DISTINCT FROM 'resume');

            DROP POLICY IF EXISTS prismpro_resume_backend_delete ON storage.objects;
            CREATE POLICY prismpro_resume_backend_delete ON storage.objects AS RESTRICTIVE
                FOR DELETE TO anon, authenticated
                USING (bucket_id IS DISTINCT FROM 'resume');

            DROP POLICY IF EXISTS prismpro_resume_backend_read_boundary ON storage.objects;
            CREATE POLICY prismpro_resume_backend_read_boundary ON storage.objects AS RESTRICTIVE
                FOR SELECT TO anon, authenticated
                USING (bucket_id IS DISTINCT FROM 'resume'
                       OR (current_user = 'authenticated'
                           AND (storage.foldername(name))[1] = (select auth.uid())::text));

            DROP POLICY IF EXISTS prismpro_resume_backend_owner_read ON storage.objects;
            CREATE POLICY prismpro_resume_backend_owner_read ON storage.objects
                FOR SELECT TO authenticated
                USING (bucket_id = 'resume'
                       AND (storage.foldername(name))[1] = (select auth.uid())::text);
        END
        $$;
    """)


def downgrade() -> None:
    # An application rollback must not reopen direct writes to private files.
    pass
