# PRI-21 final audit — 2026-09-21

## A. Verdict and scope

**Verification blocked for full release acceptance.** The corrected implementation passes
applicable local gates and independent review, with no unresolved material PRI-21 finding.
Required hosted checks on the submitted revision remain pending; this is not a code-quality
failure or production-readiness claim. One material regression was found and corrected.

### Contract and snapshot

Apply [PRI-21](https://linear.app/prismpro/issue/PRI-21/make-optional-authentication-fail-closed-on-provider-outages): only absent credentials may enter optional anonymous access; reject invalid credentials; preserve provider503; maintain user/admin isolation. Re-read through verified PrismPro Linear connection. Existing abuse budgets and public-preview controls must also remain effective.

Risk **Critical**, authentication/identity attribution. Target/main/HEAD/merge base:
`21bc3d556c4cae5eef239b5a5e52133bc60d5c8f`. Branch
`security/pri-21-fail-closed-optional-auth`, complete uncommitted change (no staged files).
Initial audited snapshot `b623dbfb42f19d47057741c701e2ab603a6f564e6df163c20ecfbb90f2483670`.
Original checkout's unrelated frontend work is excluded and preserved. Corrected-state native gates and the final independent review passed.
Corrected reviewed snapshot: `22bb0284ce36e03395b4d764549abb780c2e75e5c04e41e5caeb790b9a8278e3`
(758 files). Two production files / 49 changed production lines; eight total changed/new files.

## B. Prioritized finding and resolution

**PRI21-FINAL-001 — Medium, high confidence, introduced; resolved on the corrected snapshot.**
The reviewed logging route signatures (`logs.py:88,169` before correction) resolved optional
identity before entering the body. Failed authentication therefore skipped the existing
weighted per-IP limit (`logs.py:97,178`). Global middleware hashes unverified Bearer text
(`middleware/security.py:151`), so changing token text also changes that global budget.

Reachable consequence: clients with rejected credentials or an unavailable provider can
continue triggering JWT/key retrieval without consuming the logging IP allowance. This is
an introduced control-ordering regression, not a claim that all rate-limit attacks are new:
the existing trusted-X-Forwarded-For and token-key weaknesses remain pre-existing.

Coordinator reproduction with an actual global middleware and a two-request IP allowance:
base statuses200,200,429 with2 provider calls; reviewed change503,503,503 with3 calls.
Independent reviewer reproduced both routes using real loopback HTTP/JWKS503 and the exact
base logging module. Evidence: `/tmp/pri21-rate-order-{base,current}.log`,
`/tmp/pri21-final-audit-probe.py` and its report/log. No production traffic.

Correction at current `logs.py:98,107` and `:183,191`: retain the existing weighted IP check first; explicitly call the shared
`get_optional_user_id(request, credentials)` next, outside the logging exception handlers;
then process events. Both routes use the shared Bearer parser and identity rule. This
preserves stable401/503, existing429 precedence and batch cost without extra abstractions.
The HTTPBearer parser itself performs no JWT/provider work.

New route regression covers single/batch and invalid-token/provider-error cases with rotating
credentials. Four failures observed before correction; after correction the focused auth,
logs, bootstrap, transport, cross-user and admin suite passed94. A denied request emits no
frontend event log; exhausting the IP budget prevents further JWT verification. Each test
gets a fresh real limiter with the same defaults to avoid cross-test budget contamination.

## C. Acceptance mapping

| Criterion / invariant | Required evidence | Current state |
| --- | --- | --- |
| Absent credentials alone are anonymous | Missing-header200/no provider; empty/unsupported/incomplete headers401 within budget | Focused checks passed |
| Invalid credentials never anonymous | Real signature/expiry/issuer/audience/subject negatives; no frontend log writes | Focused checks passed |
| Provider outage remains503 | Real loopback JWKS outage/recovery on both routes, under quota | Focused checks passed |
| Cross-user/admin restrictions | Existing mounted ownership/admin regressions, auth zero-SQL checks | Focused checks passed |
| Preserve pre-auth IP budget | Rotating rejected tokens stop at429 before further provider calls; batch weight preserved | Four red regressions now green; independent real-HTTP verification passed |

Native checks before the finding passed on the initial snapshot but are historical for
the corrected path. Corrected-state reruns and independent review passed. No checks are weakened, no skips added, and no test expects a helper's
computed result as its own oracle. Initial implementation red evidence is preserved in the
feature record; final audit adds a separately observed red/green correction.

HostedCI, verified secret scan, Docker and deployed checks remain pending for PRI-21.
No uncommitted local snapshot is represented as a hosted pass. New PostgreSQL migrations/
concurrency and frontend build/browser runs are not needed locally for unchanged boundaries;
full CI remains required after authorized submission. No production access or deployment.

## D. Design and applicable concerns

Shared optional presence policy owns absent-versus-rejected credentials; required JWT
validation owns signature/claims/provider errors. Logging retains its quota and ingestion
responsibilities. The duplicate identity implementation is removed; explicit sequencing is
necessary for the demonstrated quota invariant. No new mutable shared state, schema,
transaction, retry loop, dependency, or API success payload is introduced.

Security/privacy: validate real signed tokens, ignore body userId for attribution, deny
before event writes; preserve preview middleware precedence. No new token/PII logging.
Existing broader event-content retention is outside this task. Reliability/cost: bounded
existing provider behavior and quota-before-provider work; no new throughput claim.
Concurrency/data integrity: no new persistence/concurrency rule; denied batches cannot
partially write. Performance/memory: no new cache or collection; no benchmark claim.
UI/accessibility: unchanged frontend; inspected logger fetch/sendBeacon omit Authorization,
so anonymous compatibility remains. No UI/browser testing required for that unchanged path.
Operations: backend rollout, no migration/backfill; observe safe401/503/429 counts. Revert
restores fail-open behavior, so a scoped forward fix is preferable.

## E. Final verification results

Commands ran against the corrected snapshot, using Python 3.11 at
`/tmp/pri19-audit.WWLmok/venv/bin/python` and Node 22.23.2 for contract tooling.
Native Makefile uses dummy provider credentials and SQLite; focused checks explicitly set
test provider/database variables. No live provider or production database calls.

| Command/procedure | Executed by | Result / limits |
| --- | --- | --- |
| `make verify-backend-ci PYTHON=/tmp/pri19-audit.WWLmok/venv/bin/python` | Coordinator | Passed lint, 663 tests, 88.50% coverage, clean dependency audit. Log `/tmp/pri21-audit-corrected-backend.log`. |
| `make verify-contracts PYTHON=/tmp/pri19-audit.WWLmok/venv/bin/python` with Node22 PATH | Coordinator | Four tooling tests and generated-contract freshness passed. Log `/tmp/pri21-audit-corrected-contracts.log`. |
| `python -m pytest tests/core/test_auth.py tests/api/v1/test_logs_security.py tests/api/v1/test_route_security.py tests/api/v1/test_admin_metrics.py tests/integration/test_explicit_bootstrap.py tests/integration/test_optional_auth_transport.py -q -o addopts=''` from backend | Coordinator and independent reviewer separately | 94 passed each; coordinator log `/tmp/pri21-audit-correction-green.log`. Includes real loopback JWKS outage/recovery. |
| Real HTTP/JWKS adverse and success scenarios across both routes | Independent reviewer | 16 scenarios passed, including token rotation, weighted batches, correct attribution, absent/malformed credentials and preview denial. |
| Scoped Ruff on changed auth/log modules and route/transport tests; `git diff --check` | Coordinator | Passed. |
| Whole-source copy/hash/mode verification | Independent reviewer | Corrected isolated snapshot verified; source preserved. |
| Hosted CI, Docker, verified secret scanning on PRI-21 | Not run | No committed/pushed revision; mandatory delivery evidence remains pending. |

The 15 existing native-suite skips are 10 dormant Stripe tests, 4 PostgreSQL-only tests
and 1 hardcoded SQLite lock skip. Golden real-model tests are excluded by the native target.
These are not reported as passing. New PostgreSQL/concurrency/migration and frontend/browser
checks were not locally run: no changed persistence, data schema or user interface.

Reviewer `/root/pri21_final_audit`: fresh-context round2 found PRI21-FINAL-001; round3
verified the correction, completing the three-round task budget (round1 was initial
implementation review). Exact model IDs unavailable; no cross-model claim. Immutable
reports `/tmp/pri21-final-audit-independent.md` and `/tmp/pri21-correction-review.md` retain
the original finding and resolution separately. Only audit/feature evidence documentation
is updated after review; production/test/dependency content stays unchanged.

## F. Remaining decisions and minimum acceptance actions

1. Obtain owner-authorized commit/push and pass required hosted CI, including Docker,
   PostgreSQL and verified secret scanning on the actual submitted revision.
2. Review the intentional change for clients supplying invalid credentials:401 or503
   within quota,429 when the existing quota is exhausted. Current frontend anonymous
   logging remains compatible; no migration/backfill needed.
3. Preserve separate production/deployment authorization. Before release, observe deployed
   ingestion status behavior and existing public-preview policy in the approved environment.

Broader proxy trust, token-key/global rate limits, log retention, provider-cache policy and
the known pre-existing fresh-database profile mismatch are not resolved by this narrow change.
No uninspected environment is declared healthy. PRI-21 stays In Progress; no commit, push,
merge, deployment or production mutation was performed.
