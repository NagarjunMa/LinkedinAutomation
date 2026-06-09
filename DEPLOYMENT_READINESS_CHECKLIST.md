# Production Readiness Checklist

Branch: `codex/production-readiness-freemium`

## Baseline Captured

- Backend baseline: `python -m pytest tests/ --ignore=tests/golden -q --maxfail=5`
  currently fails in the local shell because Python 3.12 loads a Starlette/httpx
  `TestClient` incompatibility (`Client.__init__() got an unexpected keyword
  argument 'app'`). CI/Docker target Python 3.11.
- Frontend lint baseline: `npm run lint -- --max-warnings=0` fails on unused
  imports and hook dependency warnings.
- Frontend type baseline: `npx tsc --noEmit` fails on dashboard context,
  Framer Motion variants, missing `react-confetti`, `react-window` v2 API, and
  one hook test type.
- Frontend audit baseline: `npm audit --omit=dev --json` reports 8 production
  vulnerabilities, including direct `next` advisories.

## Workstreams

| Area | Status | Verification Gate |
| --- | --- | --- |
| Freemium credits | Verified locally | New/current users receive one 90-credit monthly grant only |
| Billing hold | Verified locally | Stripe route hidden unless `ENABLE_BILLING=true` |
| Auth hardening | Verified locally | Legacy routes reject unauthenticated and mismatched user IDs |
| Frontend upgrade | Verified locally | Next 16, Node 20.9+, strict lint/type/build |
| Env/security | In progress | Root `.env.production` removed from tracking; secret scan must run in CI |
| CI strictness | In progress | CI now blocks lint/type/test/high audit failures; remote CI run still required |
| Production smoke | Pending | Manual checklist passes in production |

## Local Verification Completed

- Backend lint: `python3.11 -m ruff check app/ --select=E,F --ignore=E501,E402`
- Backend API/security slice: `python3.11 -m pytest tests/api/v1 tests/core/test_auth.py tests/integration/test_new_user_bootstrap.py tests/test_smoke.py -q -o addopts=""`
  - Result: 59 passed, 3 skipped. Skips are Stripe webhook tests gated by `ENABLE_BILLING=true`.
- Backend credit slice: `python3.11 -m pytest tests/api/v1/test_credits.py tests/services/credits/ -q -o addopts=""`
  - Result: 14 passed, 2 skipped.
- Frontend lint: `npm run lint`
- Frontend typecheck: `npx tsc --noEmit`
- Frontend build: `NEXT_PUBLIC_API_URL=https://api.example.com NEXT_PUBLIC_SUPABASE_URL=https://test.supabase.co NEXT_PUBLIC_SUPABASE_ANON_KEY=test npm run build`
- Frontend tests: `npm run test`
  - Result: 44 passed across 15 files.
- Frontend production audit: `npm audit --omit=dev --audit-level=high`
  - Result: passes with zero high/critical production findings. Two moderate Next/PostCSS findings remain from Next 16.2.7 vendored dependency metadata.

## Remaining Deployment Gates

- Run full CI on GitHub after pushing this branch.
- Run backend tests with configured coverage plugin in the CI Python 3.11 environment.
- Run `pip-audit -r backend/requirements.txt` in CI after dependency install.
- Verify Alembic `upgrade head` on a clean Postgres database.
- Run production manual smoke: Google sign-in, 90-credit grant, upload PDF/DOCX, evaluate, tailor, apply, export, signed URL, 402 behavior, and multi-user isolation.
- Confirm secret scan passes and no generated reports/artifacts appear in `git status`.
