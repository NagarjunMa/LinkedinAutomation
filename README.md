# PrismPro

PrismPro currently provides resume parsing, document diagnostics, JD analysis,
reviewable tailoring, saved versions and PDF export. The approved direction is a
career-evidence product: application rules select eligible facts; an optional LLM
may propose wording, never invent or confirm evidence.

## Release status

The public deployment is intended to remain **preview-only**:
`PRISM_PRO_PUBLIC_PREVIEW_ONLY=true` on frontend and backend. Existing product
code is not evidence of public availability or launch approval. Billing remains
disabled. Use a separate local/internal environment for authenticated product QA.

The Career Evidence controller, canonical evidence ledger and deterministic
bullet-plan renderer are target architecture, not claims about today's
implementation. Document diagnostics and JD coverage are not external ATS
rankings, hiring probabilities or guarantees of factual grounding.

## Start here

- [Documentation index](docs/README.md): supported guides versus historical material.
- [Architecture and durable planning](docs/architecture.md): approved Linear specifications.
- [Deployment entrypoint](DEPLOYMENT.md), [production runbook](docs/production-mvp-runbook.md)
  and [release checklist](DEPLOYMENT_READINESS_CHECKLIST.md).
- [Known gaps](BLOCKERS.md): source-backed findings, not a launch certificate.
- [API contracts](docs/api-contracts.md) and [model/prompt manifests](docs/model-manifests.md).

## Current stack

Checked against repository manifests on 2026-09-18; these are installed targets,
not claims that they are the latest available versions.

| Layer | Repository target / authority |
| --- | --- |
| Frontend | Next.js 16.3.4, React 19.2.7, TypeScript; [package manifest](frontend/package.json) and [lock](frontend/package-lock.json) |
| Backend | Python 3.11, FastAPI 0.138.0, Pydantic 2.13.4, SQLAlchemy 2.0.51; [lock](backend/requirements.lock) |
| Persistence | PostgreSQL, Alembic 1.18.4; Supabase Auth and private Storage |
| PDF | Jinja2 templates and Playwright Chromium |
| CI runtime | Python 3.11, Node 22, PostgreSQL 15; [workflow](.github/workflows/ci.yml) |

The supported topology is frontend, backend and PostgreSQL, with hosted Supabase
Auth/Storage. No Redis service, Celery worker or Gmail automation is required.
See [local infrastructure](docs/local-infrastructure.md) for dependency ownership
and Compose limitations. Monthly credits use database scheduling, not Celery;
the schedule and safety checks require separate operator verification.

## Local setup

Use Python 3.11 and Node 22. Create a virtual environment, then install the locked
dependencies from the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.lock
npm --prefix frontend ci
python -m playwright install chromium
```

Create `backend/.env` and `frontend/.env.local` using
[backend settings](backend/.env.example) and the
[frontend template](frontend/.env.example). Never overwrite existing local files
or commit credentials. Use an isolated development database and provider project,
not production data. URL-encode database credentials; do not weaken passwords.

For authenticated local product testing, explicitly set
`PRISM_PRO_PUBLIC_PREVIEW_ONLY=false` in **both** files, use
`NEXT_PUBLIC_API_URL=http://localhost:8000`, and allow that local frontend origin
in backend CORS. Configure local OAuth as described in the
[runbook](docs/production-mvp-runbook.md#oauth-redirects), then restart both servers.
Do not change the public deployment's preview flags.

Initialize the development database through the reviewed Alembic chain:

```bash
cd backend
python -m alembic upgrade head
cd ..
make dev
```

This starts the backend on port 8000 and frontend on 3000. If migration fails,
stop and diagnose the revision/schema mismatch; do not bypass migrations.
The [deployment guide](DEPLOYMENT.md) defines the stricter production procedure.

## Verification

```bash
make verify              # mocked agent/service and startup sanity checks
make verify-backend-ci   # Ruff, pytest coverage, locked dependency audit
make verify-frontend-ci  # contracts, ESLint, types, build, unit/E2E, audit
make verify-ci           # both local suites
```

Use `make help` and the [Makefile](Makefile) for exact commands.
Local suites do not prove hosted PostgreSQL, Docker, secret scanning or deployed
smoke gates passed. CI supplies Ruff and pip-audit separately from the runtime
lock; match its tool versions when preparing a verification environment.
Real-provider golden tests require explicit credentials, consent and cost awareness;
they are not part of routine offline verification.

## Contribution boundaries

Read [CLAUDE.md](CLAUDE.md) and [architecture routing](docs/architecture.md) before
development. Use the verified PrismPro Linear issue as durable task context.
Preserve unrelated work; keep changes reviewable; obtain owner approval before
commit/push. A merged PR, passing tests and a production deployment are distinct
states. Do not promote any one of them into an unsupported readiness claim.

## License

Proprietary. Internal use only.
