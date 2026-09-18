# Prism Pro MVP Production Runbook

This is the supported operational runbook, reconciled on 2026-09-18. Use it with
the [deployment entrypoint](../DEPLOYMENT.md) and
[release checklist](../DEPLOYMENT_READINESS_CHECKLIST.md). Public preview and
authenticated internal product testing are separate modes; neither green CI nor
historical smoke evidence authorizes a full product launch.

## Deployment Model

- Billing is disabled: `ENABLE_BILLING=false`.
- Stripe environment variables are optional until billing is enabled.
- Freemium allowance is `FREEMIUM_MONTHLY_CREDITS=90`.
- Supabase Storage uses one private bucket: `resume`.
- Railway backend is assumed to run as a single instance for MVP.
- No Redis or Celery service is required in the current topology. An approved
  shared/edge abuse-control design and load verification are required before
  multi-instance backend deployment; a broker alone is not sufficient.

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

When production preview mode is enabled, backend validation requires the single
canonical HTTPS CORS origin and both declared process counts to be one. The flag
defaults to true, but code permits an explicit false value: keeping it true on the
public deployment is also an operator release requirement. Verify actual hosted
replica/process settings, not just environment declarations.

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

If Cron was enabled after the migration, an authorized operator must review the
target and approve this narrowly scoped schedule change before executing it:

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

These settings apply to an authorized internal product environment. Keep public
preview auth lockdown intact. For local testing, allow
`http://localhost:3000/api/auth/callback` in that environment's Supabase redirect
list and use localhost site URLs in the frontend environment. Google still
returns to the hosted Supabase callback below, not a localhost `/auth/v1/callback`.
See [Supabase Google OAuth](https://supabase.com/docs/guides/auth/social-login/auth-google)
and [redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls)
(checked 2026-09-18). Never copy callback tokens into a ticket.

Supabase Auth URL configuration for that internal environment (replace the
example host with its actual authorized origin):

- Site URL: `https://internal.example.com`
- Redirect URLs:
  - `https://internal.example.com/api/auth/callback`
  - `http://localhost:3000/api/auth/callback` for authorized local development

Google OAuth client:

- Authorized JavaScript origins: the internal origin and `http://localhost:3000`
  for authorized local development
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
<user_id>/<resume_document_id>.<extension>
<user_id>/<export_id>.pdf
```

## RLS And Storage Audit

Run these read-only checks only against an authorized target before publication.
Store a sanitized pass/fail summary and reviewer in the release ticket, not raw
production identifiers or records. Include any additional exposed tables found
in the live schema; the list below is not a complete inventory. Retired tables
still need protection until a separately approved migration removes them.

RLS does not replace grants or backend ownership checks, and privileged roles
can bypass it. See [Supabase RLS guidance](https://supabase.com/docs/guides/database/postgres/row-level-security)
(checked 2026-09-18). Test both allowed and denied operations with two sandbox
users; merely listing policy text is not an isolation test.

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

### Historical 2026-06-30 audit (not current release evidence)

Result:

- All public tables report RLS enabled.
- User-owned write policies use ownership predicates and `WITH CHECK`.
- `resume` storage bucket is private.
- `resume` storage bucket allows only PDF and DOCX with a 10 MB limit.
- Storage object policies scope paths to the authenticated user's folder.
- `public.grant_monthly_credits(p_amount integer)` has `search_path=public`.
- Alembic production version is `8a7c2d19f4b3`.

That audit recorded this Supabase Security Advisor warning; recheck current state:

- Leaked password protection is disabled. This is not a blocker if password
  auth is disabled and Google OAuth is the only launch sign-in method. Enable
  it before offering email/password sign-in.

## Monthly Credits

The allowance is configured as 90 credits; scheduling is database-side, not a
Celery task. Do not use the old ad-hoc backfill SQL: checking for an existing row
does not by itself establish concurrency-safe balance updates.

Before enabling or changing a schedule/backfill, the backend/database owner must
inspect the installed grant function, its permissions, transaction/locking and
idempotency behavior against the current ledger, then test concurrent grant/debit
and repeat execution in an isolated PostgreSQL environment. Record the approved
SQL/revision, amount, schedule, successful execution and reviewer in Linear.
The historical monthly-credit setup guide is not authorization to mutate balances.
No monthly schedule or production balance was inspected or changed by PRI-18.

## Deployment Order

1. Confirm CI is green on the PR branch.
2. Confirm the repository's dependency audits pass without unapproved exceptions.
3. Build backend and frontend Docker images, plus the root multi-stage image if
   that is the deployment target (it is not built by current CI).
4. Test the migration chain on clean and representative existing-schema staging
   databases; verify a backup and migration-specific rollback plan.
5. Obtain explicit operator approval, verify the target, then apply reviewed
   Alembic migrations to production. Stop on errors; never bypass the chain.
6. Verify Supabase auth redirects, RLS policies, and storage bucket.
7. Deploy backend.
8. Deploy frontend.
9. Run the mode-specific smoke and record owner approval before publishing links.
   Do not disable public preview as an incidental deployment step.

## Rollback

1. Roll back frontend to the previous healthy deployment.
2. Roll back backend to the previous healthy deployment.
3. Do not roll back migrations unless a migration-specific rollback has been
   reviewed and tested.
4. If credit grants are duplicated, do not delete ledger rows manually. Obtain
   approval for an audited reconciliation/compensating-entry plan with explicit
   identity, locking and idempotency checks.

## Manual MVP Smoke

Run these product checks on a separately authorized internal deployment, not the
public trailer. Record pass/fail, revision, environment, reviewer and timestamp.
Local browser tests do not constitute a fresh production smoke result.

- Google sign-in succeeds from the authorized internal origin and returns there.
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
