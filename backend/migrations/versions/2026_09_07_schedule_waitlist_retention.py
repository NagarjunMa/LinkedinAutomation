"""Schedule daily deletion of expired waitlist records when pg_cron is enabled.

Revision ID: 2026_09_07_waitlist_retention
Revises: 2026_09_06_waitlist
Create Date: 2026-09-07
"""

from alembic import op


revision = "2026_09_07_waitlist_retention"
down_revision = "2026_09_06_waitlist"
branch_labels = None
depends_on = None


JOB_NAME = "prismpro-waitlist-retention-daily"
JOB_SCHEDULE = "17 3 * * *"
JOB_COMMAND = (
    "DELETE FROM public.waitlist_entries "
    "WHERE retention_expires_at <= CURRENT_TIMESTAMP"
)


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    # Supabase Cron is optional at migration time. When pg_cron is already
    # enabled, scheduling with the same name safely replaces the existing job.
    # If it is not enabled, the release verifier keeps deployment blocked until
    # an operator enables Cron and reruns this exact schedule statement.
    op.execute(
        f"""
        DO $migration$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'pg_cron'
            ) THEN
                PERFORM cron.schedule(
                    '{JOB_NAME}',
                    '{JOB_SCHEDULE}',
                    $job${JOB_COMMAND}$job$
                );
            END IF;
        END
        $migration$;
        """
    )


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(
        f"""
        DO $migration$
        DECLARE
            retention_job_id bigint;
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'pg_cron'
            ) THEN
                FOR retention_job_id IN
                    SELECT jobid FROM cron.job WHERE jobname = '{JOB_NAME}'
                LOOP
                    PERFORM cron.unschedule(retention_job_id);
                END LOOP;
            END IF;
        END
        $migration$;
        """
    )
