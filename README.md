# Prism Pro - AI-Powered Resume Polish & JD Tailoring

A focused, AI-powered career toolkit that helps job seekers polish resumes and tailor them to specific job descriptions. Built for SWE, Data Science, and PM candidates targeting roles in the USA and India.

## What Prism Pro does (current pivot)

Prism Pro is being refocused around two primary capabilities, with job tracking demoted to a supporting role.

### Primary features

- **Resume Polish** - Upload a resume; receive a structured, evidence-based critique covering ATS compatibility, bullet quality (XYZ formula), 7-second scan rule, and section ordering. Specialized passes for SWE / DS / PM templates.
- **JD-Driven Tailoring** - Paste a job description; Prism Pro generates targeted rewrites of your bullets, keyword recommendations, and a coverage report against the JD.

### Supporting feature (demoted, kept)

- **Job Tracking** - Lightweight applications board (`/dashboard/applications` + `/dashboard/jobs`) for tracking saved roles. URL-based job extraction retained.

### Deferred / out of scope (Phase 1)

- Voice interview prep
- Browser extension
- Email automation, Gmail scanning, referrals, contact discovery, analytics dashboards

## Phase 1 backend API surface

Phase 1 (resume backend) exposes 6 endpoints under `/api/v1/resumes/`. See the umbrella spec at `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md` for the full contract.

## Tech stack

### Frontend
- **Next.js 14** (App Router), **TypeScript**, **Tailwind CSS**
- **Framer Motion** for animations
- **Radix UI** primitives + custom design system

### Backend
- **FastAPI** (Python) - async, high-performance
- **Supabase** (PostgreSQL) + Row Level Security
- **Manual JWT handling** for stateless auth
- **Redis + Celery** for background AI tasks

### AI
- **OpenAI GPT-4o / GPT-4o-mini** with Pydantic-validated structured outputs
- Single-agent architecture with specialized passes (refactored away from the prior 12-agent system)

## Prerequisites

- Node.js 18+
- Python 3.9+
- PostgreSQL (Supabase)
- Redis
- OpenAI API key

## Quick start

```bash
git clone https://github.com/yourusername/prism-pro.git
cd prism-pro
cp .env.example .env  # edit with your credentials
docker-compose up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Project structure

```
prism-pro/
├── frontend/                  # Next.js app
│   └── src/app/dashboard/     # Dashboard, jobs, applications, settings, profile
├── backend/                   # FastAPI app
│   └── app/
│       ├── api/v1/endpoints/  # jobs, profiles, resumes, user_profiles, logs, job_extraction
│       ├── services/          # job_scorer, url_job_extractor, ai_service, resume services
│       └── tasks/             # resume_tasks, job_extraction_tasks (Celery)
└── docs/superpowers/          # Specs and execution plans
```

## Documentation

- Pivot spec: `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md`
- Phase 0 cleanup plan: `docs/superpowers/plans/2026-05-19-prism-pro-phase-0-cleanup.md`
- Phase 1 backend plan: `docs/superpowers/plans/2026-05-19-prism-pro-resume-backend-phase-1.md`

## Phase 1 — Resume + JD Backend (in progress)

New REST endpoints (v1):
- `POST /api/v1/resumes/upload` — upload PDF/DOCX, returns parsed JSON
- `POST /api/v1/resumes/{id}/evaluate` — single-agent eval + ATS sim (costs 1 credit)
- `POST /api/v1/resumes/{id}/rewrite/{bullet_id}` — hallucination-guarded bullet rewrite (free)
- `POST /api/v1/resumes/{id}/versions` — apply accepted changes, save new version
- `POST /api/v1/jd/analyze` — extract JD requirements + tailor diff plan (costs 2 credits)
- `GET /api/v1/credits/balance`

Architecture: see `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md`.

## Phase 2 — PDF Render (in progress)

New REST endpoints (v1):
- `POST /api/v1/exports` — render a resume document (optionally a specific version) to PDF using a country+role template, upload to Supabase Storage, return signed download URL. Costs 1 credit; refunded on hard render failure.
- `GET /api/v1/exports/{id}` — return a fresh signed download URL for an existing successful export. Zero-cost.

Templates: 6 HTML+CSS templates under `backend/app/services/pdf/templates/` (us|in × swe|ds|pm). Rendering uses headless Chromium via Playwright (`backend/app/services/pdf/renderer.py`); sync renderer is offloaded via `run_in_executor` from async endpoints.

Phase 2 plan: `docs/superpowers/plans/2026-05-20-prism-pro-phase-2-pdf-render.md`.
Architecture: see `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md` §7.7.

## Security

- All secrets in env vars (never committed)
- Supabase RLS isolates user data
- Rate limiting on all endpoints
- Pydantic validation on every request
