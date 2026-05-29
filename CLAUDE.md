# Prism Pro — Project Documentation

**Prism Pro** is an AI-powered resume polish and JD-tailoring platform for experienced engineers targeting roles in the USA and India. The product gives bullet-level severity flags the way a senior recruiter would mark up a resume by hand, then proposes JD-driven rewrites in a per-change diff view, and exports recruiter-grade PDFs in country-aware templates.

**Canonical spec:** `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md`

---

## Current scope

### Primary (shipped — Phase 1)
- **Resume Polish** — single-agent GPT-4o evaluator with specialized passes. Bullet-level severity flags (Strong / Weak / Vague Impact). ATS raw-text simulator with parseability scoring.
- **JD-Driven Tailoring** — JD extractor + tailor produces a diff plan (bullet rewrites, skill reorder, summary rewrite) with per-change accept. Hallucination guard rejects unprompted numbers across rewriter + tailor.

### Primary (shipped — Phase 2)
- **PDF Export** — Playwright + Chromium renders six country-aware templates (USA / India × SWE / DS / PM). Files persist to Supabase Storage. Signed-URL access.

### Primary (shipped — Phase 3)
- **Frontend** — Routes: `/dashboard/resume`, `/resume/[id]/edit`, `/resume/tailor`, `/credits`. API client + TanStack Query hooks. Severity-coded bullet renderer. Hallucination-guarded rewrite modal. ATS parseability tab. Diff view with per-change accept.

### Primary (shipped — Phase 4 production hardening)
- Supabase Storage upload (replaces Railway ephemeral filesystem).
- Credit ledger row-lock on `users` row (was arbitrary ledger row — non-deterministic).
- Stripe webhook receiver with idempotent grants.
- Monthly free-tier grant Celery beat task.
- Per-user LLM cost telemetry.
- Admin metrics endpoint (`GET /admin/metrics/cost-per-user`).

### Primary (shipped — 2026-05-26 Tailor Apply → Preview → Export)
- **`POST /jd/{id}/apply`** — creates JD-linked `ResumeVersion` + preview HTML (0 credits, star-pattern versioning — re-tailoring branches from original `ResumeDocument`, never from latest version).
- **`render_html_only()`** — self-contained HTML with inlined CSS for iframe `srcdoc` preview (no `file://` links).
- **Extended `POST /exports`** — accepts `resume_version_id` + dash-format `template_id` alongside legacy `resume_document_id + country + role_template`.
- **`GET /analytics/jd-progress`** — per-JD funnel counts (versions + exports).
- Frontend: `PreviewPanel` (sticky iframe + template picker + Download PDF), `useTailorApply` + `useExportPdf` hooks.
- Schema enforcement: extractor + tailor migrated to `client.beta.chat.completions.parse()` with typed Pydantic models (`JDExtraction.company_name`, `BulletPlaceholder` typed model).

### Primary (shipped — 2026-05-26 Auth + onboarding)
- **Welcome credits** — `_ensure_user_row()` auto-creates `User` row + grants 10 credits on first sign-in (idempotent via IntegrityError guard for TOCTOU race).
- **Profile bootstrap** — returns empty defaults (not 404) for new users so dashboard loads cleanly.
- **Auth hardening** — removed `test_user_123` unauthenticated fallback; returns 401 instead.

### Supporting (kept, demoted)
- Job tracking under `/dashboard/applications` and `/dashboard/jobs`.
- URL-based job extraction (Jina AI Reader + GPT-4o-mini).

### Deferred (not in MVP)
- Voice interview prep — separate pillar, not scheduled
- Browser extension job tracker — separate pillar, not scheduled
- Multi-agent resume evaluation — explicitly rejected (single-agent + specialized passes is the canonical architecture)
- Email automation, Gmail scanning, weekly digests
- Referral templates, contact discovery (Apollo)
- Analytics intelligence dashboards

### Geography & personas
- MVP markets: **USA + India**
- Personas: SWE, Data Science, PM (six PDF templates: 3 roles × 2 countries)

