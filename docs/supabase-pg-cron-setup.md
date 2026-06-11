# Supabase pg_cron — Monthly Credit Grant Setup

One-time setup on each Supabase project (dev + production). Replaces the deprecated Celery beat task.

## 1. Enable the pg_cron extension

Supabase Dashboard → **Database** → **Extensions** → search `pg_cron` → toggle ON.

(Alternatively, in the SQL editor: `CREATE EXTENSION IF NOT EXISTS pg_cron;`)

## 2. Apply the Alembic migration

The `grant_monthly_credits()` function is created by Alembic migration `2026_05_29_pg_cron`. After deploying the latest backend image, run:

```bash
cd backend && alembic upgrade head
```

## 3. Schedule the cron job

Run **once** in the Supabase SQL editor:

```sql
SELECT cron.schedule(
  'monthly-credit-grant',
  '0 0 1 * *',           -- midnight UTC, 1st of every month
  $$SELECT grant_monthly_credits(90)$$
);
```

This persists in the `cron.job` table. Verify with:

```sql
SELECT * FROM cron.job WHERE jobname = 'monthly-credit-grant';
```

## 4. Verify a run

After the next scheduled tick (or invoke manually for testing):

```sql
SELECT grant_monthly_credits(90);   -- returns count of users credited
SELECT * FROM credit_ledger WHERE reason = 'grant' ORDER BY created_at DESC LIMIT 5;
```

## Existing-user backfill

Run this once before launch, and rerun safely if needed:

```sql
SELECT grant_monthly_credits(90);
```

The monthly `external_ref` unique constraint prevents duplicate grants for users
who already received the current month's freemium allowance.

## Idempotency model

The function builds `external_ref = 'monthly:YYYY-MM:user_id'` per user per month. The `credit_ledger.external_ref UNIQUE` constraint blocks duplicates — re-running mid-month for any reason is safe (silently skips already-credited users).

## Unschedule (if needed)

```sql
SELECT cron.unschedule('monthly-credit-grant');
```

## Why not Celery

- Removes Redis + worker + beat containers from Railway (cost + ops)
- Single source of truth (function lives in the DB, not split across Python + Redis)
- Idempotency enforced by DB constraint, not Python logic
- No "is the beat scheduler actually running?" question
