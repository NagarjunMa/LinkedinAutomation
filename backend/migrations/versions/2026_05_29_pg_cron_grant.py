"""Add grant_monthly_credits() Postgres function for pg_cron scheduling.

Replaces the Celery beat task with a pure-SQL function that pg_cron can
schedule. Idempotent per (user, month) via external_ref unique constraint
on credit_ledger.external_ref.

Revision ID: 2026_05_29_pg_cron
Revises: 2026_05_25_jd_links
Create Date: 2026-05-29
"""
from alembic import op


revision = "2026_05_29_pg_cron"
down_revision = "2026_05_25_jd_links"
branch_labels = None
depends_on = None


GRANT_FN_SQL = """
CREATE OR REPLACE FUNCTION grant_monthly_credits(p_amount integer DEFAULT 90)
RETURNS integer AS $$
DECLARE
  v_period text := to_char(NOW() AT TIME ZONE 'UTC', 'YYYY-MM');
  v_count integer := 0;
  v_user record;
  v_balance integer;
  v_ref text;
BEGIN
  FOR v_user IN SELECT user_id FROM users LOOP
    v_ref := 'monthly:' || v_period || ':' || v_user.user_id;

    SELECT COALESCE(SUM(delta), 0) INTO v_balance
    FROM credit_ledger
    WHERE user_id = v_user.user_id;

    BEGIN
      INSERT INTO credit_ledger (id, user_id, delta, reason, balance_after, external_ref, created_at)
      VALUES (
        gen_random_uuid()::text,
        v_user.user_id,
        p_amount,
        'grant',
        v_balance + p_amount,
        v_ref,
        NOW()
      );
      v_count := v_count + 1;
    EXCEPTION WHEN unique_violation THEN
      NULL;
    END;
  END LOOP;

  RETURN v_count;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(GRANT_FN_SQL)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS grant_monthly_credits(integer);")