---

## Architecture

### AI — "precision over complexity"
- **Single-agent core** (GPT-4o-2024-08-06) with specialized passes for ATS, XYZ-formula, scan-rule, JD-keyword coverage.
- **Pydantic-validated structured outputs** for every model call — AI is a data processor, not a creative writer.
- **Hallucination guard** — regex rejects digits/scientific-notation/x-multipliers not present in the original bullet, except for typed placeholders like `[X%]` or `[N users]`.
- **Retry policy** — `tenacity` retries on `RateLimitError`, `APIConnectionError`, `APITimeoutError`. Never retries on `HallucinationError` (logic error, not transient).
- Models: GPT-4o-2024-08-06 for evaluation/rewrite/tailor, GPT-4o-mini for extraction.

### Backend (FastAPI)
Routes live at `/api/v1/`:

| Route | Purpose | Credits |
|---|---|---|
| `POST /resumes/upload` | PDF/DOCX → parsed JSON + Supabase Storage | 0 |
| `POST /resumes/{id}/evaluate` | Single-agent eval + ATS simulator | 1 |
| `POST /resumes/{id}/rewrite/{bullet_id}` | Per-bullet rewrite (guarded) | 0 |
| `POST /resumes/{id}/versions` | Apply accepted changes, save new version | 0 |
| `POST /jd/analyze` | JD extract + tailor diff plan | 2 |
| `POST /jd/{id}/apply` | Create JD-linked ResumeVersion + preview HTML | 0 |
| `POST /exports` | Playwright PDF render to Storage (accepts version_id + template_id) | 1 |
| `GET /exports/{id}` | Refresh signed URL (no credit) | 0 |
| `GET /analytics/jd-progress` | Per-JD funnel counts (versions + exports) | 0 |
| `GET /credits/balance` | Current credit balance | 0 |
| `POST /webhooks/stripe` | Idempotent credit grants | platform |
| `GET /admin/metrics/cost-per-user` | Admin allowlist gated | 0 |

Legacy routes (kept, demoted): `jobs.py`, `job_extraction.py`, `profiles.py`, `user_profiles.py`, `logs.py`.

Removed in Phase 0: email services (Resend, SendGrid, generic), referral services + endpoint, activity endpoint + model, analytics services, `job_aggregator`, `question_answer_service`, Celery tasks for email/analytics/feedback, multi-agent evaluator + Harvard compliance test files, ten one-shot debug/migration scripts, sixteen stale `.md` files.

Removed in Phase 4: `schemas/activity.py`, `schemas/analytics.py`, `schemas/export.py`, `utils/email_helpers.py`, `core/config_old.py`, two stale in-app migration files, `services/orchestrator_manager.py`, legacy `api/v1/endpoints/resumes.py`.

### Auth
- **Supabase ES256 + JWKS** (migrated from HS256 shared secret in 2026).
- Backend fetches public keys from `${SUPABASE_URL}/auth/v1/.well-known/jwks.json`, caches 1 hour, verifies tokens with `audience="authenticated"`.
- `SUPABASE_JWT_SECRET` no longer required.

### Frontend (Next.js 14 App Router)
Kept routes:
- `/` (rebranded landing — editorial minimalist, earth-tone + neutral)
- `/dashboard`, `/dashboard/resume`, `/dashboard/resume/[id]/edit`, `/dashboard/resume/tailor`, `/dashboard/credits`, `/dashboard/applications`, `/dashboard/jobs`, `/dashboard/profile`, `/dashboard/settings`
- `/docs`, `/privacy-policy`, `/terms`, `/login`, `/onboarding`

Removed in Phase 0: `/dashboard/activity`, `/dashboard/referrals`, `/dashboard/resume-evaluation` (redirects configured in `next.config.mjs`).
Settings trimmed to **Privacy** + **Change History** only.

