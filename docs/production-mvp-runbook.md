# Prism Pro MVP Production Runbook

This is the authoritative launch checklist for the 50-100 user MVP. Older
planning documents are historical references and should not be used as launch
instructions.

## Deployment Model

- Billing is disabled: `ENABLE_BILLING=false`.
- Stripe environment variables are optional until billing is enabled.
- Freemium allowance is `FREEMIUM_MONTHLY_CREDITS=90`.
- Supabase Storage uses one private bucket: `resume`.
- Railway backend is assumed to run as a single instance for MVP.
- Redis or platform-backed distributed rate limiting is required before
  multi-instance backend deployment or broader traffic.

## Backend Environment

Set these in Railway for the backend service:

```bash
ENVIRONMENT=production
SQLALCHEMY_DATABASE_URI=postgresql://...
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
OPENAI_API_KEY=<openai-key>
CORS_ORIGINS=https://www.prismpro.live
PUBLIC_FRONTEND_ORIGIN=https://www.prismpro.live
PRISM_PRO_PUBLIC_PREVIEW_ONLY=true
BACKEND_REPLICA_COUNT=1
WEB_CONCURRENCY=1
SECRET_KEY=<32+ character secret>
ADMIN_USER_IDS=<comma-separated-supabase-user-ids>
SUPABASE_STORAGE_BUCKET=resume
FREEMIUM_MONTHLY_CREDITS=90
ENABLE_BILLING=false
```

Do not put `SUPABASE_SERVICE_ROLE_KEY` in any frontend environment.

## Frontend Environment

Set these in Railway/Vercel for the frontend service:

```bash
NEXT_PUBLIC_API_URL=https://api.prismpro.live
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
NEXT_PUBLIC_SITE_URL=https://www.prismpro.live
NEXT_PUBLIC_FRONTEND_URL=https://www.prismpro.live
PRISM_PRO_PUBLIC_PREVIEW_ONLY=true
```

The backend refuses to start in production preview mode if the CORS allowlist
contains another origin, either declared process count is not one, or the
preview flag is disabled. Railway horizontal scaling must also be fixed at one
replica until the limiter is moved to a shared store or the edge.

## Public-preview release verification (PRI-5)

### Supabase Auth lockdown

In the PrismPro Supabase project, open **Authentication → General
Configuration** and disable both:

- **Allow new users to sign up**
- **Allow anonymous sign-ins**

The release verifier reads these settings through the Supabase Management API;
it does not attempt to create a real auth user. Use a short-lived personal
access token with Auth config read access and never commit it.

### Waitlist retention schedule

Enable Supabase Cron before applying the latest Alembic migration. Migration
`2026_09_07_waitlist_retention` creates or replaces a daily 03:17 UTC job named
`prismpro-waitlist-retention-daily`. It deletes only rows whose explicit
`retention_expires_at` deadline has passed.

If Cron was enabled after the migration, run this once in the SQL editor:

```sql
select cron.schedule(
  'prismpro-waitlist-retention-daily',
  '17 3 * * *',
  $$delete from public.waitlist_entries
    where retention_expires_at <= current_timestamp$$
);
```

Verify the job and recent execution history:

```sql
select jobid, schedule, command, active
from cron.job
where jobname = 'prismpro-waitlist-retention-daily';

select status, return_message, start_time, end_time
from cron.job_run_details
where jobid = (
  select jobid from cron.job
  where jobname = 'prismpro-waitlist-retention-daily'
)
order by start_time desc
limit 10;
```

Do not clear the retention gate until `cron.job_run_details` contains at least
one completed `succeeded` run for this job. If the daily run has not occurred
yet, leave the release pending and inspect it after the next 03:17 UTC run.

### Executable production gate

From an authorized operator machine with the production database URL and a
short-lived Supabase Management API token:

```bash
cd backend
export SQLALCHEMY_DATABASE_URI='postgresql://...'
export SUPABASE_ACCESS_TOKEN='sbp_...'
python scripts/verify_public_preview_release.py \
  --backend-url https://api.prismpro.live \
  --frontend-origin https://www.prismpro.live \
  --supabase-project-ref '<prismpro-project-ref>'
```

That default command is read-only. After reviewing the target project and
database, add `--write-smoke` to create one unique `example.com` waitlist row,
verify the 8 KiB limit, neutral duplicate response, unique persistence, and
burst limit, then delete only that generated row.

Do not pass `--allow-http` in production. It exists only for local testing.

### Waitlist access and deletion requests

1. Accept requests only through `support@prismpro.live`.
2. Confirm control of the submitted address by sending a single-use nonce and
   requiring a reply from the same address. Do not disclose whether an address
   is present before verification.
3. Have an authorized operator query only the normalized email requested.
4. For access, return the record through an approved encrypted channel. For
   deletion, delete only that normalized email inside a transaction and record
   the request timestamp and outcome outside the waitlist table without copying
   the optional free-text response.
5. Have a second operator review destructive requests when practical. Never
   paste production records into Linear, GitHub, application logs, or chat.
6. Confirm completion to the requester without exposing internal identifiers.

## OAuth Redirects

Supabase Auth URL configuration:

- Site URL: `https://www.prismpro.live`
- Redirect URLs:
  - `https://www.prismpro.live/api/auth/callback`
  - `https://prismpro.live/api/auth/callback`

Google OAuth client:

