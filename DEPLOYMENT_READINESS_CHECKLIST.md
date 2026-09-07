# Production Readiness Checklist

This checklist is the phase tracker for work that must be resolved before Prism
Pro is publicly shared. Long-term cleanup that does not block the 50-100 user
MVP belongs in `TECH_DEBT.md`; anything below is a release gate.

## Phase 1: Configuration And Documentation Hygiene

| Item | Status | Verification Gate |
| --- | --- | --- |
| Remove stale `SUPABASE_JWT_SECRET` references | Complete | CI/test config uses Supabase ES256 + JWKS only |
| Remove stale build-ignore documentation | Complete | README no longer claims `ignoreBuildErrors` is masking TypeScript issues |
| Keep launch docs authoritative | Complete | README points to this checklist and `docs/production-mvp-runbook.md` |
| Keep frontend secrets out of public env | Pending production check | Frontend has only `NEXT_PUBLIC_*`; no service role/admin vars |

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
| Docker images | CI gated | Backend and frontend Docker builds pass |

## Phase 3: Supabase Security Gate

| Item | Status | Verification Gate |
| --- | --- | --- |
| User-owned table RLS | Complete | Live Supabase audit on 2026-06-30 reports all public tables with `rowsecurity=true` |
| Ownership policies | Complete | Live policies use user predicates or explicit authenticated read-only access for shared job listings |
| Update policy safety | Complete | Live `UPDATE`/`ALL` policies include `WITH CHECK` for user-owned write paths |
| Private storage bucket | Complete | Live `storage.buckets.public=false` for bucket `resume` |
| User-scoped storage paths | Complete | Live `storage.objects` policies restrict paths to the authenticated user |
| Service role isolation | Pending production check | Service role key exists only in backend env |

Run the SQL checks in `docs/production-mvp-runbook.md` and paste results into
the release ticket before publication.

## Phase 4: Product Smoke Gate

| Item | Status | Verification Gate |
| --- | --- | --- |
| Google sign-in | Complete | User-confirmed production smoke passed on 2026-06-30 |
| Monthly credits | Complete | User-confirmed 90-credit grant smoke passed on 2026-06-30 |
| Uploads | Complete | User-confirmed PDF and DOCX upload smoke passed on 2026-06-30 |
| Resume evaluation | Complete | User-confirmed evaluation debit smoke passed on 2026-06-30 |
| JD tailoring | Complete | User-confirmed tailor debit smoke passed on 2026-06-30 |
| Pointer apply | Complete | User-confirmed pointer apply smoke passed on 2026-06-30 |
| Tailored resume library | Complete | User-confirmed library smoke passed on 2026-06-30 |
| PDF download | Complete | User-confirmed PDF download debit smoke passed on 2026-06-30 |
| Low-credit path | Complete | User-confirmed `402` smoke passed on 2026-06-30 |
| Multi-user isolation | Complete | User-confirmed multi-user isolation smoke passed on 2026-06-30 |
| Stripe hidden | Complete | User-confirmed no payment/top-up/Stripe UI smoke passed on 2026-06-30 |

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
| Public preview flags | Pending production check | Set `PRISM_PRO_PUBLIC_PREVIEW_ONLY=true` on frontend and backend |
| Supabase public signup | Pending production check | Auth → General configuration → **Allow new users to sign up** is disabled; anonymous sign-ins are disabled |
| Preview database migration | Pending production check | `alembic upgrade head` creates `waitlist_entries` with RLS enabled and no `anon`/`authenticated` grants |
| Waitlist API | Pending production smoke | Valid and duplicate submissions return the same `202` response; rate limits and 8 KiB request cap are active |
| Public-preview analytics | Pending production smoke | Hero CTA, form start/success/failure category, and scroll-depth events reach `/api/v1/public-preview/events` without email or free-text fields |
| Distributed abuse controls | Pending production check | Keep the backend at one replica while using the in-process limiter, or add an edge/distributed IP rate limit before scaling horizontally |
| Product API lockdown | Pending production smoke | A request with an existing bearer token receives `403` for product API routes |
| Auth callback lockdown | Pending production smoke | OAuth callback and email confirmation URLs return to `/` without creating session cookies |
| Waitlist retention | Pending operations setup | Schedule `python scripts/purge_expired_waitlist.py` daily; first run with `--dry-run` |
| Data requests | Pending operations setup | Route verified access/export/deletion requests from `support@prismpro.live` to an authorized operator |
| Public origins | Pending production check | Backend `CORS_ORIGINS` contains only the deployed PrismPro frontend origin |

The public trailer must use a separate deployment for internal product testing.
Do not set either preview flag to `false` on the public deployment.

## Phase 6: Launch Decision

Public launch is approved only when Phases 2-5 are complete and the production
runbook has captured the actual Supabase audit output and manual smoke results.
