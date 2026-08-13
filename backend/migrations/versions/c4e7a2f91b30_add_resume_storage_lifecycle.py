"""add resume storage lifecycle

Revision ID: c4e7a2f91b30
Revises: 8a7c2d19f4b3
Create Date: 2026-08-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c4e7a2f91b30"
down_revision = "8a7c2d19f4b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resume_documents",
        sa.Column(
            "storage_status",
            sa.String(length=16),
            nullable=False,
            server_default="ready",
        ),
    )
    op.create_check_constraint(
        "ck_resume_documents_storage_status",
        "resume_documents",
        "storage_status IN ('pending', 'ready', 'deleting')",
    )
    op.create_index(
        "ix_resume_documents_user_storage_status",
        "resume_documents",
        ["user_id", "storage_status"],
        unique=False,
    )
    op.execute('DROP POLICY IF EXISTS "own_resume_documents" ON public.resume_documents')
    op.execute(
        """
        CREATE POLICY own_resume_documents
        ON public.resume_documents
        FOR SELECT
        TO authenticated
        USING (user_id::text = (select auth.uid())::text)
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('storage.objects') IS NOT NULL
               AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                REVOKE INSERT, UPDATE, DELETE ON storage.objects FROM authenticated;
                DROP POLICY IF EXISTS update_own_files ON storage.objects;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('storage.objects') IS NOT NULL
               AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                GRANT INSERT, UPDATE, DELETE ON storage.objects TO authenticated;
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
    op.execute('DROP POLICY IF EXISTS "own_resume_documents" ON public.resume_documents')
    op.execute(
        """
        CREATE POLICY own_resume_documents
        ON public.resume_documents
        FOR ALL
        TO authenticated
        USING (user_id::text = (select auth.uid())::text)
        WITH CHECK (user_id::text = (select auth.uid())::text)
        """
    )
    op.drop_index(
        "ix_resume_documents_user_storage_status",
        table_name="resume_documents",
    )
    op.drop_constraint(
        "ck_resume_documents_storage_status",
        "resume_documents",
        type_="check",
    )
    op.drop_column("resume_documents", "storage_status")
