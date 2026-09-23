# PRI-22 final pre-merge audit — 2026-09-22

## A. Verdict and scope

**Verification blocked for full release acceptance; local final audit passed.** No material finding remains in the reviewed code. Required hosted PostgreSQL15, Docker and secret-scanning evidence on the submitted revision is pending; this is not an unqualified release-readiness claim.

Risk: **Critical**, because the shared credit boundary protects paid work and concurrent balances. Re-read the current requirements through the verified PrismPro Linear connection: require the existing PostgreSQL user lock, propagate failures, prevent concurrent overspend, explicitly limit SQLite to development/test, and validate debit/refund amounts under optimized Python.

Branch `security/pri-22-fail-closed-credit-locking`; HEAD/main/merge base and remote main verified as `f20e4881f040feca588ef17cc578fac64eb71a5b`. Complete uncommitted change; no staged files. Four production files /96 changed production lines. Nine implementation/evidence files reviewed; this final audit adds a tenth documentation file. Original checkout's unrelated frontend edits are excluded and preserved.

Reviewed snapshot `833bea210aec5e566a45130f12103ada13306f007b38dce3f8bdd9a4731b37e5`,761 captured paths. No production/test correction was needed. Only the feature record and this audit record change after independent review to retain final evidence.

## B. Findings

**No material findings.** No required code correction or cosmetic recommendation is manufactured. Existing scheduled SQL grant metadata, dormant payment activation, ambiguous commit outcomes and broader logging policy remain outside this change and are not certified by this audit.

## C. Acceptance mapping

| Criterion | State | Evidence | Gap |
| --- | --- | --- | --- |
| PostgreSQL lock errors abort | Met locally | Original55P03 retained with no follow-up SUM/append; rollback/recovery; independent real25006 read-only error and post-flush commit-failure probes | Hosted PG15/deployed settings unverified |
| Concurrent debits cannot go negative | Met locally | Six sessions against5 allow one debit3 and final2; debit/grant/refund each block on their user; another user proceeds | Local PG14.22 is not hosted15 evidence |
| SQLite explicit/local-test only | Met locally | Local successes; production/unknown dialect and missing user denied; bootstrap validates modes before insertion | No production configuration access |
| Invalid amounts stable under Python-O | Met locally | Zero/negative/bool/fraction/string/null rejected before DB access; real optimized child process | None within supported runtime |

Compatibility checks retain allowance idempotency, bootstrap races,402/safe503, refund reconciliation and caller-owned transactions. Unsupported isolation/autocommit fail before writing; a SQL-level isolation probe checks actual transaction state rather than engine configuration alone.

## D. Design assessment and applicable concerns

`ledger.validate_credit_transaction` owns supported transaction conditions and is reused before bootstrap insertion. `_lock_user` requires the matching existing user; `_append` uses authoritative SUM(delta) and flushes without committing. `application.credits.paid_operation` owns transaction completion and transport-neutral errors. Existing HTTP adapters preserve safe response mapping. These extend established functions without a separate lock service, competing balance source or new framework.

Security/privacy: callers retain ownership checks; denied debits cannot start paid work; new error messages omit SQL/user payloads. Existing reconciliation logging is unchanged. Integrity/concurrency: actual lock waits, independent sessions, multiple-append rollback, grant references and bootstrap transactions were checked. Reliability: original errors propagate, failed debits roll back, failed refunds require reconciliation, and ambiguous commits are not replayed automatically. Locks end before provider/render work; no new timeout or latency guarantee is claimed.

Performance/memory/cost: one bounded isolation lookup per PostgreSQL append; no new growing collection, cache, retry loop or measured performance claim. Compatibility: synchronous psycopg2 and transactional READ COMMITTED remain required; deployed settings need separate verification. UI/accessibility, model grounding and schema/RLS changes are not applicable because those surfaces are unchanged. Operations: backend-only rollout, no migration/backfill; retain safe error/reconciliation diagnostics. Revert restores unsafe fallback/assertions; prefer a scoped forward correction.

## E. Fresh verification results

