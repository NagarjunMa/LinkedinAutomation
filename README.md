# Prism Pro

**Recruiter-grade resume prep for working engineers.** Polish your resume the way a senior recruiter would, tailor it to any JD with a per-change diff view, and export country-aware PDFs for US and Indian markets.

For engineers who refuse generic AI bullets.

![Backend tests](https://img.shields.io/badge/backend--tests-157%20pass-green) ![Backend coverage](https://img.shields.io/badge/backend--coverage-87%25-green) ![Frontend tests](https://img.shields.io/badge/frontend--tests-44%20pass-green) ![Frontend coverage](https://img.shields.io/badge/frontend--coverage-84%25-green)

---

## What's shipped

### Resume polish
- Upload PDF or DOCX (parsed structurally — bullets, skills, sections preserved)
- Single-agent GPT-4o evaluator with specialized passes (ATS, XYZ formula, 7-second scan, country-aware tone)
- Bullet-level severity flags: **Strong / Weak / Vague Impact** — same lens a senior recruiter uses
- ATS raw-text simulator shows your resume as a parser sees it (tables stripped, columns lost, etc.)
- Per-bullet rewrite with hallucination guard — hard numbers stay as `[X%]` / `[N users]` placeholders; verbs, structure, framing are rewritten

### JD-driven tailoring
- Paste any job description
- Backend extracts must-have / good-to-have / soft-skills + seniority + country hint + company name
- Tailor produces a diff plan: bullet rewrites + skill reorder + summary rewrite
- Per-change accept; version history preserved

### Apply → Preview → Export pipeline (new)
- Apply accepted changes via `POST /jd/{id}/apply` — creates a JD-linked `ResumeVersion` (star-pattern: always branches from original ResumeDocument)
- Inline iframe preview with sticky template picker
- Download PDF in the matching country/role template
- Per-JD funnel analytics via `GET /analytics/jd-progress`

### PDF export
- Playwright + Chromium renders 6 country-aware templates (USA / India × SWE / DS / PM)
- Files persist to Supabase Storage; signed-URL access for downloads
- 1 credit per export

### Credit system
- 90 free credits / month (auto-granted via `_ensure_user_row()` and Supabase **pg_cron** → `grant_monthly_credits()`)
- Billing is disabled for the freemium launch; Stripe routes stay dormant behind `ENABLE_BILLING=true`
- Per-operation cost: evaluate = 1, tailor = 2, rewrite = 0, apply = 0, export = 1
- MVP production launch steps live in [`docs/production-mvp-runbook.md`](docs/production-mvp-runbook.md).

---

## Tech stack

### Frontend
- Next.js 16.2.7 (App Router)
- Tailwind CSS + shadcn/ui
- TanStack Query for API state
- Framer Motion for animations (restrained — fade-up, scroll reveals, marquee)
- Typography: **Humane** (display + nav), **Fraunces** (serif headings), **Geist Sans** (body / UI)

### Backend
- FastAPI + SQLAlchemy 2.0 + Pydantic v2 (production installs use `backend/requirements.lock`)
- OpenAI (`gpt-4o-2024-08-06` for eval/rewrite/tailor, `gpt-4o-mini` for extraction)
- Schema-enforced LLM responses via `client.beta.chat.completions.parse()` with typed Pydantic models
- Tenacity retries on `RateLimitError` / `APIConnectionError` / `APITimeoutError`
- Hallucination guard (regex) rejects unprompted digits incl. scientific notation + `x` multipliers

### Database & infra
- Supabase Postgres + Row-Level Security on every user-owned table
- Supabase Storage (private bucket, signed URLs)
- Supabase Auth (ES256 JWT via JWKS — migrated from HS256)
- Supabase pg_cron for the monthly credit grant (no Redis / Celery — see `docs/supabase-pg-cron-setup.md`)
- Railway deploy targets (`main` branch = production; no separate staging)

---

## API endpoints (`/api/v1/`)

| Method | Path | Credits | What |
|---|---|---|---|
| POST | `/resumes/upload` | 0 | PDF/DOCX → parsed JSON + Supabase Storage |
| POST | `/resumes/{id}/evaluate` | 1 | Single-agent eval + ATS simulator |
| POST | `/resumes/{id}/rewrite/{bullet_id}` | 0 | Per-bullet rewrite (hallucination-guarded) |
| POST | `/resumes/{id}/versions` | 0 | Apply accepted changes, save version |
| POST | `/jd/analyze` | 2 | JD extract + tailor diff plan |
| POST | `/jd/{id}/apply` | 0 | Create JD-linked version + preview HTML |
| POST | `/exports` | 1 | Render to PDF via Playwright (accepts version_id + template_id) |
| GET | `/exports/{id}` | 0 | Refresh signed URL |
| GET | `/analytics/jd-progress` | 0 | Per-JD funnel counts |
| GET | `/credits/balance` | 0 | Current balance |
| POST | `/webhooks/stripe` | — | Billing-gated webhook, disabled for freemium launch |
| GET | `/admin/metrics/cost-per-user` | — | Admin allowlist gated |

Legacy job-tracking routes (`/jobs`, `/job-extraction`, `/profiles`, `/user-profiles`, `/logs`) are kept and demoted.

---

## Local development

### One command — backend + frontend

```bash
make dev
```

Boots FastAPI on `:8000` and Next.js on `:3000` together. Ctrl+C stops both.

### Other Makefile targets

```bash
make install        # pip install + npm install
make backend        # backend only
make frontend       # frontend only
make test           # backend pytest + frontend lint/tsc/build
make lint           # ruff + next lint
make build          # frontend production build
make clean          # wipe .next/, __pycache__/, .pytest_cache/
make stop           # kill processes on :8000 and :3000
make migrate        # alembic upgrade head
```

### Required env vars

`backend/.env`:
```
SQLALCHEMY_DATABASE_URI=postgresql://postgres:<pwd>@db.<ref>.supabase.co:5432/postgres
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_ANON_KEY=sb_publishable_xxxxx
SUPABASE_SERVICE_ROLE_KEY=sb_secret_xxxxx
SUPABASE_STORAGE_BUCKET=resume
OPENAI_API_KEY=sk-proj-xxxxx
FREEMIUM_MONTHLY_CREDITS=90
ENABLE_BILLING=false
ADMIN_USER_IDS=user-id-1,user-id-2     # comma-separated; for admin/metrics endpoint
```

`frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://<ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_xxxxx
NEXT_PUBLIC_GOOGLE_CLIENT_ID=...
```

URL-encode special characters in your Postgres password (`@` → `%40`, `#` → `%23`, etc.) OR set a password without special chars.

**Production (Railway):** use Supabase **session pooler** URI, not direct connection:
```
SQLALCHEMY_DATABASE_URI=postgresql://postgres.<ref>:<pwd>@aws-0-<region>.pooler.supabase.com:5432/postgres
```
Direct connection (`db.<ref>.supabase.co:5432`) resolves to IPv6 only — Railway containers can't reach it. Get the exact URI from Supabase Dashboard → Project Settings → Database → "Session pooler" tab.

### DB bootstrap on a fresh Supabase project

```bash
make migrate     # alembic upgrade head — relies on existing chain
# If migration chain conflicts (known issue, see TECH_DEBT.md):
cd backend && python3.11 -c "from app.main import app; from app.db.base_class import Base; from app.db.session import engine; from app.models import *; Base.metadata.create_all(bind=engine)" && alembic stamp head
```

Then apply RLS policies via Supabase SQL editor — see `CLAUDE.md` for the canonical RLS + Storage policy SQL.

---

## Repo layout

```
backend/                       FastAPI app
  app/
    api/v1/endpoints/          Route handlers
    services/resume/           parser, evaluator, ATS sim, rewriter, hallucination_guard
    services/jd/               extractor, tailor
    services/pdf/              Playwright renderer + 6 templates
    services/storage/          Supabase Storage client
    services/credits/          ledger (debit/refund/grant)
    services/payments/         Stripe webhook handler
    core/                      auth (ES256), config, llm_logging
    middleware/                credits, security
  migrations/                  Alembic
  tests/                       services, api, integration, fixtures
frontend/                      Next.js 16.2.7
  src/app/                     Routes
  src/components/landing/      Navigation, BentoGrid
docs/superpowers/
  specs/                       Pivot design spec
  plans/                       Phase 0/1/4 implementation plans
Makefile                       make dev / make test / make stop
TECH_DEBT.md                   Deferred refactors
BLOCKERS.md                    Pre-deploy must-fix
progress.txt                   Phase-by-phase delivery status
```

---

## Test coverage

- **Backend pytest:** 157 pass, 12 skip — `make test` or `cd backend && pytest` (86.7% coverage, gate at 80%)
- **Frontend Vitest:** 81 tests pass across 24 test files — `cd frontend && npm run test:coverage` (87.6% lines, 75.6% branches)
- **Frontend e2e (Playwright):** `cd frontend && npm run test:e2e`
- **Coverage report:** `cd backend && pytest --cov=app --cov-report=term-missing` or `cd frontend && npm run test:coverage`
- **Pre-push hook** (Lefthook) always runs both local CI suites before every `git push`, regardless of which application changed. It blocks on backend Ruff/tests/coverage/audit and frontend lint/types/build/unit coverage/Playwright/audit. Docker, PostgreSQL service checks, and TruffleHog remain blocking GitHub CI jobs.
- Core Prism Pro paths are 90%+ covered; legacy job-tracking modules (excluded via `.coveragerc`) are not gated.

---

## Publication readiness

Use `docs/production-mvp-runbook.md` and `DEPLOYMENT_READINESS_CHECKLIST.md`
as the authoritative launch references. Public sharing is blocked until:

- GitHub CI is green for backend, frontend, audits, Docker builds, and the MVP
  Playwright smoke suite.
- Supabase RLS/storage audit results are captured and show user-owned tables,
  ownership predicates, `WITH CHECK` update policies, and a private `resume`
  bucket.
- Manual production smoke passes for Google sign-in, 90-credit grants,
  PDF/DOCX upload, evaluation, tailoring, pointer apply, tailored resume
  library, PDF download, zero-credit `402`, and multi-user isolation.
- Resume PDF layout QA passes on real resumes/JDs for one-page output,
  A4/Letter scaling, margins, overflow, empty sections, long bullets, and
  downloaded PDF content.

Post-MVP maintenance items are tracked separately in `TECH_DEBT.md`; they must
not be used as launch instructions.

---

## Status

See `progress.txt` for phase-by-phase delivery state.

---

## License

Proprietary. Internal use only.
