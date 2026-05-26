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

### Frontend typography (in-progress branch: `feat/frontend-content-rebrand`)
- **Display headlines / wordmark / nav** — Humane variable typeface (`public/fonts/HUMANE Typeface/Variable-TT/Humane-VF.ttf`)
- **Section H2s, card titles, FAQ Qs** — Fraunces (serif, optical-size, italic)
- **Body / UI / labels / buttons / footer / marquee** — Geist Sans (Vercel's typeface)
- Earth-tone palette (terracotta/sage/sand/charcoal) in light mode; cool near-black `#0d0d0d` neutral in dark mode.

### Database & infra
- **Supabase** (Postgres 17 + Auth + Storage + Row-Level Security).
- **Redis + Celery** for background tasks (`resume_tasks`, `job_extraction_tasks`, `credit_tasks`).
- **Alembic** migrations — note: the migration chain has accumulated branches and is bootstrapped on fresh DBs via `Base.metadata.create_all()` + `alembic stamp head`. A baseline squash is in TECH_DEBT.md.
- **Storage bucket** name: `resume` (env-overridable via `SUPABASE_STORAGE_BUCKET`).
- **RLS policies** on every user-owned table (`resume_documents`, `resume_evaluations_v2`, `resume_versions`, `jd_evaluations`, `credit_ledger`, `resume_exports`). Storage policies enforce per-user folder isolation.

### Local dev
- **Makefile** at repo root: `make dev` runs backend + frontend together; `make stop` kills both; `make test`, `make lint`, `make migrate`, `make clean` available.
- Backend env loaded via `load_dotenv()` at `app/main.py` startup — no `--env-file` flag required.

### CI
- GitHub Actions workflow at `.github/workflows/ci.yml`.
- Backend: ruff lint (advisory — see TECH_DEBT), pytest SQLite default, pytest Postgres for concurrency-sensitive paths, Playwright Chromium install for PDF render tests.
- Frontend: lint, build, tsc (`continue-on-error` — pre-existing TS errors tracked in TECH_DEBT).

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

- Pivot spec: `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md`
- Phase 0 cleanup: `docs/superpowers/plans/2026-05-19-prism-pro-phase-0-cleanup.md`
- Phase 1 backend: `docs/superpowers/plans/2026-05-19-prism-pro-resume-backend-phase-1.md`
- Phase 4 production hardening: `docs/superpowers/plans/2026-05-19-prism-pro-phase-4-production-hardening.md`
- Tech debt: `TECH_DEBT.md`
- Production blockers: `BLOCKERS.md` (Phase 2 PDF renderer failures, items §P2)
- Frontend rebrand audit: `frontend/REBRAND_AUDIT.md`

---

## Status (2026-05-26)

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
| Tailor Apply → Preview → Export pipeline | ✅ merged to main (2026-05-26) |
| Welcome credits + profile bootstrap + auth hardening | ✅ merged to main (2026-05-26) |
| Analytics endpoint (JD progress funnel) | ✅ merged to main (2026-05-26) |
| Frontend editorial rebrand | 🚧 in progress on `feat/frontend-content-rebrand` |

## Test coverage (2026-05-26)

- **Backend pytest:** 127 pass, 12 skip, 45% overall coverage
- **Frontend vitest:** 5/5 pass (`PreviewPanel` component tests)
- **Core Prism Pro paths (high coverage):**
  - API endpoints: `analytics` 100%, `credits` 100%, `admin_metrics` 100%, `exports` 96%, `jd` 93%, `resumes_v2` 91%, `webhooks` 84%
  - Services: `hallucination_guard` 100%, `evaluator` 100%, `rewriter` 100%, `parser` 94%, `extractor` 95%, `tailor` 97%, `template_engine` 97%, `renderer` 81%, `supabase_storage` 89%, `ledger` 93%, `stripe_webhook_handler` 79%
  - Schemas: `jd` 100%, `resume_v2` 100%, `resume_export` 100%
- **Low coverage (acceptable — legacy/demoted code):** `jobs.py` 17%, `job_extraction.py` 29%, `profiles.py` 16%, `url_job_extractor.py` 11%, `job_matcher.py` 0%, `supabase_cache_service.py` 0%, `supabase_task_queue.py` 0%, `resume_tasks.py` 0% (Celery), `consolidated_resume_evaluator.py` 0% (removed in Phase 0 but file remains)
- **Gap to address:** `core/auth.py` at 35% — newly added `_ensure_user_row()` lacks direct unit tests (covered via integration tests)
