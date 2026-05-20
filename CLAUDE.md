# Prism Pro - Project Documentation (Pivot Scope)

**Prism Pro** is an AI-powered resume polish and JD tailoring platform for job seekers. The codebase is being refocused: resume tooling is now the headline product, job tracking is demoted to a supporting feature, and a number of legacy modules (email automation, referrals, contact discovery, analytics dashboards, multi-agent evaluator) have been removed.

For the canonical scope, see `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md`.

---

## Current scope

### Primary (Phase 1)
- **Resume Polish** - Structured, evidence-based resume critique. ATS compliance, XYZ-formula bullet checks, 7-second scan rule, section ordering. Specialized passes for SWE / DS / PM.
- **JD-Driven Tailoring** - Paste a job description; receive targeted bullet rewrites, keyword coverage, and a coverage report.

### Supporting (kept, demoted)
- Job tracking under `/dashboard/applications` and `/dashboard/jobs`.
- URL-based job extraction (Jina AI Reader + GPT-4o-mini).

### Deferred / not in scope
- Voice interview prep
- Browser extension
- Email automation, Gmail scanning, weekly digests
- Referral templates, contact discovery (Apollo)
- Analytics intelligence dashboards
- Multi-agent resume evaluation (replaced by single-agent + specialized passes)

### Geography & personas
- MVP targets: USA + India
- Personas: SWE, Data Science, PM

---

## Architecture

### AI - "Precision over Complexity"
The earlier multi-agent system (12+ agents) was retired. Current approach:
- **Single-agent core** with specialized passes for ATS, XYZ-formula, scan-rule, and JD-keyword coverage.
- **Pydantic-validated structured outputs** for every model call - the AI is a data processor, not a creative writer.
- Models: GPT-4o-2024-08-06 for evaluation, GPT-4o-mini for extraction / cheaper passes.
- Hyper-Critical Sr. Hiring Manager persona for resume critique.

### Backend (FastAPI)
Routes that remain after Phase 0:
- `jobs.py` - job CRUD
- `profiles.py` + `user_profiles.py` - user profile data
- `job_extraction.py` - URL-based job extraction
- `resumes.py` - resume CRUD (evolves into Phase 1 endpoints)
- `logs.py` - logging

Removed in Phase 0:
- Email services (Resend, SendGrid, email_service), email templates
- Referral services (simple_referral_service, apollo_client, contact_discovery), `simple_referrals` endpoint
- `activity` endpoint + `ActivityRecord` model
- Analytics services (analytics_service, analytics_intelligence), `job_aggregator`, `question_answer_service`
- Celery tasks: `email_monitoring_tasks`, `email_scanning_tasks`, `analytics_tasks`, `feedback_collector`

### Frontend (Next.js 14 App Router)
Routes kept:
- `/dashboard`, `/dashboard/jobs`, `/dashboard/applications`, `/dashboard/profile`, `/dashboard/settings`
- `/docs`, `/privacy-policy`, `/terms`, `/login`, `/onboarding`

Routes removed in Phase 0:
- `/dashboard/activity`, `/dashboard/referrals`, `/dashboard/resume-evaluation` (redirects to `/dashboard` configured in `next.config.mjs`)

Settings tabs trimmed to **Privacy** + **Change History** only (email/notifications tabs removed).

### Database & infra
- Supabase (Postgres + RLS) for primary data.
- Redis + Celery for background AI tasks (`resume_tasks`, `job_extraction_tasks`).
- Manual JWT handling on top of Supabase auth.

---

## Engineering principles learned

- **Context is king.** The model needs the right user context (experience level, target role, JD) injected without blowing up tokens.
- **Structured AI beats free-form.** Pydantic schemas turned unreliable generation into a reliable data pipeline.
- **Compliance is engineering.** Google's OAuth verification / Limited Use Policy required real refactoring (scope reduction, privacy policy).

---

## Plans & specs

- Pivot spec: `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md`
- Phase 0 cleanup (this branch): `docs/superpowers/plans/2026-05-19-prism-pro-phase-0-cleanup.md`
- Phase 1 backend: `docs/superpowers/plans/2026-05-19-prism-pro-resume-backend-phase-1.md`
