# Local infrastructure and dependency boundaries

PRI-17 removes unused orchestration and the retired Gmail integration. It does
not change hosted infrastructure, authentication, billing, migrations or data.

## Supported services

`docker-compose.yml` declares frontend, backend and PostgreSQL only. There is no
Celery app or Redis consumer in the current backend, so no worker, broker or
`REDIS_HOST` setting is required. Removing the old volume declaration does not
delete an existing Docker volume. Do not run volume-pruning commands as part of
this upgrade.

The existing Compose file is not a complete credential/bootstrap recipe. Supply
the database URI and provider configuration described in `backend/.env.example`
and the frontend environment template; its `POSTGRES_*` values alone do not
configure the backend's `SQLALCHEMY_DATABASE_URI`. Native development remains
`make dev` with local environment files. Do not copy production secrets into Git.

## Python dependencies

- `backend/requirements.in` owns top-level requirements and security floors.
- `backend/requirements.txt` includes that file for compatibility; it no longer
  maintains a second, drifting copy of the ranges.
- CI and Docker install `backend/requirements.lock` with Python 3.11.
- From `backend`, regenerate with
  `python3.11 -m piptools compile --no-strip-extras --output-file=requirements.lock requirements.in`.
  Do not use `--upgrade` for a removal-only change; review retained versions and
  run the dependency audit.

PRI-17 includes one owner-approved security exception: Soup Sieve is raised from
2.8.4 to 2.9.0 for GHSA-j934-xhv5-fg8f and GHSA-gjv8-xp57-g29c. Its explicit
security floor prevents resolving an affected release again. All other retained
locked versions remain unchanged.

For the subsequent PRI-65 `pypdf` security update and its complete dependency
audit/compatibility evidence, see [Dependency security repair](dependency-security.md).

The Google/Gmail Python SDK family and its orphan transitives are removed after
import/consumer review. Backend-only `GOOGLE_*` Gmail settings, email processing
thresholds and `ENABLE_EMAIL_SCANNING` are no longer recognized. Old environment
entries are ignored by Settings; no live credentials are revoked or changed.

Google sign-in remains the frontend Supabase OAuth flow, with backend JWT
validation via PyJWT/cryptography. Configure the Google provider in Supabase;
the retired backend Gmail SDK is not part of this flow. See the
[Supabase Google sign-in guide](https://supabase.com/docs/guides/auth/social-login/auth-google)
(checked 2026-09-17).

Stripe and `ENABLE_BILLING=false` remain unchanged. BeautifulSoup remains because
optional URL job extraction imports it. Resend remains a separately reserved
transactional integration, not evidence that an email automation worker runs.
Broader historical documentation cleanup is tracked in PRI-18.

## Verification and rollback

Run `docker compose config --quiet`, `make verify-backend-ci` and
`make verify-contracts`. A clean environment installed from the lock must run
startup and backend tests without any retired Google/Gmail packages installed.
Docker build and hosted PostgreSQL/secret-scanning gates are still required.

Rollback restores the prior Compose/dependency/configuration files and rebuilds
the environment. No database migration or data restoration is required.
