# PRI-20 final verification — 2026-09-21

## A. Verdict

**Verification blocked for full release acceptance.** No material defect was
found in the PRI-20 implementation. All four issue criteria are met within
the verified local scope, but required image/hosted checks and production
monthly-job verification are not established. Passing local checks does not
make those gates passed.

Risk: **Critical** (authentication, account persistence and credit entitlement).
Reviewed branch: `security/pri-20-explicit-account-bootstrap`; uncommitted change
against main/HEAD/merge base `a70cdfc3011513e05e24d60b79f3c599963ea80c`.
The complete source, including untracked implementation and tests, matches
snapshot `8dc237a91f559646de59c07e311ae197a21850f8564b3d6a4615c9d983322a1a`.
This audit report and its feature-record link were added after verification;
no implementation, test, dependency or generated-contract file changed.
Original checkout's unrelated work remains excluded and untouched.

Scope: 8 production files / 282 changed lines, including generated artifacts.
Requirements were reread through `linear_prismpro` in the verified PrismPro
project; [PRI-20](https://linear.app/prismpro/issue/PRI-20/separate-user-bootstrap-and-monthly-credits-from-authentication)
remains In Progress. No commit, push, merge, deployment or production mutation.

## B. Prioritized findings

No required implementation corrections were identified within PRI-20.

**PRI20-R2-PRE1 — Medium, high confidence, pre-existing; unresolved outside scope.**
At `backend/migrations/versions/0001_initial_core_schema.py:90`, the legacy
`user_profiles` table is created with only `id` and `user_id`. The model at
`backend/app/models/job.py:52` expects `full_name` and additional columns, and
`backend/app/repositories/profile_repository.py:16` selects that full model.
On a freshly migrated PostgreSQL database, the profile endpoint consequently
returns 500. This affects fresh-database profile functionality, not the new
bootstrap transaction or identity boundary.

Evidence: actual base endpoint reproduction, database column inspection,
unchanged model/repository/endpoint/migrations, and the current browser's
profile failure. Prior independent review reproduced it; this final reviewer
corroborated the source/baseline evidence without recreating that empty-database
experiment. The final audit browser still reaches setup, credits and dashboard
while the separate profile fetch fails. Do not describe the whole dashboard as
healthy on a fresh database.

Smallest reasonable correction: separately reconcile the supported profile
schema/model through an approved migration or approved retirement of the legacy
path. Verify a clean migration and authenticated profile GET against real
PostgreSQL, including existing-data compatibility. No schema workaround was
applied; this is not an introduced PRI-20 regression.

Optional future improvement: retain the no-bypass browser procedure as a
maintained CI regression. Its successful manual/sandbox execution establishes
current evidence; existing bypass-based browser tests alone will not protect
that complete boundary in future changes. This is not a current code defect.

## C. Acceptance mapping

| Criterion | Status | Evidence | Gap |
| --- | --- | --- | --- |
| Ordinary authentication makes no user/credit writes | Met locally | All three identity dependencies execute zero SQL through FastAPI; no application DB dependency remains in auth. | Deployed clients not exercised. |
| First-user bootstrap is concurrency-idempotent | Met locally | PostgreSQL sessions race first contacts; one account and one allowance. Grant/commit failure rolls back both; retry succeeds. | Local PostgreSQL14, hosted gate uses15. |
| Monthly credits are not duplicated per period | Met locally | Actual recurring SQL and bootstrap share unique UTC period reference; concurrent/repeated jobs and email collisions tested. | Production job scheduling/health/amount unverified. |
| Provider and DB failures are stable and distinguishable | Met locally | Signed-token rejection, required-auth provider503, setup503, conflict409, and safe response tests pass. | Real deployed provider outage not induced. |
| Deliberate session boundary is reachable and recoverable | Met locally | Actual browser with signed restored session, no bypass: pending/failed setup blocks feature traffic; manual retry204 and reload preserve90credits. Lifecycle tests cover logout/account switch/timeout/token refresh. | Local synthetic provider and dev webpack; no live OAuth. |

Expectations come from the contract rather than production helper return values.
Tests assert forbidden effects, atomicity, identity ownership and persistence.
The old test expecting authentication writes was changed deliberately to the
new contract. Its weak mocked race check was replaced with real PostgreSQL
concurrency. No tests were skipped or weakened to obtain the audit result.

## D. Design assessment

Authentication owns token validation; the application service owns the account
and initial-credit transaction; the endpoint maps transport errors. This fits
the existing delivery/application/service direction. The ledger helper remains
the canonical allowance writer; bootstrap does not duplicate balance arithmetic
or commit before the grant. A skipped insert is checked against the verified
identity, so another user's email collision cannot masquerade as success.

The dashboard gate mounts before DashboardProvider. Identity-keyed lifetime,
effect cleanup and a 15-second abort bound stale results and loading; routine
token refresh preserves mounted state. Its direct fixed-token request is
intentional: the ordinary API helper replaces supplied Authorization with the
latest global session, which could bind an in-flight setup to another identity.
No new general framework or redundant credit policy was introduced.

Security/privacy, transaction integrity, concurrency, recovery, API compatibility,
and diff hygiene were inspected. Status/alert semantics and a native retry button
cover the changed loading/error UI; no comprehensive assistive-technology audit
is claimed. Auth no longer issues SQL; no measured latency or throughput claim
is made. No new unbounded loop, process or cache is introduced. Diagnostics at
the new setup boundary avoid raw SQL or personal data in responses/log messages.

No changes touch migrations, billing, RLS, uploads, model generation or new
providers, so those subsystems were not broadly re-audited. Existing general
ledger-lock behavior remains PRI-22; optional-auth outage policy remains PRI-21.
Those exclusions do not imply those areas are defect-free.

## E. Verification results

Freshly executed for this final audit unless marked otherwise. Python is 3.11
at `/tmp/pri19-audit.WWLmok/venv/bin/python`; Node is 22.23.2. The native Makefile
provides dummy settings. PostgreSQL tests explicitly set both database variables
to `postgresql://127.0.0.1:55432/pri20_test`, an isolated task-owned database.
No production credentials or external model calls were used.

| Command/procedure | Evidence class | Result and limits |
| --- | --- | --- |
| `make verify-backend-ci PYTHON=/tmp/pri19-audit.WWLmok/venv/bin/python` | Executed by coordinator | Passed lint, 625 tests, 88.47% coverage and dependency audit. 15 explicit skips: 10 dormant Stripe tests, 4 PG-only tests run separately, 1 pre-existing hardcoded SQLite lock skip. Golden real-provider suite excluded by native target. |
| `make verify-frontend-ci PYTHON=/tmp/pri19-audit.WWLmok/venv/bin/python`, Node 22 on PATH | Executed by coordinator | Passed contract checks, lint, types, build, 253 unit tests, 8 MVP browser tests and production dependency audit. |
| `python -m pytest tests/services/credits/ -k concurrent -q -o addopts=''` with sandbox DB | Executed by coordinator | 4 passed, 1 pre-existing hardcoded skip; separate sessions and real recurring function SQL. |
| `PRISM_PRO_PUBLIC_PREVIEW_ONLY=true ... npx playwright test tests/e2e/landing-page.spec.ts --project=chromium` | Executed by coordinator | 8 passed; dummy provider/API settings, Node 22. |
| Robust signed-session browser harness | Executed by coordinator and independently by reviewer | Passed: no bypass, all pre-retry requests held/failed, no early feature traffic, manual retry to real 204, credits 200, reload, 90 credits. 710 running source files matched manifest. |
| Focused auth/bootstrap/export tests | Executed independently in isolated copy | 47 passed. |
| Route security/credits/preview tests | Executed independently in isolated copy | 20 passed. |
| Three bootstrap PostgreSQL race tests | Executed independently in isolated copy | 3 passed, no skips. |
| Five frontend setup/lifecycle tests | Executed independently in isolated copy | 5 passed on Node 22. |
| Full-source hash/provenance and `git diff --check` | Executed by both | 754 files matched before/after review; no unrelated changes. |
| Clean `alembic upgrade head` and base profile reproduction | Prior executed evidence corroborated | Migration execution passed on unchanged source; profile GET failed as documented. Not misrepresented as fresh reruns. |
| Backend/frontend Docker builds | Blocked | Docker Desktop exists; starting it and bounded readiness retries still produced server timeouts. No successful image build claimed. |
| Hosted CI / verified TruffleHog scan | Not run | Work is uncommitted; no push authority, local scanner unavailable. |
| Production monthly job/provider checks | Not run | No authorized production access used. |

Fresh reviewer: Codex subagent `pri20_final_audit`, separate fresh context,
same configured model family; exact model identifier unavailable. No cross-model
claim or recursive delegation. Third review round for this implementation;
no material PRI-20 finding. Immutable report:
`/tmp/pri20-final-audit-independent.md`. Native logs:
`/tmp/pri20-final-audit-backend.log`, `...-frontend.log`, `...-postgres.log`,
`...-landing.log`. Earlier red/green evidence remains in the feature record.

Browser log limitation: parent/reviewer accidentally used the same log path
during independent runs. It is not a uniquely attributable reviewer artifact.
The reviewer separately observed process exit 0, kept its own script/screenshot,
and checked the 710 running source hashes. This supports repeated session setup;
the isolated PostgreSQL race tests establish concurrent first-contact behavior.

## F. Remaining decisions and minimum acceptance actions

1. Complete required image builds and hosted checks, including verified secret
   scanning and PostgreSQL 15, on the actual submitted revision. Commit/push
   still require owner approval; this audit grants none.
2. Before rollout, verify the production monthly job's installation, schedule,
   health and approved allowance; perform only authorized idempotent backfill
   if existing accounts lack the intended current grant.
3. Coordinate frontend/backend delivery and independently deployed clients.
   Older clients need explicit bootstrap; a new frontend cannot initialize
   against an old backend. No PRI-20 schema migration is needed. Rollback is a
   paired frontend/backend revert while retaining the job and period uniqueness.
4. Separately resolve PRI20-R2-PRE1 before accepting profile functionality on
   a fresh database. The current production schema was not inspected, so no
   claim is made about whether that environment has the same mismatch.

Implementation is locally verified within scope; full release acceptance remains
pending. No finding required an implementation edit during this audit.
