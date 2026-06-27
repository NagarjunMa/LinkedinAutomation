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
| User-owned table RLS | Pending audit | All user-owned tables report `rowsecurity=true` |
| Ownership policies | Pending audit | Policies include user predicates, not only `TO authenticated` |
| Update policy safety | Pending audit | `UPDATE`/`ALL` policies include `WITH CHECK` |
| Private storage bucket | Pending audit | `storage.buckets.public=false` for bucket `resume` |
| User-scoped storage paths | Pending audit | `storage.objects` policies restrict paths to the authenticated user |
| Service role isolation | Pending production check | Service role key exists only in backend env |

Run the SQL checks in `docs/production-mvp-runbook.md` and paste results into
the release ticket before publication.

## Phase 4: Product Smoke Gate

| Item | Status | Verification Gate |
| --- | --- | --- |
| Google sign-in | Pending manual smoke | Login works from `https://www.prismpro.live` |
| Monthly credits | Pending manual smoke | New user receives exactly 90 credits once for the current month |
| Uploads | Pending manual smoke | PDF and DOCX upload succeed |
| Resume evaluation | Pending manual smoke | Evaluation debits 1 credit and returns transparent score explanations |
| JD tailoring | Pending manual smoke | Tailor/analyze debits 2 credits and returns truth/fit signals |
| Pointer apply | Pending manual smoke | Selected/edited pointers persist tailored JSON |
| Tailored resume library | Pending manual smoke | Company-specific saved resume is visible and isolated to the user |
| PDF download | Pending manual smoke | Download renders from saved JSON and debits 1 credit |
| Low-credit path | Pending manual smoke | Zero-credit calls return `402` |
| Multi-user isolation | Pending manual smoke | A second user cannot read first user data |
| Stripe hidden | Pending manual smoke | No payment/top-up/Stripe UI appears |

## Phase 5: Resume PDF Layout Gate

| Item | Status | Verification Gate |
| --- | --- | --- |
| One-page fit | Pending manual QA | Single-page resumes stay one page unless source content justifies 2 pages |
| A4/Letter scaling | Pending manual QA | Both page sizes keep readable margins and no crop |
| Long bullet wrapping | Pending manual QA | Bullets wrap without clipping or overlap |
| Empty section handling | Pending manual QA | Empty sections are suppressed or rendered cleanly |
| Downloaded PDF content | Pending manual QA | Downloaded PDF contains visible resume content |
| Browser preview isolation | Pending manual QA | Tailor preview iframe renders under production security headers without blank/cropped content |

## Phase 6: Launch Decision

Public launch is approved only when Phases 2-5 are complete and the production
runbook has captured the actual Supabase audit output and manual smoke results.
