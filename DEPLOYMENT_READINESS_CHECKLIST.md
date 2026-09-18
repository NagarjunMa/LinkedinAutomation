# Production Readiness Checklist

Reconciled 2026-09-18. This checklist defines gates, not a statement that the
current revision is deployed or launch-approved. Record revision, environment,
timestamp and reviewer in the PrismPro Linear release issue for every result.
Historical 2026-06-30 results below require revalidation for the release target.
Linear owns current task status; old TECH_DEBT/progress notes are historical.

## Phase 1: Configuration And Documentation Hygiene

| Item | Status | Verification Gate |
| --- | --- | --- |
| Remove stale `SUPABASE_JWT_SECRET` references | Complete | CI/test config uses Supabase ES256 + JWKS only |
| Remove stale build-ignore documentation | Complete | README no longer claims `ignoreBuildErrors` is masking TypeScript issues |
| Keep launch docs authoritative | Complete | README points to this checklist and `docs/production-mvp-runbook.md` |
| Keep frontend secrets out of public env | Pending production check | Public variables contain no secrets; service role/admin credentials stay backend-only |

## Phase 2: CI And Dependency Gates

| Item | Status | Verification Gate |
| --- | --- | --- |
| Backend lint/test/coverage | CI gated | GitHub backend job passes |
| Clean Postgres migration smoke | CI gated | `alembic upgrade head` passes against CI Postgres |
| Postgres concurrent credit tests | CI gated | `tests/services/credits/ -k concurrent` passes |
| Backend dependency audit | CI gated | `pip-audit -r backend/requirements.lock` passes |
| Frontend lint/type/build/test/e2e | CI gated | GitHub frontend job passes |
| Frontend production audit | CI gated | `npm audit --omit=dev --audit-level=high` passes |
| Secret scanning | CI gated | TruffleHog verified scan passes |
| Service Docker images | CI gated | Backend and frontend Docker builds pass |
| Root multi-stage Docker image | Separate evidence required if used | Not built by current CI; build the actual deployment target |

## Phase 3: Supabase Security Gate

| Item | Status | Verification Gate |
| --- | --- | --- |
| User-owned table RLS | Historical; revalidate | Live Supabase audit on 2026-06-30 reports all public tables with `rowsecurity=true` |
| Ownership policies | Historical; revalidate | Live policies use user predicates or explicit authenticated read-only access for shared job listings |
| Update policy safety | Historical; revalidate | Live `UPDATE`/`ALL` policies include `WITH CHECK` for user-owned write paths |
| Private storage bucket | Historical; revalidate | Live `storage.buckets.public=false` for bucket `resume` |
| User-scoped storage paths | Historical; revalidate | Live `storage.objects` policies restrict paths to the authenticated user |
| Service role isolation | Pending production check | Service role key exists only in backend env |

Run the authorized read-only SQL checks in `docs/production-mvp-runbook.md` and
record sanitized findings in the release ticket. Also exercise positive and
negative cross-user isolation in an approved sandbox; policy listings alone
are not sufficient. Do not copy production identifiers or user records.

## Phase 4: Product Smoke Gate

| Item | Status | Verification Gate |
| --- | --- | --- |
| Google sign-in | Historical; revalidate | User-confirmed production smoke passed on 2026-06-30 |
| Monthly credits | Historical; revalidate | User-confirmed 90-credit grant smoke passed on 2026-06-30 |
| Uploads | Historical; revalidate | User-confirmed PDF and DOCX upload smoke passed on 2026-06-30 |
| Resume evaluation | Historical; revalidate | User-confirmed evaluation debit smoke passed on 2026-06-30 |
| JD tailoring | Historical; revalidate | User-confirmed tailor debit smoke passed on 2026-06-30 |
| Pointer apply | Historical; revalidate | User-confirmed pointer apply smoke passed on 2026-06-30 |
| Tailored resume library | Historical; revalidate | User-confirmed library smoke passed on 2026-06-30 |
| PDF download | Historical; revalidate | User-confirmed PDF download debit smoke passed on 2026-06-30 |
| Low-credit path | Historical; revalidate | User-confirmed `402` smoke passed on 2026-06-30 |
| Multi-user isolation | Historical; revalidate | User-confirmed multi-user isolation smoke passed on 2026-06-30 |
| Stripe hidden | Historical; revalidate | User-confirmed no payment/top-up/Stripe UI smoke passed on 2026-06-30 |

## Phase 5: Resume PDF Layout Gate

| Item | Status | Verification Gate |
| --- | --- | --- |
| One-page fit | Pending manual QA | Single-page resumes stay one page unless source content justifies 2 pages |
| A4/Letter scaling | Pending manual QA | Both page sizes keep readable margins and no crop |
| Long bullet wrapping | Pending manual QA | Bullets wrap without clipping or overlap |
| Empty section handling | Pending manual QA | Empty sections are suppressed or rendered cleanly |
| Downloaded PDF content | Pending manual QA | Downloaded PDF contains visible resume content |
| Browser preview isolation | Pending manual QA | Tailor preview iframe renders under production security headers without blank/cropped content |

## Public-preview trailer gate (PRI-5)

| Item | Status | Verification Gate |
| --- | --- | --- |
| Public preview flags | Code-enforced; pending production evidence | Keep `PRISM_PRO_PUBLIC_PREVIEW_ONLY=true` on both services; omitted flags default true, but explicit false is allowed in code and forbidden by public-release policy |
| Supabase public signup | Verifier added; pending production evidence | Auth → General configuration → **Allow new users to sign up** is disabled; anonymous sign-ins are disabled; release verifier passes |
| Preview database migration | Migration/verifier ready; pending production run | `alembic upgrade head` creates `waitlist_entries` with RLS enabled and no `anon`/`authenticated` grants |
| Waitlist API | Pending production smoke | Valid and duplicate submissions return the same `202` response; rate limits and 8 KiB request cap are active |
| Public-preview analytics | Pending production smoke | Hero CTA, form start/success/failure category, and scroll-depth events reach `/api/v1/public-preview/events` without email or free-text fields |
| Distributed abuse controls | Startup guard added; pending Railway evidence | `BACKEND_REPLICA_COUNT=1` and `WEB_CONCURRENCY=1`; keep Railway at one replica until an edge/distributed limiter exists |
| Product API lockdown | Pending production smoke | A request with an existing bearer token receives `403` for product API routes |
| Auth callback lockdown | Pending production smoke | OAuth callback and email confirmation URLs return to `/` without creating session cookies |
| Waitlist retention | Migration automation added; pending production evidence | Supabase Cron job `prismpro-waitlist-retention-daily` is active and has a successful recorded run |
| Data requests | Runbook defined; pending operator validation | Verified-address access/export/deletion workflow from `support@prismpro.live` is exercised by an authorized operator |
| Public origins | Code-enforced; pending production evidence | `CORS_ORIGINS` equals the single canonical `PUBLIC_FRONTEND_ORIGIN`; release verifier passes allowed/denied preflights |

The public trailer must use a separate deployment for internal product testing.
Do not set either preview flag to `false` on the public deployment.

## Phase 6: Launch Decision

For a public trailer, require applicable configuration/CI/security gates and every
public-preview trailer gate above, with explicit owner approval. Product paths
must remain blocked. Internal product QA is a separate deployment.

A full product launch additionally requires current Phases 2–5 evidence,
resolution or explicit reviewed disposition of known gaps, and owner approval of
any preview/auth-policy transition. Old completion labels, merged PRs and local
tests are not launch authorization. Critical operational guidance in PRI-18 also
requires an explicit additional human review before merge.
