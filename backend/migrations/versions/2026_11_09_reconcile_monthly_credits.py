"""Align scheduled credit grants with the 90-credit policy and ledger lock."""

from alembic import op
from alembic.script import ScriptDirectory


revision = "2026_11_09_monthly_credits"
down_revision = "2026_09_07_waitlist_retention"
branch_labels = None
depends_on = None


GRANT_FN_SQL = """
CREATE OR REPLACE FUNCTION public.grant_monthly_credits(p_amount integer DEFAULT 90)
RETURNS integer
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog
AS $grant$
DECLARE
    grant_period text := to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM');
    grant_count integer := 0;
    account_id text;
    current_balance integer;
    monthly_ref text;
BEGIN
    IF p_amount IS NULL OR p_amount <= 0 THEN
        RAISE EXCEPTION 'Credit amount must be positive' USING ERRCODE = '22023';
    END IF;
    IF current_setting('transaction_isolation') <> 'read committed' THEN
        RAISE EXCEPTION 'Credit grants require READ COMMITTED' USING ERRCODE = '25000';
    END IF;

    -- Share the application's users-row lock before reading the ledger balance.
    FOR account_id IN
        SELECT u.user_id
        FROM public.users u
        WHERE NOT EXISTS (
            SELECT 1 FROM public.credit_ledger
            WHERE external_ref = 'monthly:' || grant_period || ':' || u.user_id
        )
        ORDER BY u.user_id
        FOR UPDATE OF u
    LOOP
        monthly_ref := 'monthly:' || grant_period || ':' || account_id;
        SELECT COALESCE(SUM(delta), 0) INTO current_balance
        FROM public.credit_ledger
        WHERE user_id = account_id;

        INSERT INTO public.credit_ledger
            (id, user_id, delta, reason, balance_after, external_ref, created_at)
        VALUES (gen_random_uuid()::text, account_id, p_amount, 'grant',
                current_balance + p_amount, monthly_ref, now())
        ON CONFLICT (external_ref) DO NOTHING;

        IF FOUND THEN
            grant_count := grant_count + 1;
        END IF;
    END LOOP;

    RETURN grant_count;
END;
$grant$;
"""


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(GRANT_FN_SQL)
    op.execute("REVOKE EXECUTE ON FUNCTION public.grant_monthly_credits(integer) FROM PUBLIC")
    op.execute(
        """
        DO $migration$
        DECLARE
            browser_role name;
            monthly_job_id bigint;
        BEGIN
            FOR browser_role IN
                SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')
            LOOP
                EXECUTE format(
                    'REVOKE EXECUTE ON FUNCTION public.grant_monthly_credits(integer) FROM %I',
                    browser_role
                );
                IF has_function_privilege(browser_role, 'public.grant_monthly_credits(integer)', 'EXECUTE') THEN
                    RAISE EXCEPTION 'Role % retains monthly credit grant execution', browser_role;
                END IF;
            END LOOP;

            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
                monthly_job_id := (
                    SELECT jobid FROM cron.job
                    WHERE jobname = 'monthly-credit-grant' AND database = current_database()
                );
                IF monthly_job_id IS NOT NULL THEN
                    PERFORM cron.alter_job(
                        monthly_job_id,
                        command := 'SELECT public.grant_monthly_credits(90)'
                    );
                END IF;
            END IF;
        END;
        $migration$;
        """
    )


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    # Keep the corrected schedule and access restrictions across application rollback.
    scripts = ScriptDirectory.from_config(op.get_context().config)
    previous = scripts.get_revision("2026_05_29_pg_cron").module.GRANT_FN_SQL
    op.execute(previous.replace("FUNCTION grant_monthly_credits(", "FUNCTION public.grant_monthly_credits("))
    op.execute("ALTER FUNCTION public.grant_monthly_credits(integer) SET search_path = public")