Coordinator runtime: Python3.11.1 (`/tmp/pri19-audit.WWLmok/venv/bin/python`), Node22.23.2, SQLAlchemy2.0.51, psycopg2 2.9.12 and isolated PostgreSQL14.22. Provider configuration was explicit dummy values. A new disposable local database was used for clean migration and CI-selected tests. No production/provider calls occurred.

| Command/procedure | Executed by | Result / evidence |
| --- | --- | --- |
| `make verify-backend-ci PYTHON=/tmp/pri19-audit.WWLmok/venv/bin/python` | Coordinator |687 passed,26 skipped,88.61% coverage; Ruff/dependency audit passed. `/tmp/pri22-audit-backend.log` |
| `make verify-contracts PYTHON=/tmp/pri19-audit.WWLmok/venv/bin/python` with Node22 PATH | Coordinator |Four tooling tests, lint and artifact freshness passed. `/tmp/pri22-audit-contracts.log` |
| `python -m alembic upgrade head` then `python -m pytest tests/services/credits/ -v -k concurrent -o addopts=''`, from backend with disposable PG URL | Coordinator |Clean migration passed;15 passed,one existing hardcoded skip,32 deselected. `/tmp/pri22-audit-postgres.log` |
| Focused credit/application/middleware/bootstrap/payment pytest selection | Independent reviewer |64 passed,23 skipped. Exact command in `/tmp/pri22-final-audit-review.md`; `/tmp/pri22-final-audit-sqlite.log` |
| PostgreSQL CI-selected suite | Independent reviewer |15 passed,one existing skip. `/tmp/pri22-final-audit-postgres.log` |
| `python /tmp/pri22-final-audit-probes.py` | Independent reviewer |Five probes passed: SQL-level isolation, read-only lock error, post-flush commit failure, refund timeout/recovery, multiple-debit rollback. `/tmp/pri22-final-audit-probes.log` |
| Ruff, `git diff --check`, manifest/copy integrity | Coordinator/reviewer |Passed; all761 source/copy hashes and modes current during review |
| Bounded Docker daemon probe | Coordinator |Timed out after5seconds; no Docker build claimed |
| Hosted CI/PG15/verified secret scan/deployment | Not run |Uncommitted change; requires authorized submission and release evidence |

The26 native-suite skips are15 existing skips plus11 new PostgreSQL-only cases; all11 new cases passed on real PostgreSQL separately. Golden live-model tests remain excluded by the native target, not counted as passes. No tests or thresholds were weakened. Historical implementation red/green evidence remains in [the feature record](credit-locking.md), separate from these fresh audit runs.

Initial local database restart omitted its custom port and failed because another process owned5432. Restarting the same disposable instance on its recorded dedicated loopback port succeeded; no existing server was altered. This was a setup error, not a behavioral failure. Shared installed dependencies and deployed environments are outside source-manifest guarantees.

Fresh reviewer `/root/pri22_final_audit`, round2 of maximum3, inherited no implementation conversation. Exact model identities unavailable; no cross-model claim. Immutable report `/tmp/pri22-final-audit-review.md`, SHA256 `1b2f459a27d003b538ce1075b963a44cdc2091d433a0598d693566e1df55002a`. Independent results were read separately from coordinator native-gate results.

Primary basis retained from2026-09-22: [PostgreSQL row locks](https://www.postgresql.org/docs/15/explicit-locking.html), [SQLAlchemy isolation API](https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Connection.get_isolation_level), and installed PostgreSQL dialect inspection. Actual probes substantiate selected behavior; public documentation does not establish deployed configuration.

## F. Remaining decisions and minimum acceptance actions

1. Owner-authorized commit/push and required hosted PG15, Docker and secret-scanning checks on that revision.
2. Required review/merge; keep PRI-22 In Progress until delivery conditions are met.
3. Separately authorized deployment and verification of transactional READ COMMITTED in the target environment.

No commit, push, merge or deployment performed by this audit. No unresolved local material finding remains; coverage is limited to this change and stated consumers/checks.
