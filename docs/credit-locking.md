# PRI-22 — Fail-closed credit locking

## Post-merge CI repair — 2026-10-01

### Current execution context and contract

The historical PRI-22 implementation and audit below are retained. This follow-up
repairs only the lock-observation test on `fix/postgres-credit-lock-test-polling`,
based on merged `main` revision `b83d9d41e7ee6122562e67437f6fbc99d5cdce9f`.
The owner authorized the repair branch while post-merge CI is red. The previous
local PRI-27 branch was removed after verifying its tree matched merged `main`.
The owner authorized commit and push on 2026-10-01 after local verification and
review. PR creation is manual; merge and production operations are not authorized.

Problem: [post-merge CI run 36819595257](https://github.com/NagarjunMa/LinkedinAutomation/actions/runs/36819595257)
failed the `grant` case of `test_each_credit_operation_waits_for_its_user_only`.
The observer polls `pg_stat_activity` within one transaction. If its first
snapshot precedes the worker connection, later polls can miss the blocked worker.
A disposable PostgreSQL 14 probe first reproduced that observation failure.
On PostgreSQL 15.19, forcing the observer sample before worker connection caused
all three operation cases to fail the existing blocking assertion. Refreshing the
activity snapshot before every poll made those cases pass.

Risk: **Significant** because this changes concurrency verification used as a CI
gate. This is test-only; no production billing, transaction, API, migration, RLS,
pricing, or authentication behavior is in scope. Full documentation is retained
in the existing feature record, with local acceptance criteria because the required
`linear_prismpro` connection is unavailable. The generic Linear plugin is excluded
by the owner's routing instruction; no issue was read or updated for this repair.
The catalog provides `production-engineering-loop`, used here, rather than the
repository's requested `engineering-loop` alias.

### Acceptance and planned evaluations

| ID | Required outcome | Evidence / plausible defect rejected |
| --- | --- | --- |
| R1 | The observer detects a worker that connects after its first activity sample | Force that ordering in all three existing debit/grant/refund cases; observe a failure before the polling fix, then a pass on PostgreSQL 15. Removing snapshot refresh must fail the same assertion. |
| R2 | The tested row lock remains real, user-specific, and precedes balance calculation | Preserve `blocked`, unfinished-worker, independent Bob debit, and final-balance assertions. Record worker statements and forbid SUM/INSERT while the holder owns the user lock. An isolated mutation removing the ledger lock must fail that pre-balance assertion. Retain the existing overspend, timeout, rollback and unsupported-mode cases. |
| R3 | The repair preserves repository gates and source boundaries | Native backend lint/coverage/audit, CI-selected real PostgreSQL suite, test lint, diff review and fresh independent review. No lowered thresholds, skips, changed production files, or dependencies. |

Design: keep database observation in the existing test. The production ledger
remains the owner of locking and balance rules; the application retains transaction
ownership. Create an activity sample before launching the worker to exercise the
previously uncontrolled interleaving. After establishing the failing regression,
call `pg_stat_clear_snapshot()` before each observation. An observer-only autocommit
transaction would also refresh activity between queries, but the explicit refresh
retains the existing transaction configuration and states the reason directly.
Keep existing deadlines, lock timeouts, future cleanup and schema cleanup.
Use explicit synthetic settings and
an isolated local PostgreSQL 15 container; never load a production connection for
these tests.

Planned commands: `make verify-backend-ci PYTHON=/tmp/pri27-push-venv/bin/python`;
`python -m pytest tests/services/credits/ -v -k concurrent` with the isolated
PostgreSQL URL; focused regression and isolated mutation checks with
`-o addopts=''`; Ruff on the changed test; `git diff --check`.
Implemented and verified locally; fresh independent review found no material
findings. Commit and push are authorized; hosted CI on the manually created PR
remains pending.
PRI-28 remains deferred until the repair is merged and `main` CI is green.

Compatibility and recovery: test-only, no application rollout, migration or data
backfill. Reverting the repair restores the intermittent observation failure;
the production lock implementation is unchanged. No frontend/accessibility/model
behavior or production performance/cost claim is involved. Test polling remains
bounded, and evidence must distinguish local container checks from hosted gates.

Primary source accessed 2026-10-01:
[PostgreSQL 15 statistics snapshots](https://www.postgresql.org/docs/15/monitoring-stats.html#MONITORING-STATS-VIEWS).
PostgreSQL documents transaction-scoped activity snapshots and the explicit
`pg_stat_clear_snapshot()` refresh operation.

### Evidence and findings resolution

- **Red:** forced-order cases failed for debit, grant and refund on PostgreSQL
  15.19 at the intended blocking assertion (three failures, no setup failures);
  `/tmp/pri27-lock-repair-red.log`, with pre-fix diff retained at
  `/tmp/pri27-lock-repair-red.diff`.
- **Green:** after refresh and the additional pre-balance assertion, the exact
  CI-selected credit command passed: 15 passed, one existing hard-coded legacy
  skip, 32 deselected; `/tmp/pri27-lock-repair-postgres-final2.log`. No new skip or
  lowered threshold. The earlier full PostgreSQL attempt lacked migrated public
  tables; that environment setup failure is not behavioral red evidence. Applying
  `python -m alembic upgrade head` in the sandbox passed and supplied the same
  prerequisite as CI; `/tmp/pri27-lock-repair-migration.log`.
- **Confirmed evaluation gap:** the first missing-lock mutation passed because
  the ledger insert's foreign-key wait also satisfies a generic wait assertion.
  The test now records only worker statements and rejects a balance read or insert
  before the held user lock is released. This strengthens the existing production
  invariant without modifying the ledger. The neighboring lock-timeout test uses
  the same statement-recording pattern. Evidence:
  `/tmp/pri27-lock-repair-no-lock.log` (old wait-only assertion accepted the
  defect), `/tmp/pri27-lock-repair-no-lock-final.log` (all three cases now reject
  it at the pre-balance assertion). Removing snapshot refresh is also rejected in
  all three cases; `/tmp/pri27-lock-repair-no-refresh-final.log`. All mutations
  occurred in a disposable copy and were restored there.
- Final-state native backend gate: 703 passed,
  26 skipped, 89% displayed combined coverage (80% required), Ruff and locked
  dependency audit passed; `/tmp/pri27-lock-repair-backend-final.log`.
  Changed-test Ruff and `git diff --check` also passed. The changed PG tests are
  verified on the actual database rather than counting their SQLite skips as
  passes. Live golden model tests remain excluded by the unchanged native target.

The sandbox uses synthetic identities, loopback-only PostgreSQL, no host data
volume and image digest
`sha256:724292da1f2e50bdccfc3302ce75bbba7f4a6076701b588cc795fcac65683550`.
Its database is disposable. Local PostgreSQL 15 evidence is not a hosted CI pass.
The container and its database were removed after verification and review.
The foreground Docker client stalled on its credential helper; a temporary empty
client config downloaded the public image without reading real registry credentials
or changing the user's Docker configuration.

Scoped lesson: an activity observer needs a fresh snapshot when new sessions may
appear; observing a wait alone does not establish that locking precedes balance
calculation. Keep both the forced-order regression and forbidden-statement check.
Additional source accessed 2026-10-01:
[PostgreSQL 15 row lock conflicts](https://www.postgresql.org/docs/15/explicit-locking.html#LOCKING-ROWS).

### Final local review and remaining gates

Fresh-context reviewer `/root/credit_lock_polling_review` inspected the complete
two-file diff, source/callers, contract and repository guidance in an isolated copy.
Exact model identities were unavailable; no cross-model review is claimed.
Reviewed snapshot ID:
`0874d2cb4fba2bd36b6859306a689c2048211a2802bad9da94909469dce29f46`.
All 774 captured paths plus three supplemental architecture/sequence files retained
their hashes and modes through review. The original-source provenance check passed.
Report: `/tmp/pri27-lock-repair-independent-review.md`.

The reviewer freshly ran 14 schema-contained PostgreSQL tests with one existing
skip, repeated both three-case mutation checks, verified the cached-activity
behavior directly, checked schema cleanup, and passed test lint and diff hygiene.
The unchanged public-schema legacy case was checked through the coordinator's full
15-pass suite log, rather than repeated under the reviewer's schema-only boundary.
The native backend final log was inspected, not independently rerun. Verdict:
**no material findings**. R1, R2 and applicable local R3 evidence are met.

Only this record's evidence/status text changed after review. The executable test
retains reviewed SHA-256
`6d1080a6534a0bf4c955ce0f322c3c6626de5975e7175bde580c88d7fd06b374`.
No production file, dependency, threshold, CI setting or migration changed. Backend
Docker context excludes tests; frontend/API/UI, authentication/RLS, model behavior
and production performance are unaffected, so their native suites/image rebuilds
were not repeated for this test-only repair. Existing deadlines can still fail
under extreme host scheduling delays; no universal absence of flakiness is claimed.

Remaining: authorized commit/push, manual repair PR; normal hosted CI including
backend Docker/migrations/PostgreSQL/audit and verified secret scan; owner review
and merge; green post-merge `main` CI. Linear evidence synchronization is blocked
by unavailable `linear_prismpro` access. No issue is marked complete, and neither
the repair's merge nor PRI-28 implementation has occurred.

## Execution context

Source: [PRI-22](https://linear.app/prismpro/issue/PRI-22/fail-closed-when-postgresql-credit-row-locking-fails), re-read 2026-09-22. Base/main: `f20e4881f040feca588ef17cc578fac64eb71a5b` (PRI-21 PR58 and post-merge CI passed). Branch: `security/pri-22-fail-closed-credit-locking`. Original checkout's unrelated frontend edits are excluded.

Status: final local pre-merge audit passed with no material findings; see [current audit evidence](credit-locking-audit.md). Required hosted gates and owner-authorized delivery remain pending. Full documentation, Critical risk: paid-operation balances and database concurrency. No commit, push or deployment authorized.

| Location | Verified responsibility / intended change |
| --- | --- |
| `backend/app/services/credits/ledger.py` | Authoritative SUM(delta), shared append/lock, debit/refund validation |
| `backend/app/application/credits.py` | Paid-operation transaction and failure rollback |
| `backend/app/application/bootstrap.py` | Validate supported credit transaction before account insert; roll back unavailable-credit errors |
| `backend/app/middleware/credits.py`, `backend/app/api/error_mapping.py` | HTTP compatibility adapter updated for safe503; canonical application error mapping unchanged |
| `backend/tests/services/credits/test_locking.py`, `test_locking_concurrent.py` | New negative/optimized-Python and actual PostgreSQL coverage; existing ledger/bootstrap tests retained |
| `backend/tests/application/test_credits.py` | Paid-work forbidden effects, rollback and safe errors |
| `.github/workflows/ci.yml`, `Makefile` | Native backend checks and PostgreSQL `-k concurrent` selection |

Read architecture.md, repository guidance and approved sequence/architecture/grounding documents in the original checkout. No nested backend AGENTS.md exists. production-engineering-loop v0.5.0 used; catalog has no `engineering-loop` alias. Supabase/PostgreSQL guidance also consulted.

## Problem and goal

The shared append path catches every row-lock exception and continues. Debit/refund validation uses assertions, which disappear under optimized Python. The paid-operation boundary only rolls back insufficient-balance errors during debit. Require safe locking and amount validation before any credit append or paid work, while keeping transaction ownership with callers.

## Change contract

- PostgreSQL: require the existing matching user row and its lock before reading the balance. Propagate acquisition errors; no fallback query or append.
- SQLite: explicit development/test-only path, requiring the user to exist. No claim that SQLite supplies equivalent concurrent serialization.
- PostgreSQL ledger writes require transactional READ COMMITTED. A real baseline probe with REPEATABLE READ produced balance -1 after two debits of3 against5, despite taking the row lock: locking an unchanged users row does not refresh a ledger snapshot. Reject unsupported isolation/autocommit before writing.
- Debit/refund amounts are positive integers (exclude booleans), with stable ValueError even under `python -O`.
- Keep caller-owned commit/rollback. Failed debit must roll back and never yield to paid work or trigger a refund; SQLAlchemy/locking-configuration failures use the existing safe external-service failure. Bootstrap validates the same transaction condition before inserting an account, preventing partial creation under autocommit.
- Preserve public success payloads, insufficiency402, failed-refund reconciliation, grant external references, bootstrap and ownership. No new automatic retries.

Non-goals: changing prices/grant policy, scheduled SQL grant implementation, Stripe activation, database schema/RLS, general billing redesign, frontend or production configuration. The scheduled SQL grant is an unchanged separate writer; Python locking does not certify its historical `balance_after` metadata. SUM(delta) remains authoritative.

## Design and security

The ledger owns supported write conditions and balance arithmetic. The application owns transactions and transport-neutral errors; delivery retains existing HTTP mapping. Reuse the existing users row and shared append function, not a new lock service or balance store. Keep provider/model work outside the debit transaction. No credentials, customer records or raw user data in new logs/tests. Missing users and incompatible database modes must fail before append.

## Acceptance and planned evaluations

| Criterion | Expected behavior / test | Plausible defect detected |
| --- | --- | --- |
| A1: PostgreSQL lock errors abort transaction | Real held lock/lock timeout; original55P03 propagates, caller rolls back, no event/paid work, session recovers | Swallow original failure then query an aborted transaction; execute work despite debit failure |
| A2: same-user debits never negative | Separate concurrent sessions against5; only one debit3 succeeds. Hold user lock to demonstrate debit/refund/grant block; other user proceeds | Missing/wrong-user lock; stale snapshot; holding a global lock |
| A3: explicit local SQLite | Development/test successes; production/unsupported dialect and missing user denied | Silent fallback for any dialect or no matching row |
| A4: invalid amounts under optimization | Zero/negative/bool/fraction/string/null rejected before DB access in ordinary and real `python -O` process | Assertion-only validation; coercing invalid deltas |
| Compatibility | Existing credits, bootstrap/job concurrency, application/middleware, route/admin tests | Changed grant/idempotency, refund or transport behavior |

## Implementation and verification plan

Behavioral TDD: baseline, failing negative/transaction tests, smallest implementation, actual PostgreSQL tests and correction, native gates, fresh-context independent review (maximum three rounds). No artificial red phase for unchanged characterization checks; documentation uses diff inspection.

Native: `make verify-backend-ci PYTHON=/tmp/pri19-audit.WWLmok/venv/bin/python`; `make verify-contracts` with Python3.11/Node22. Focused pytest uses explicit dummy provider settings and SQLite. PostgreSQL tests receive only the disposable local connection URL, use separate sessions and unique schemas, and clean up their schemas/connections. The PostgreSQL filename includes `concurrent` so existing CI selection includes all cases.

PostgreSQL14 is installed locally; CI uses15. Hosted15, Docker and verified secret scanning remain delivery gates. A read-only Docker daemon probe did not respond; no Docker configuration changed. No live Supabase or production checks. Frontend/accessibility unchanged; no new UI-specific checks required locally.

## Compatibility, rollout and rollback

Backend-only, no schema migration/backfill. Supported PostgreSQL configuration requires READ COMMITTED and ordinary transactional sessions; deployed settings remain unverified and unsupported bindings fail closed. Runtime failures preserve safe503 handling and existing402/credit-reconciliation semantics. Do not automatically retry ambiguous commit outcomes. Deployment requires normal approval and hosted gates. Observe existing safe error/credit reconciliation diagnostics. Rollback restores unsafe fallback/assertion behavior; prefer a scoped forward correction.

## Evidence and progress

- Baseline predecessor source (tree equals merged base): focused credits/application/middleware21 passed, five existing skips; `/tmp/pri22-baseline.log`.
- Actual PostgreSQL bootstrap/job baseline: three passed; `/tmp/pri22-postgres-baseline.log`.
- Actual PostgreSQL stale-snapshot probe:5 -> concurrent debit3 -> stale debit3 -> SUM(delta)=-1; `/tmp/pri22-isolation-probe.py`. Establishes the isolation guard's relevance.
- Unit/transaction regression red:21 failed/5 passed; `/tmp/pri22-red.log`. These were behavior failures, not import/setup failures. After the first correction:33 passed including existing middleware cases.
- Actual PostgreSQL regression red:5 failed/4 passed; `/tmp/pri22-postgres-red.log`. Original lock timeout was swallowed, paid failure missed the safe boundary, and unsupported isolation/autocommit allowed writes. After correction, nine new PG cases and three existing bootstrap/job cases passed.
- HTTP compatibility adapter regression: one expected failure before mapping safe503, then included in focused green.
- Focused compatibility green:67 passed/14 skips; `/tmp/pri22-focused-green.log` (before the two added bootstrap-mode cases).
- Bootstrap mode regressions: REPEATABLE READ first failed safe-error/rollback, then passed after catching the shared error. AUTOCOMMIT exposed a persisted account without its allowance (one failure/one pass); now the shared precondition runs before insertion. Evidence `/tmp/pri22-bootstrap-red.log`, `/tmp/pri22-bootstrap-autocommit-red.log`.
- Local PostgreSQL14 clean Alembic upgrade and CI-selected credit suite passed (intermediate14 passed/one existing skip). Final rerun includes both bootstrap-mode cases; `/tmp/pri22-postgres-final.log`.
- Final native backend gate:687 passed,26 skipped,88.61% coverage; Ruff and dependency audit passed. `/tmp/pri22-backend-final.log`.
- Final contract gate:four tooling tests, tooling lint and artifact freshness passed; `/tmp/pri22-contracts.log`.
- Final PostgreSQL CI selection:15 passed,one existing hardcoded skip,32 deselected; `/tmp/pri22-postgres-final.log`. All11 new PostgreSQL cases executed and passed. Local runtime PostgreSQL14.22, Python3.11.1, SQLAlchemy2.0.51, psycopg2 2.9.12.

## Initial implementation verification — 2026-09-22

Base/main/HEAD/merge base: `f20e4881f040feca588ef17cc578fac64eb71a5b`; full uncommitted diff on the branch above. Nine changed/new files, four production files and96 changed production lines. No unrelated edits, migrations, dependencies or test thresholds changed. The26 SQLite-suite skips are15 existing skips plus11 new PostgreSQL-only cases verified separately on the real database. Golden live-model tests are excluded by the native target; neither exclusions nor skips are passes.

Reviewed source snapshot `b1ad238ad3f45627deeda41641bcd34df2b9cf2fe0ffce842c54c00266de9340` covers761 files. Reviewer `/root/pri22_independent_review` used fresh context and an isolated copy with before/after hashes and modes verified. Exact model identities unavailable; no cross-model claim. Round1 of maximum3, **no material findings**. Immutable report `/tmp/pri22-independent-review.md`. Only this feature record's evidence/status changes after review; implementation/tests/configuration stay unchanged.

| Acceptance | Implementation and final evidence | Result |
| --- | --- | --- |
| A1 | Original PG55P03 preserved; paid/HTTP boundaries rollback and deny; real failure probes for resume evaluation, JD analysis, stored export and tailored download prove no provider work/refund/debit event | Met locally |
| A2 | Matching users-row lock and transactional READ COMMITTED; six-way race and three blocking operation cases; other-user independence; SQL-level isolation probe | Met locally |
| A3 | Shared dialect/environment guard; no missing-user append; bootstrap precondition before insert; SQLite local successes and production/unsupported negatives | Met locally |
| A4 | Explicit positive-integer validation; ordinary cases and real Python-O child | Met locally |

Independent commands (isolated backend, explicit dummy environment as above):

- `python -m pytest tests/services/credits/ tests/application/test_credits.py tests/middleware/test_credits.py tests/integration/test_explicit_bootstrap.py tests/integration/test_new_user_bootstrap.py tests/api/v1/test_credits.py tests/services/payments/ -q -o addopts=''`:73 passed,23 skips; `/tmp/pri22-independent-sqlite.log`.
- `python -m pytest tests/services/credits/ -k concurrent -q -o addopts=''` with disposable PostgreSQL URL:15 passed,one existing skip; `/tmp/pri22-independent-postgres.log`.
- `python /tmp/pri22-independent-probes.py`:eight adversarial checks passed, including four real paid consumers, lock release before work, caller rollback, SQL-level isolation and missing PG users; `/tmp/pri22-independent-probes.log`.
- Ruff, whole-source freshness and diff hygiene passed. Reviewer initially named a nonexistent bootstrap test file (collection error); corrected command passed. That attempt is not counted as behavioral red evidence.

Design review confirmed one shared transaction precondition, one balance rule and caller-owned transactions; no additional locking abstraction is needed. Credit locks end before external work. Safe errors retain non-retryable delivery envelopes; uncertain commit outcomes are not automatically replayed. No new UI, accessibility, schema, RLS, model, privacy-sensitive logging or memory-growth behavior. Dormant Stripe and scheduled SQL grants were inspected as unchanged consumers, not certified for activation or complete historical metadata consistency.

Hosted PostgreSQL15, Docker, verified secret scanning and deployment evidence remain pending. Native PostgreSQL14 does not replace the hosted15 gate. No production operation occurred. Before delivery: owner-authorized commit/push, required hosted checks and final review/merge. Before deployment: verify supported transaction configuration in the approved environment. No schema migration or backfill; prefer a forward correction over restoring unsafe fallback behavior.

## Decisions, sources and limits

Isolation guard is an evidence-driven refinement within the approved locking boundary. Do not silently change the session's isolation mid-transaction. `validate_credit_transaction` owns this precondition once; the ledger and bootstrap reuse it. The supported psycopg2 driver's autocommit flag is checked because SQLAlchemy's isolation-level getter alone reports READ COMMITTED in autocommit mode. Existing scheduled SQL grant and broader payment policy remain out of scope.

Sources inspected 2026-09-22: [PostgreSQL15 row locks](https://www.postgresql.org/docs/15/explicit-locking.html), [SQLAlchemy2 session transactions](https://docs.sqlalchemy.org/en/20/orm/session_basics.html), installed SQLAlchemy2.0.51 PostgreSQL dialect. Supabase changelog index retrieved; no relevant locking/API change identified. Local execution, not documentation alone, establishes selected behavior.

Scoped lessons: a users-row lock cannot refresh a REPEATABLE READ ledger snapshot; validate transaction mode before any related bootstrap write, particularly under autocommit. Separate SQLite tests from actual row-lock evidence. The regression cases above preserve these observations. Next step: final pre-merge verification and authorized delivery. Keep PRI-22 In Progress through initial implementation and final verification/merge.
