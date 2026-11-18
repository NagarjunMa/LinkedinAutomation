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

### PRI-33 Interview schema rollback

The previous backend expects `2026_11_13_career_sources`. After applying
`2026_11_14_career_interviews`, follow the same recovery sequence as PRI-32
with the following revision and data checks:

- With empty interview tables, pause schema releases and interview traffic.
  Use the PRI-33 migration image or checkout and a migration-owner connection
  in READ COMMITTED. From `backend/`, run
  `python -m alembic downgrade 2026_11_13_career_sources`. Verify startup with
  the previous checkout's `python -m alembic current --check-heads` and check
  `/health` before restoring traffic.
- With saved interviews or messages, retain the schema and use a corrective
  build that recognizes the current migration head. The downgrade fails
  before dropping either table if interview data is present.

Keep the production preview's database role and route restrictions in place.
Before enabling authenticated interview traffic in a hosted environment,
verify that its runtime role can access the required tables and take the
owner-row lock. Confirm account closure and the retention policy before
collecting real transcripts.

Before writing or reading interview messages, configure a persistent
`CAREER_TRANSCRIPT_KEY` in the authenticated backend's secret store. Generate a
separate key per environment with
`python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`.
Share that environment's key across its authorized backend replicas and preserve
it through restart and rollback. The database stores encrypted transcript text.
If rotation is needed, preserve the old key and plan re-encryption before
changing it. The public preview and migration process do not need the key.

### PRI-34 Career Evidence ledger

Apply `2026_11_14_career_evidence` before starting the corresponding web image.
Authenticated evidence requests reuse `CAREER_TRANSCRIPT_KEY` for encrypted
claims, source details and decision reasons. Confirm the authenticated runtime
can read and append ledger records, lock owner and source rows, and delete
linked evidence when deleting a source or résumé. The deletion trigger uses
the caller's privileges, including the privilege needed to lock an evidence
row. Keep direct Data API privileges revoked and rehearse owner isolation,
résumé deletion and account closure with synthetic identities before collecting
real evidence.

If the ledger is empty, pause evidence writes and source, résumé, and account deletions. Run
`python -m alembic downgrade 2026_11_14_career_interviews` from the PRI-34 build
using the migration-owner connection in READ COMMITTED. Verify the prior
image's head and `/health` before promoting it. If the ledger contains data,
preserve the schema and key and use a corrective build that supports the current
head. The downgrade refuses to drop a populated ledger.

### PRI-35 Career run and artifact lineage

Apply `2026_11_14_career_lineage` before starting the matching backend. Keep
the persistent `CAREER_TRANSCRIPT_KEY` for run metadata. In development, use
synthetic records to verify runtime access, revoked Data API grants, owner
isolation, invalidation after evidence changes, and deletion cascades.

If the lineage tables are empty, pause metadata writes and related deletions.
Use the migration-owner connection at READ COMMITTED to run
`python -m alembic downgrade 2026_11_14_career_evidence`. Verify the previous
image's Alembic head and `/health`. With saved metadata, preserve the schema
and key and deploy a corrective image that supports the current head.

### PRI-40 Authenticated Career turn streaming

Apply `2026_11_16_career_turns` before starting the corresponding backend.
Keep `CAREER_TURNS_ENABLED=false` for the first deployment and for the public
preview. In development, verify the disabled endpoint returns 503 for an
authenticated request, then enable it on the authenticated backend for a
two-account smoke test. Use the existing persistent `CAREER_TRANSCRIPT_KEY`.
The runtime connection must use transactional PostgreSQL READ COMMITTED and
allow the application to lock the owner and write the interview and run tables.
Preserve the restricted public-preview database role and revoked Data API grants.

Test browser POST streaming with synthetic messages. Verify that status events
arrive during processing, the final reply is available through the existing
session and messages endpoints, and the second account gets 404 on the first
account's session. Start with deterministic fallback. Optional model testing
requires the existing AI configuration and a separate persistent
`CAREER_MODEL_SAFETY_KEY`. The Railway release packages the reviewed commit
with the backend so the model run can record it. Confirm the retention and
account-deletion workflow before handling real transcripts.

- **Disable the feature:** Set `CAREER_TURNS_ENABLED=false` and restart the
  current backend or a corrective build that recognizes the current head.
  Confirm `/health`, the disabled endpoint, and access to existing transcripts.
- **Restore a pre-PRI-40 image:** Its startup check requires
  `2026_11_14_career_lineage`. Disable admissions and quiesce turn processing
  first. Before any PRI-40 turn records exist, the PRI-40 migration checkout
  can run `python -m alembic downgrade 2026_11_14_career_lineage` with the
  migration-owner connection in READ COMMITTED. Verify the prior checkout
  with `python -m alembic current --check-heads` and `/health` before restoring
  traffic. Once a turn record exists, retain the migration and the transcript
  key and use the flag-off or corrective build. The downgrade refuses to
  discard saved admission metadata.

### PRI-41 Career turn interruption recovery

Apply `2026_11_16_career_recovery` before starting the corresponding backend.
Keep `CAREER_TURNS_ENABLED=false` for the public preview. In the authenticated
development environment, use a synthetic account and the same message key and
payload to verify an in-flight duplicate, completed replay, disconnect, expiry,
reconnect, and explicit retry. Confirm that another account cannot read or
retry the turn. Keep the existing transactional PostgreSQL READ COMMITTED
configuration and persistent transcript key.

The turn POST reports `turn.pending`, `turn.interrupted`, or `turn.replayed`
for previously used keys. Use the reported state version and `retry: true` to
recover an interrupted turn when `can_retry` is true. Recovery keeps the original
message and uses deterministic fallback. The server refunds unused token
capacity once and keeps the reservation for work that may have reached the
provider. Existing PRI-40 completed turns remain readable and can be replayed
with their saved content and an omitted stage. Legacy interrupted turns have
no recorded state or dispatch fence and remain visible in the transcript.

For rollback, disable turns and wait for current work to finish or its lease
to expire. Before any PRI-41 turn is admitted, the migration owner can
downgrade to `2026_11_16_career_turns` in READ COMMITTED. Verify the prior
image's Alembic check and `/health`. Once an admission exists, keep the active
revision and transcript key and use a compatible backend with turns disabled.
The downgrade guard preserves the recovery records.

### PRI-44 Career Evidence decisions

Apply `2026_11_18_evidence_measurement` with the migration-owner connection
before starting the matching backend. Preserve the environment's
`CAREER_TRANSCRIPT_KEY`. In development, verify legacy evidence reads,
synthetic owner decisions and cross-account denial, stale-revision rejection,
and the invalidation of artifacts tied to the edited revision.

For rollback, pause evidence decision writes. If no revision contains
measurement metadata, use the PRI-44 migration checkout and a READ COMMITTED
migration-owner connection to run
`python -m alembic downgrade 2026_11_16_career_recovery`. Verify the prior
image's `alembic current --check-heads` and `/health` before restoring traffic.
Once any revision contains a measurement, retain the active head and key.
Use a corrective backend that recognizes the head and preserves measurement
metadata on subsequent decisions. The downgrade guard also protects measurements
on historical revisions.
