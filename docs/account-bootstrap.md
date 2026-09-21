# Explicit account bootstrap — PRI-20

Contract established 2026-09-21 from [PRI-20](https://linear.app/prismpro/issue/PRI-20/separate-user-bootstrap-and-monthly-credits-from-authentication).
Base: `a70cdfc3011513e05e24d60b79f3c599963ea80c` (merged PRI-19).
Branch: `security/pri-20-explicit-account-bootstrap`. Risk: **Critical**;
authentication, first-account persistence and credit grants cross trust and
transaction boundaries. Full feature record; no production changes authorized.

Final verification requested after implementation:
[PRI-20 audit](account-bootstrap-audit.md) records the fresh native checks,
third independent review, acceptance mapping and remaining release gates.

## Contract and boundaries

Ordinary token authentication/authorization must not query or write application
storage. A deliberate authenticated session boundary initializes an account
idempotently. Only the validated JWT supplies identity; request bodies must not
choose another user or an entitlement amount. New account creation and its
initial current-month allowance succeed together or roll back together.

The existing PostgreSQL monthly job owns recurring allowances. Bootstrap of an
existing user never repairs/backfills a grant or changes its email. Initial and
scheduled grants share `monthly:YYYY-MM:user_id` uniqueness, using UTC. This
preserves the existing 90-credit default and configurable initial allowance.
Job configuration must use the same approved amount; no pricing change here.

Invalid authentication is 401; required-auth provider connection failures are
503 `Authentication service unavailable`; setup database failures are 503
`Account setup service unavailable`; conflicting account data is 409. Error
responses must not contain raw SQL, connection information or other user data.
Optional-auth outage semantics remain PRI-21; general ledger locking is PRI-22.

The authenticated dashboard must wait for setup before mounting feature
providers. Restored sessions are included. Failed setup offers safe manual
retry; bounded requests and obsolete-response cleanup prevent indefinite
loading or a previous identity unlocking another account's dashboard. Routine
token refresh after success must preserve mounted/unsaved dashboard state.

Non-goals: changing ownership policies, auth providers, billing, ledger schema,
preview-access policy, background infrastructure or the resume architecture.
Budget: 3–8 production files, fewer than 500 changed production lines. Tests,
documentation are recorded separately. Generated transport files are also
counted conservatively toward the production-file budget.

## Ownership and actual paths

- `backend/app/core/auth.py`: shared JWT validation and read-only identity
  dependencies. No SQLAlchemy session dependency or account initialization.
- `backend/app/application/bootstrap.py`: transaction owner; unique-insert
  coordination, verified identity after conflicts and the existing ledger service.
- `backend/app/api/v1/endpoints/bootstrap.py`: bodyless bearer-authenticated
  `POST /api/v1/auth/bootstrap`, 204 on completed/idempotent setup; safe errors.
- `backend/app/api/v1/api.py`: route registration. Existing public-preview
  middleware blocks this product endpoint before authentication/setup.
- `frontend/src/components/protected-route.tsx`:
  session boundary before DashboardProvider; identity-keyed mount, fixed-token
  request, 15-second cancellation, manual retry and no server error prose.
  The ordinary API helper intentionally resolves the latest global token;
  bootstrap binds its own token to avoid using a changed identity mid-request.
- `backend/scripts/export_openapi.py`: includes auth in offline client contracts.
- `backend/migrations/versions/2026_05_29_pg_cron_grant.py` and
  `docs/supabase-pg-cron-setup.md`: unchanged recurring grant function/runbook.

No new schema or general repository abstraction is needed. The unique account
insert coordinates concurrent first contact before the ledger mutation; one
commit makes both visible. An email collision is a conflict, not evidence of a
successful same-user bootstrap. A retry after a lost success response cannot
grant again. Browser cancellation does not cancel a server transaction; this
idempotency is required for safe retry.

## Acceptance and evaluation plan

| Criterion | Evaluation / plausible defect rejected |
| --- | --- |
| Auth makes no user/credit writes | SQL statement capture across all three identity dependencies; reject hidden setup/read calls as well as writes. |
| Concurrent first contact is idempotent | Separate PostgreSQL sessions race on one identity; require one account and one 90-credit ledger entry. SQLite alone is insufficient. |
| One monthly allowance per period | Concurrent scheduled SQL jobs and bootstrap; rerun job and assert one entry; existing-user bootstrap must not backfill. |
| Stable distinguishable failures | Real JWT client exception classes; API invalid/provider/database/conflict cases; no leaked details or side effects. |
| Atomic account + grant | Inject grant and commit failures; assert neither row persists, then retry successfully. Unique-email collision must not take over an account. |
| Reachable session integration | ProtectedRoute tests: restored session ordering, failure/retry, logout/account switch, timeout, refreshed token preserves unsaved state. |
| Existing access boundaries | Preview-denial test plus existing ownership/auth suites and repository-wide checks. |

Old tests expecting auth writes and existing-user lazy monthly backfill are
updated because PRI-20 explicitly moves those responsibilities. The old mock
race test only asserted absence of an exception; actual concurrent persistence
replaces it. Existing JWT/profile behavior remains covered.

## Compatibility, rollout and rollback

No persisted schema changes. API clients must explicitly bootstrap a validated
session before first use of account-dependent APIs. Ship the frontend gate and
backend endpoint/auth change together; independently deployed clients need the
same boundary. Do not roll out backend auth removal to an older client lacking
bootstrap. A new frontend against an older backend remains blocked on setup.

Before release, verify the approved monthly job is installed, scheduled, healthy
and configured with the intended allowance using the existing runbook. Accounts
missing the current grant require the approved idempotent backfill procedure;
logging in no longer repairs missing recurring grants. This task does not run
that procedure or inspect production credentials/data.

Rollback is a coordinated frontend/backend revert, with no schema rollback.
Keep the monthly job; the shared unique reference prevents double monthly grants
if the old lazy path is restored. Existing unrelated ledger locking limitations
remain a separate issue.

## Execution context and evidence

Implementation is uncommitted. Original checkout's unrelated frontend edits are
excluded; work is in the clean PRI-11 worktree on the branch above. Baseline
focused backend suite: 37 passed, 2 PostgreSQL-only skips. Regression red:
five backend tests failed for auth SQL access/missing explicit endpoint;
frontend setup-ordering/retry tests failed because children mounted immediately.
First focused green: 28 backend tests and 3 frontend boundary tests passed.
Final local verification passed on the implementation captured by snapshot
`f88f31cf5d2da738c1846dcd6a51c2a72b7ce18b57bb166d53335ba8bb367709`.
Only this evidence record was updated afterward; production/test content did not
change. Scope is 8 production files / 282 changed lines, including generated
OpenAPI and TypeScript artifacts. Feature implementation is uncommitted and not
released. PRI-20 remains In Progress for review/owner delivery and hosted gates.

### Verification results (2026-09-21)

Python alias `PYTHON=/tmp/pri19-audit.WWLmok/venv/bin/python` resolves to 3.11;
locked AnyIO 4.14.2, FastAPI 0.138.0, SQLAlchemy 2.0.51, PyJWT 2.13.0.
Final frontend commands used Node 22.23.2 on PATH, matching CI's major version.
The Makefile supplies dummy test credentials. PostgreSQL commands additionally
set `DATABASE_URL` and `SQLALCHEMY_DATABASE_URI` to the isolated local database
`postgresql://127.0.0.1:55432/pri20_test`; Supabase/OpenAI settings were dummy values.
No production credentials or external model calls were used.

| Command / procedure | Result | Limits |
| --- | --- | --- |
| `make verify-backend-ci PYTHON=...` | Passed: lint, 625 tests, 88.47% coverage, dependency audit | 15 explicit skips: 10 dormant Stripe, 4 PostgreSQL tests run separately below, 1 pre-existing hardcoded SQLite lock skip. Golden real-provider suite excluded by native target. |
| `make verify-frontend-ci PYTHON=...` with Node22 | Passed: contracts/tooling, lint, types, production build, 253 unit tests, 8 MVP Chromium smoke tests, production dependency audit | Existing MVP signed cases use nonproduction bypass; separate browser check below covers actual gate. |
| `python -m alembic upgrade head` on clean PostgreSQL14 sandbox | Passed all migrations | Migration execution does not prove ORM/schema alignment (see known defect below); CI uses PostgreSQL15. |
| `python -m pytest tests/services/credits/ -k concurrent -q -o addopts=''` with sandbox DB | 4 passed, 1 pre-existing hardcoded skip | Real separate sessions, isolated schemas, actual monthly function. |
| Two new PostgreSQL race scenarios, 10 repeated pytest runs | 20 passed | Stress repetition justified by the observed unique-email race; no throughput claim. |
| `PRISM_PRO_PUBLIC_PREVIEW_ONLY=true ... npx playwright test tests/e2e/landing-page.spec.ts --project=chromium` | 8 passed on Node22 | Public-preview mode only. |
| Browser sandbox, `/tmp/pri20-review-browser-check.cjs` | Passed actual signed/restored-session gate, 503 retry, real POST204, feature requests after setup, reload and exactly one 90-credit grant | Local fixture JWKS provider + real Next/FastAPI/PostgreSQL; no Supabase production or OAuth exchange. Dev webpack used because Turbopack rejects the scratch dependency symlink. Profile endpoint's pre-existing schema failure remains visible. |
| Fresh-context independent reviewer | No material implementation findings; 47 backend contract, 23 consumer, 3 PostgreSQL race, 5 frontend lifecycle tests passed independently | Same configured model family; exact identifier unavailable, no cross-model claim. 754 hashes matched before/after; isolated source copy, no code edits. Independent robust browser follow-up passed; initial browser coverage gap L1 is closed. |
| `git diff --check` and snapshot provenance check | Passed | Snapshot includes untracked changes; original unrelated worktree remains excluded. |
| Docker image builds | Blocked | Docker daemon unavailable. |
| Hosted CI / TruffleHog verified secret scan | Not run for this uncommitted change | No commit/push authority; local TruffleHog unavailable. Prior branch's CI is not evidence for this change. |
| Production cron health, amount, backfill, deployed auth provider | Not run | Release prerequisites require authorized environment verification. |

The first scratch browser script injected failure into only one request: it
passed once but failed on independent rerun because React development Strict
Mode can start another setup request. The reviewer corrected the verification
harness (no application change) to hold/fail **all** requests before manual retry
and inspect request starts, not just responses. That robust independent check
passed, as did an independent database query for one ledger entry totaling 90.
The immutable first review and follow-up are
`/tmp/pri20-independent-review.md` and
`/tmp/pri20-independent-review-followup.md`; exact source IDs come from their
JSON manifests. This is fresh-context review, not separate-model certification.

Logs and immutable review packet/report are in `/tmp/pri20-*` on the development
machine. Durable outcome/commands/limitations are retained here and in PRI-20;
temporary artifacts are supporting evidence, not required project dependencies.

### Separate pre-existing defect found during sandbox verification

A database migrated from empty to the current head has only `id` and `user_id`
in `public.user_profiles`, while the existing ORM/GET profile endpoint selects
`full_name` and other absent columns. The browser reaches the dashboard and
credits successfully, but profile fetch returns 500 (`UndefinedColumn`). This
was independently reproduced by executing the unchanged base revision's actual
GET endpoint against that freshly migrated sandbox. All migrations, the profile
model and endpoint are unchanged from the base.

This is not introduced by PRI-20 and is outside its no-schema-change scope.
Do not call the whole dashboard or fresh-database deployment healthy based on
bootstrap checks. Reconcile the legacy profile schema in a separately scoped
change before accepting fresh-database profile functionality. No migration or
schema workaround was applied here. Baseline evidence:
`/tmp/pri20-baseline-profile.log` (base endpoint 500; columns `id`, `user_id`).


### Evidence-backed correction and references

Real PostgreSQL testing reproduced a same-user concurrent insert failing on
`users_email_key` despite `ON CONFLICT (user_id) DO NOTHING`. The correction
omits the conflict target and independently checks for the authenticated user ID
after a skipped insert. The different-identity/email-collision test prevents
turning arbitrary unique conflicts into success. This lesson applies to inserts
with multiple unique constraints; it is not a general license to ignore errors.

Primary references checked 2026-09-21: [PostgreSQL INSERT](https://www.postgresql.org/docs/15/sql-insert.html)
(all usable unique constraints participate without a conflict target),
[transaction isolation](https://www.postgresql.org/docs/15/transaction-iso.html)
(a later Read Committed statement sees the concurrent committed row), and the
installed PyJWT 2.13.0 exception hierarchy (`PyJWKClientConnectionError` derives
from `PyJWTError`, so catch connection failures before invalid-token failures).
[PyJWT API reference](https://pyjwt.readthedocs.io/en/latest/api.html) corroborates
the named exception; installed source is the version-specific authority.
