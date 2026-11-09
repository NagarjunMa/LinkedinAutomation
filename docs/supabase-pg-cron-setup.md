# Supabase pg_cron — Monthly Credit Grant Setup

One-time setup on each Supabase project (dev + production). Replaces the deprecated Celery beat task.

## 1. Enable the pg_cron extension

Supabase Dashboard → **Database** → **Extensions** → search `pg_cron` → toggle ON.

(Alternatively, in the SQL editor: `CREATE EXTENSION IF NOT EXISTS pg_cron;`)

## 2. Apply the Alembic migration

The Alembic head `2026_11_09_monthly_credits` sets the default to 90,
restricts browser execution, and updates the command of the existing
`monthly-credit-grant` job. It preserves the job ID, schedule, and active
status. Apply it through the approved pre-deploy migration process, outside
the monthly run window. Confirm the deployment uses the existing job owner
and that the job is idle before applying.

## 3. Schedule the cron job

For a project without the job, first check for the same name across
databases while signed in as the approved scheduler role. Scheduling by
name can replace that role's existing job. If the name is unused, run:

```sql
SELECT cron.schedule(
  'monthly-credit-grant',
  '0 0 1 * *',           -- midnight UTC, 1st of every month
  $$SELECT public.grant_monthly_credits(90)$$
);
```

Verify the single active job, its cadence, and its exact command:

```sql
SELECT jobid, active, schedule, command
FROM cron.job
WHERE jobname = 'monthly-credit-grant' AND database = current_database();
```

Verify the function defaults to 90, is security invoker, and denies both
browser roles:

```sql
SELECT pg_get_function_arguments(oid) AS arguments, prosecdef,
       has_function_privilege('anon', oid, 'EXECUTE') AS anon_execute,
       has_function_privilege('authenticated', oid, 'EXECUTE') AS authenticated_execute
FROM pg_proc
WHERE oid = 'public.grant_monthly_credits(integer)'::regprocedure;
```

## 4. Verify a run

After the next scheduled tick, verify the corrected command succeeded.
Run manual grant tests only in an isolated database with synthetic accounts.

```sql
SELECT r.start_time, r.end_time, r.status
FROM cron.job_run_details r
JOIN cron.job j USING (jobid)
WHERE j.jobname = 'monthly-credit-grant' AND j.database = current_database()
  AND r.command = 'SELECT public.grant_monthly_credits(90)'
ORDER BY r.start_time DESC
LIMIT 5;
```

## Prior grants and recovery

Existing monthly entries retain their original amounts, including any
20-credit grants. Any historical reconciliation requires a separately reviewed
and approved compensating-entry plan.

## Idempotency model

The function locks the user row before calculating the balance, as the
application does. The unique `credit_ledger.external_ref` key uses the UTC
month and user ID, so repeating the job skips accounts already credited
for that period.

## Pause and roll back

Prefer a forward fix. If an operator approves a rollback to an older backend
image, pause the job and verify it is inactive and has no running execution
before changing the function. The prior image requires its own Alembic head
at startup.

```sql
SELECT cron.alter_job(jobid, active := false)
FROM cron.job
WHERE jobname = 'monthly-credit-grant' AND database = current_database();
```

Use the newer image to run `alembic downgrade 2026_09_07_waitlist_retention`.
Confirm that revision, the paused job, and the browser execution restrictions
before redeploying the prior image. The downgrade restores the previous
function body and retains the 90-credit command and existing ledger entries.
Keep the job paused until a reviewed forward fix passes.

## Why not Celery

- Removes Redis + worker + beat containers from Railway (cost + ops)
- Single source of truth (function lives in the DB, not split across Python + Redis)
- Idempotency enforced by DB constraint, not Python logic
- No "is the beat scheduler actually running?" question
