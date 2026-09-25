# PrismPro deployment entrypoint

Updated for PRI-25 against main `f1d17a9` on 2026-09-25. This guide replaces the old
multi-provider/Redis recipe; it does not authorize a deployment.

## Supported topology and release modes

- Frontend and one backend instance/process, with PostgreSQL and Supabase Auth/Storage.
- No Redis, Celery or Gmail worker. [Local Compose](docs/local-infrastructure.md)
  is a development skeleton, not a production credential/bootstrap recipe.
- Keep billing off and both public-preview flags true on the public deployment.
- Test authenticated product paths on a separate internal deployment.
- Multi-instance operation needs an approved shared/edge abuse-control design and
  load verification first; adding a broker alone does not satisfy that gate.

The [production runbook](docs/production-mvp-runbook.md) owns environment,
OAuth, Storage, RLS, waitlist and smoke procedures. The
[release checklist](DEPLOYMENT_READINESS_CHECKLIST.md) records required evidence.
Do not substitute old email/Celery documents or a provider's quick deploy button.

## Safe migration procedure

1. Identify the authorized target environment and verify a recoverable backup and
   migration-specific rollback plan before any production write.
2. Inspect `backend/migrations/versions` and run the chain on an isolated clean
   PostgreSQL database and a representative existing-schema staging database.
3. Inspect current revision and expected heads from the backend directory:
   `python -m alembic current` and `python -m alembic heads`.
4. With explicit operator approval, configure the verified backend Railway
   service's **Pre-Deploy Command** as `sh scripts/migrate.sh` (working directory
   `/app`) and a reviewed timeout. Confirm the selected image contains the
   script and that the service's approved database credential can apply the
   migration. The pre-deploy step must complete before the new web deployment
   starts; record the target, revision, result, timestamp and reviewer. For a
   deliberate local or staging run, use `make migrate` or the same script from
   `backend/` against that explicit target.
5. Recheck schema, RLS, grants, Storage isolation and required scheduled jobs using
   the runbook. A matching revision number alone does not establish schema parity.

On failure, stop. Do not mark an unexecuted migration as applied, bootstrap tables
from ORM metadata, delete revision history, or weaken access controls to continue.
Prepare a reviewed repair migration or reconciliation plan instead.
Alembic stamping updates revision metadata without running migrations; see the
[official command reference](https://alembic.sqlalchemy.org/en/latest/api/commands.html#alembic.command.stamp)
(checked 2026-09-18).

The web command `sh scripts/start.sh` performs only a read-only Alembic
`current --check-heads` check before Uvicorn. `RUN_DB_MIGRATIONS` no longer
enables startup writes. An unmigrated schema prevents that instance from
serving. Railway's pre-deploy command runs in a separate container with the
service environment; a nonzero exit stops that deployment before the new
instance starts. Verify this setting on the actual PrismPro backend service:
this repository has no Railway service configuration, and adding deprecated
`railway.json` would not reliably configure a new service. Do not treat the
script's presence as proof that the hosted pre-deploy gate is enabled.

## Release and rollback

Require the applicable hosted CI jobs, image build for the actual Dockerfile being
deployed, explicit human review and environment-specific smoke evidence.
CI builds `backend/Dockerfile`, `frontend/Dockerfile`, and the root multi-stage
`Dockerfile`. It smokes the backend process in both backend-capable images;
verify the exact selected image and environment again before deployment.
Do not infer deployed state from a green PR or merge.

Deploy only the approved revision after migration compatibility is confirmed.
The old application may remain live while pre-deploy runs, so migrations must
be compatible with both old and new application versions during the overlap.
If a pre-deploy step fails, stop the release and inspect whether any schema
change committed before the failure; do not retry blindly or shift traffic.
Rollback application images to a known healthy compatible revision. Database
downgrades, credit corrections and data restoration need their own reviewed plan;
never delete ledger history as a rollback shortcut. PRI-18 changes documentation
only and requires no migration or service restart.
