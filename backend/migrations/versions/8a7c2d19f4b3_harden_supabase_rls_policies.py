"""harden Supabase RLS policies

Revision ID: 8a7c2d19f4b3
Revises: f2b8d1c9a710
Create Date: 2026-06-30 00:00:00.000000
"""
from alembic import op


revision = "8a7c2d19f4b3"
down_revision = "f2b8d1c9a710"
branch_labels = None
depends_on = None


USER_OWNED_TABLES = (
    "users",
    "user_profiles",
    "job_applications",
    "profile_info",
    "profile_settings",
    "profile_change_history",
    "resumes",
)


ACTIVE_USER_OWNED_TABLES = (
    "jd_evaluations",
    "resume_documents",
    "resume_evaluations_v2",
    "resume_exports",
)


def _drop_policy(table: str, policy: str, schema: str = "public") -> None:
    op.execute(f'DROP POLICY IF EXISTS "{policy}" ON {schema}.{table}')


def _enable_rls(table: str, schema: str = "public") -> None:
    op.execute(f"ALTER TABLE {schema}.{table} ENABLE ROW LEVEL SECURITY")


def _own_user_id_policy(table: str) -> None:
    _drop_policy(table, f"own_{table}")
    op.execute(
        f"""
        CREATE POLICY own_{table}
        ON public.{table}
        FOR ALL
        TO authenticated
        USING (user_id::text = (select auth.uid())::text)
        WITH CHECK (user_id::text = (select auth.uid())::text)
        """
    )


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                CREATE ROLE authenticated;
            END IF;
        END $$;
        """
    )
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_proc p
                JOIN pg_namespace n ON n.oid = p.pronamespace
                WHERE n.nspname = 'auth' AND p.proname = 'uid'
            ) THEN
                CREATE FUNCTION auth.uid()
                RETURNS uuid
                LANGUAGE sql
                STABLE
                AS 'select null::uuid';
            END IF;
        END $$;
        """
    )

    for table in USER_OWNED_TABLES:
        _enable_rls(table)
        _own_user_id_policy(table)

    for table in ACTIVE_USER_OWNED_TABLES:
        _enable_rls(table)
        _own_user_id_policy(table)

    _drop_policy("resume_evaluations_v2", "own_resume_evaluations")

    _enable_rls("resume_evaluations")
    _drop_policy("resume_evaluations", "own_resume_evaluations")
    op.execute(
        """
        CREATE POLICY own_resume_evaluations
        ON public.resume_evaluations
        FOR ALL
        TO authenticated
        USING (
            EXISTS (
                SELECT 1
                FROM public.resumes
                WHERE resumes.id = resume_evaluations.resume_id
                  AND resumes.user_id::text = (select auth.uid())::text
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1
                FROM public.resumes
                WHERE resumes.id = resume_evaluations.resume_id
                  AND resumes.user_id::text = (select auth.uid())::text
            )
        )
        """
    )

    _enable_rls("resume_versions")
    _drop_policy("resume_versions", "own_resume_versions")
    op.execute(
        """
        CREATE POLICY own_resume_versions
        ON public.resume_versions
        FOR ALL
        TO authenticated
        USING (
            EXISTS (
                SELECT 1
                FROM public.resume_documents
                WHERE resume_documents.id = resume_versions.resume_document_id
                  AND resume_documents.user_id::text = (select auth.uid())::text
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1
                FROM public.resume_documents
                WHERE resume_documents.id = resume_versions.resume_document_id
                  AND resume_documents.user_id::text = (select auth.uid())::text
            )
        )
        """
    )

    _enable_rls("job_listings")
    _drop_policy("job_listings", "authenticated_can_read_job_listings")
    op.execute(
        """
        CREATE POLICY authenticated_can_read_job_listings
        ON public.job_listings
        FOR SELECT
        TO authenticated
        USING (true)
        """
    )

    _enable_rls("alembic_version")

    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('storage.objects') IS NOT NULL THEN
                DROP POLICY IF EXISTS update_own_files ON storage.objects;
                CREATE POLICY update_own_files
                ON storage.objects
                FOR UPDATE
                TO authenticated
                USING (
                    bucket_id = 'resume'
                    AND (storage.foldername(name))[1] = (select auth.uid())::text
                )
                WITH CHECK (
                    bucket_id = 'resume'
                    AND (storage.foldername(name))[1] = (select auth.uid())::text
                );
            END IF;
        END $$;
        """
    )

    op.execute(
        "ALTER FUNCTION public.grant_monthly_credits(p_amount integer) "
        "SET search_path = public"
    )


def downgrade() -> None:
    op.execute("ALTER FUNCTION public.grant_monthly_credits(p_amount integer) RESET search_path")
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('storage.objects') IS NOT NULL THEN
                DROP POLICY IF EXISTS update_own_files ON storage.objects;
            END IF;
        END $$;
        """
    )
    _drop_policy("job_listings", "authenticated_can_read_job_listings")
    _drop_policy("resume_versions", "own_resume_versions")
    _drop_policy("resume_evaluations", "own_resume_evaluations")

    for table in ACTIVE_USER_OWNED_TABLES:
        _drop_policy(table, f"own_{table}")
    for table in USER_OWNED_TABLES:
        _drop_policy(table, f"own_{table}")