### Frontend typography (merged via PR #6, 2026-05-26)
- **Display headlines / wordmark / nav** — Humane variable typeface (`public/fonts/HUMANE Typeface/Variable-TT/Humane-VF.ttf`)
- **Section H2s, card titles, FAQ Qs** — Fraunces (serif, optical-size, italic)
- **Body / UI / labels / buttons / footer / marquee** — Geist Sans (Vercel's typeface)
- Earth-tone palette (terracotta/sage/sand/charcoal) in light mode; cool near-black `#0d0d0d` neutral in dark mode.

### Database & infra
- **Supabase** (Postgres 17 + Auth + Storage + Row-Level Security).
- **pg_cron** for the monthly credit grant — replaces Celery as of 2026-05-29. Single SQL function `grant_monthly_credits()` scheduled at midnight UTC on the 1st of each month. Idempotent per `(user, month)` via `credit_ledger.external_ref` unique constraint. See `docs/supabase-pg-cron-setup.md` for one-time setup.
- **Alembic** migrations — note: the migration chain has accumulated branches and is bootstrapped on fresh DBs via `Base.metadata.create_all()` + `alembic stamp head`. A baseline squash is in TECH_DEBT.md.
- **Storage bucket** name: `resume` (env-overridable via `SUPABASE_STORAGE_BUCKET`).
- **RLS policies** on every user-owned table (`resume_documents`, `resume_evaluations_v2`, `resume_versions`, `jd_evaluations`, `credit_ledger`, `resume_exports`). Storage policies enforce per-user folder isolation.
- **No async task queue.** All LLM calls return synchronously. There are no long-running background jobs in the active feature set.

### Local dev
- **Makefile** at repo root: `make dev` runs backend + frontend together; `make stop` kills both; `make test`, `make lint`, `make migrate`, `make clean` available.
- Backend env loaded via `load_dotenv()` at `app/main.py` startup — no `--env-file` flag required.
- **Pre-push hook** (`lefthook.yml`) runs backend pytest + frontend vitest with coverage gates before every `git push`. Bypass with `--no-verify`.

### CI
- GitHub Actions workflow at `.github/workflows/ci.yml`.
- Backend: ruff lint (advisory — see TECH_DEBT), pytest SQLite default, pytest Postgres for concurrency-sensitive paths, Playwright Chromium install for PDF render tests. **Coverage gate at 80%**.
- Frontend: lint, build, tsc (`continue-on-error` — pre-existing TS errors tracked in TECH_DEBT), vitest with coverage. **Coverage gate at 80% lines / 75% branches / 72% functions**.

### Production deploy (Railway)
- **SQLALCHEMY_DATABASE_URI** must use Supabase **session pooler** (`aws-0-<region>.pooler.supabase.com:5432`) — Railway containers can't reach Supabase's direct connection (IPv6-only).
- Username on pooled URI: `postgres.<project_ref>` (tenant routing).
- See README "Local development" → Required env vars + Supabase Dashboard → Project Settings → Database → "Session pooler" for canonical URI.

---

## Engineering principles learned

- **Context is king.** The model needs the right user context (experience level, target role, JD) injected without blowing the token budget.
- **Structured AI beats free-form.** Pydantic schemas turned unreliable generation into a reliable data pipeline.
- **Compliance is engineering.** Google OAuth verification / Limited Use Policy required real refactoring.
- **Hallucination is a runtime guard, not a prompt-only concern.** Regex on rewriter + tailor outputs is the last line of defense.
- **Multi-agent fan-out is theater for resume eval.** Five specialized passes through one well-prompted model beats a panel of agents debating.
- **Storage MUST be persistent.** Railway ephemeral filesystem cost us a P0 in staging — Supabase Storage migration was non-negotiable.

---

## Plans & specs

**Specs (`docs/superpowers/specs/`):**
- `2026-05-19-prism-pro-pivot-design.md` — pivot from job tracker to resume polish platform
- `2026-05-25-tailor-apply-preview-export-design.md` — Apply→Preview→Export pipeline
- `2026-05-26-comprehensive-test-coverage-design.md` — tiered coverage gates + dead-code culling

**Plans (`docs/superpowers/plans/`):**
- `2026-05-19-prism-pro-phase-0-cleanup.md`
- `2026-05-19-prism-pro-resume-backend-phase-1.md`
- `2026-05-19-prism-pro-phase-4-production-hardening.md`
- `2026-05-20-prism-pro-phase-2-pdf-render.md`
- `2026-05-20-prism-pro-frontend-phase-3.md`
- `2026-05-25-tailor-apply-preview-export-plan.md`
- `2026-05-26-comprehensive-test-coverage-plan.md`

**Other refs:**
- Tech debt: `TECH_DEBT.md`
- Production blockers: `BLOCKERS.md`
- Frontend rebrand audit: `frontend/REBRAND_AUDIT.md`
- Progress tracker: `progress.txt`

---

## Status (2026-05-27)

| Phase | Status |
|---|---|
| Phase 0 — Cleanup | ✅ merged to main |
| Phase 1 — Backend foundation | ✅ merged to main |
| Phase 2 — PDF render + 6 templates | ✅ merged to main |
| Phase 3 — Frontend resume + JD + credits UI | ✅ merged to main |
| Phase 4 — Plan + fixtures + CI | ✅ merged to main |
| Phase 4 — Production hardening (12 tasks) | ✅ merged to main |
| ES256 JWT migration | ✅ merged to main |
| Fresh Supabase project bootstrap | ✅ completed |
| Tailor Apply → Preview → Export pipeline | ✅ merged to main (2026-05-26, PR #7) |
| Welcome credits + profile bootstrap + auth hardening | ✅ merged to main (2026-05-26, PR #7) |
| Analytics endpoint (JD progress funnel) | ✅ merged to main (2026-05-26, PR #7) |
| Frontend editorial rebrand | ✅ merged to main (2026-05-26, PR #6) |
| Comprehensive test coverage (26 tasks) | ✅ merged to main (2026-05-26, PR #8) |
| Railway Supabase pooler fix + env validation cleanup | ✅ merged to main (2026-05-27, PR #9) |

## Test coverage (2026-05-27)

- **Backend pytest:** 157 pass, 12 skip — **86.7% coverage** (gate at 80%)
- **Frontend vitest:** 44 pass across 15 test files — **83.6% lines / 75.3% branches / 72.7% functions** (gate at 80/75/72)
- **Frontend e2e (Playwright):** 25-test suite, cookie-based auth bypass gated to non-prod
- **Pre-push hook** (lefthook): runs both suites + coverage gates before every `git push`. Bypass with `--no-verify`.
- **Core Prism Pro paths (high coverage):**
  - API endpoints: `analytics` 100%, `credits` 100%, `admin_metrics` 100%, `exports` 96%, `jd` 93%, `resumes_v2` 91%, `webhooks` 84%
  - Services: `hallucination_guard` 100%, `evaluator` 100%, `rewriter` 100%, `parser` 94%, `extractor` 95%, `tailor` 97%, `template_engine` 97%, `renderer` 81%, `supabase_storage` 89%, `ledger` 94%, `stripe_webhook_handler` 91%
  - Schemas: `jd` 100%, `resume_v2` 100%, `resume_export` 100%
  - `core/auth.py`: 92% (added unit tests for `_ensure_user_row`, JWKS, dependency wiring)
  - Frontend hooks (all): 100% — `useTailorApply`, `useExportPdf`, `useJdAnalyze`, `useCreditsBalance`; `use-resume` at 54%
  - Frontend API clients (all): 100% — `resume-v2`, `jd`, `exports`, `credits`
- **Excluded from coverage gate** (`.coveragerc`): legacy job-tracking routes + infra wrappers + legacy ORM models (21 files)
- **Coverage gaps remaining:** `frontend/use-resume.ts` 54% lines (additional mutations untested), 3 components with function coverage below 75% (tracked in TECH_DEBT)
