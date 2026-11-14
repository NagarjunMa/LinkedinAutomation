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
4. Use the separate migration and web services described below after the
   environment has been switched to the split release workflow. Until then,
   retain the existing reviewed pre-deploy configuration. For a deliberate
   local or staging migration, use `make migrate` against the verified target.
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
serving.

## Release the Railway backend with separate database logins

Configure two services for the same verified Supabase database. Build both from
the reviewed `backend/Dockerfile` and the same backend source snapshot.

- **Migration service** has no public domain or health check. Set its start
  command to `true`, restart policy to Never, and pre-deploy command to
  `sh scripts/migrate.sh` with a reviewed timeout. Set its
  `SQLALCHEMY_DATABASE_URI` to the login that owns the application objects
  and can run the reviewed migrations. Existing migrations can depend on the
  current object owner and pg_cron job owner. Use `ENVIRONMENT=development`
  for the migration container's application configuration. Its database URL
  determines the database target.
- **Web service** uses the image's `sh scripts/start.sh` command and Railway
  `/health` readiness check. Clear its pre-deploy command as part of the
  credential cutover. Set its `SQLALCHEMY_DATABASE_URI` to the restricted
  login. Keep migration credentials scoped to the migration service. If the
  web service uses the Railway edge rate limiter opt-in, keep the web service
  alone in its Railway environment and configure the migration service in a
  separate environment. [Production ingress settings](docs/production-mvp-runbook.md)
- Add `sslmode=verify-full&sslrootcert=/app/certs/supabase-root-2021.crt&connect_timeout=10`
  to both URLs using the correct query separator. The image includes the
  Supabase Root 2021 public CA. Verify that the selected endpoint presents a
  certificate for its configured hostname. [Supabase TLS guidance](https://supabase.com/docs/guides/platform/ssl-enforcement)

For the public-preview web service, create a fresh PostgreSQL login without
role memberships, object ownership, administrative attributes or RLS bypass.
As the application table owner, run the following through a separately
authenticated `psql` session with the target checked first. Keep passwords
out of the command and use the approved credential store.

```sh
psql -v runtime_role=prismpro_preview_runtime -f backend/scripts/grant_preview_runtime.sql
```

The grant script gives the login access to the Alembic revision and the columns
the waitlist uses for duplicate detection and inserts. The role can read
waitlist IDs, normalized email addresses and timestamps. Free-text fields are
insert-only. The database allows up to 181 days for the 180-day retention
deadline, including clock tolerance. The owner and existing scheduled retention job remain responsible
for maintenance. Verify effective privileges across all schemas, including
rights inherited from PUBLIC, before assigning the login to Railway. These
grants apply to the public-preview web service. An authenticated backend needs
its own reviewed role.

Disable Railway GitHub autodeploys on both split services. Use the manual
[Release Railway backend workflow](.github/workflows/release-backend.yml) as the
single release lane. It serializes runs by target and uses the selected Git
revision. Configure GitHub environments `development` and `production` with
the approved deployment branch restrictions and approvals for each target. Set
the GitHub environment secret `RAILWAY_WEB_TOKEN` to a Railway project token
scoped to the web service's Railway environment. If the migration service
runs in a different Railway environment, set `RAILWAY_MIGRATION_TOKEN` to a
project token scoped to that environment. Each CLI invocation receives only
the token for its destination. [Railway token types](https://docs.railway.com/integrations/api#choosing-a-token-type) Set `RAILWAY_PROJECT_ID`,
`RAILWAY_WEB_ENVIRONMENT_ID`, `RAILWAY_MIGRATION_SERVICE_ID` and
`RAILWAY_WEB_SERVICE_ID` as environment variables. Set
`RAILWAY_MIGRATION_ENVIRONMENT_ID` when the migration service uses a separate
Railway environment. Both service instances must target the same database.

The workflow calls the release command below. For operator recovery, use the
same command after pausing other releases and confirming Railway has no
migration or web deployment in progress. From a reviewed checkout using Railway CLI 5.71 or newer, run:

```sh
python3 backend/scripts/railway_backend_release.py \
  --project <project-id> --environment <environment-id> \
  --migrator <migration-service-id> --web <web-service-id> \
  --revision <full-reviewed-commit-sha>
```

Set `--migration-environment <migration-environment-id>` when the services
use separate Railway environments in the same project. Configure both service
root directories as `/` and Dockerfile paths as `Dockerfile` for this archive.

The command packages one backend archive from the reviewed Git commit and waits
for the migration deployment it submitted to reach SUCCESS and log the Alembic
completion marker before uploading the web deployment.
The web startup revision check and Railway readiness probe are additional
release gates. If the command loses contact with Railway or times out, inspect
the deployment IDs and schema state before retrying. Run the environment's
health and product smoke checks after Railway reports success.

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

### PRI-32 Career schema rollback

Web startup checks that the database revision matches the image's Alembic head.
After `2026_11_13_career_sources` is applied, the previous backend image expects
`2026_11_11_profile_truncate` and fails its startup check against the newer head.

- **If the Career tables are empty:** Pause schema releases and quiesce Career
  writers. Use the PRI-32 migration image or checkout with the migration-owner
  connection in READ COMMITTED. From `backend/`, run
  `python -m alembic downgrade 2026_11_11_profile_truncate`. The downgrade locks
  both tables and stops if either table contains records. Verify the revision
  with `python -m alembic current`, then use the previous checkout or image to
  run `python -m alembic current --check-heads` before restoring that web build.
  Verify `/health` and the existing environment smoke checks before returning
  traffic to the restored build.
- **If either table contains records:** Retain the schema and records. Prepare
  and validate a corrective backend build that includes the active Alembic head
  and restores the required application behavior. Verify its startup check and
  smoke tests on a representative database before promotion. Keep the active
  schema revision on the database throughout recovery.