- Authorized JavaScript origin: `https://www.prismpro.live`
- Authorized redirect URI:
  - `https://<project-ref>.supabase.co/auth/v1/callback`

## Storage Setup

Create a private Supabase Storage bucket:

- Name: `resume`
- Public: disabled
- Max file size: 10 MB
- MIME types:
  - `application/pdf`
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

Object paths must be user-scoped, for example:

```text
<user_id>/uploads/<resume_id>/<filename>
<user_id>/exports/<version_id>/<filename>
```

## RLS And Storage Audit

Run these SQL checks before publication and paste the results into the release
notes or deployment ticket.

```sql
-- User-owned tables must have RLS enabled.
select schemaname, tablename, rowsecurity
from pg_tables
where schemaname = 'public'
  and tablename in (
    'users',
    'resume_documents',
    'resume_evaluations_v2',
    'resume_versions',
    'jd_evaluations',
    'resume_exports',
    'credit_ledger',
    'job_applications',
    'job_listings',
    'user_profiles'
  )
order by tablename;

-- Policies must enforce ownership predicates, not only TO authenticated.
select schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
from pg_policies
where schemaname = 'public'
  and tablename in (
    'users',
    'resume_documents',
    'resume_evaluations_v2',
    'resume_versions',
    'jd_evaluations',
    'resume_exports',
    'credit_ledger',
    'job_applications',
    'job_listings',
    'user_profiles'
  )
order by tablename, policyname;

-- Update policies should include WITH CHECK.
select tablename, policyname, cmd, with_check
from pg_policies
where schemaname = 'public'
  and cmd in ('UPDATE', 'ALL')
order by tablename, policyname;

-- Storage bucket must be private and named resume.
select id, name, public, file_size_limit, allowed_mime_types
from storage.buckets
where id = 'resume';

-- Storage policies must scope object paths by authenticated user.
select policyname, cmd, qual, with_check
from pg_policies
where schemaname = 'storage'
  and tablename = 'objects'
order by policyname;
```

Release is blocked if:

- Any user-owned table reports `rowsecurity=false`.
- A user-data policy grants broad `TO authenticated` access without a user
  ownership predicate.
- An update policy lacks a `WITH CHECK` clause.
- The `resume` bucket is public.
- Storage object policies do not enforce user-scoped paths.

### 2026-06-30 Live Audit Result

Project: `foytemzinonzkufkstqf`

Result:

- All public tables report RLS enabled.
- User-owned write policies use ownership predicates and `WITH CHECK`.
- `resume` storage bucket is private.
- `resume` storage bucket allows only PDF and DOCX with a 10 MB limit.
- Storage object policies scope paths to the authenticated user's folder.
- `public.grant_monthly_credits(p_amount integer)` has `search_path=public`.
- Alembic production version is `8a7c2d19f4b3`.

Remaining Supabase Security Advisor warning:

- Leaked password protection is disabled. This is not a blocker if password
  auth is disabled and Google OAuth is the only launch sign-in method. Enable
  it before offering email/password sign-in.

## Monthly Credits

Enable `pg_cron`, schedule the monthly grant, and backfill the current month:

```sql
create extension if not exists pg_cron;

select cron.schedule(
  'monthly-freemium-credit-grant',
  '0 0 1 * *',
  $$select public.grant_monthly_credits(90);$$
);

-- Safe to rerun for the current month.
insert into credit_ledger (user_id, delta, reason, balance_after, external_ref)
select
  u.user_id,
  90,
  'monthly_grant',
  coalesce((
    select cl.balance_after
    from credit_ledger cl
    where cl.user_id = u.user_id
    order by cl.created_at desc
    limit 1
  ), 0) + 90,
  'monthly:' || to_char(now(), 'YYYY-MM') || ':' || u.user_id
from users u
where not exists (
  select 1
  from credit_ledger cl
  where cl.external_ref = 'monthly:' || to_char(now(), 'YYYY-MM') || ':' || u.user_id
);
```

## Deployment Order

1. Confirm CI is green on the PR branch.
2. Confirm `pip-audit -r backend/requirements.lock` has no high/critical issues.
3. Build backend and frontend Docker images.
4. Apply Alembic migrations on a clean staging database.
5. Apply Alembic migrations to production.
6. Verify Supabase auth redirects, RLS policies, and storage bucket.
7. Deploy backend.
8. Deploy frontend.
9. Run manual smoke before publishing links publicly.

## Rollback

1. Roll back frontend to the previous healthy deployment.
2. Roll back backend to the previous healthy deployment.
3. Do not roll back migrations unless a migration-specific rollback has been
   reviewed and tested.
4. If credit grants are duplicated, do not delete ledger rows manually; add a
   compensating ledger entry with a clear `external_ref`.

## Manual MVP Smoke

Record pass/fail and timestamp for each item.

- Google sign-in succeeds from `https://www.prismpro.live`.
- User row is created.
- User receives exactly 90 credits for the current month.
- PDF resume upload succeeds.
- DOCX resume upload succeeds.
- Resume evaluation debits 1 credit.
- JD tailor/analyze debits 2 credits.
- Pointer select/edit/apply persists the tailored JSON.
- Tailored resume library lists the company-specific resume.
- PDF download renders from saved JSON and debits 1 credit.
- Low/zero credit paths return `402`.
- Second test user cannot read the first user's resume, JD, export, profile, or application data.
- Legacy URL extraction/demo endpoints are not public launch APIs.
- No Stripe/payment/top-up UI appears.
