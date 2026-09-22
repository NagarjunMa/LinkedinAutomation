# PRI-21 — Optional authentication fails closed

## Execution context

Requirement: [PRI-21](https://linear.app/prismpro/issue/PRI-21/make-optional-authentication-fail-closed-on-provider-outages), verified through `linear_prismpro` in PrismPro.
Base: main `21bc3d556c4cae5eef239b5a5e52133bc60d5c8f` (PRI-20, PR #57).
Branch: `security/pri-21-fail-closed-optional-auth`. Current change is uncommitted.
Updated 2026-09-21. Final audit found and corrected PRI21-FINAL-001 (rate-limit ordering).
The [final audit](optional-authentication-audit.md) supersedes earlier verification status.
Corrected-state native gates and final independent review passed. Next: owner-authorized
delivery and hosted checks; the issue remains In Progress.

| Verified location | Responsibility / action |
| --- | --- |
| `backend/app/core/auth.py::get_optional_user_id` | Sole optional-identity rule; distinguish absent header from invalid supplied credentials and reuse required identity validation. |
| `backend/app/api/v1/endpoints/logs.py` | Both mounted log POST routes call the shared identity rule after weighted IP limiting and before event writes; duplicate failure-swallowing helper removed. |
| `backend/app/api/v1/api.py`, `backend/app/main.py` | Verified route mounting and existing public-preview guard. No changes. |
| `backend/tests/core/test_auth.py` | Direct dependency contract; update old invalid-token anonymity expectation. |
| `backend/tests/api/v1/test_logs_security.py` | Actual mounted single/batch routes, signed-token denial, attribution and forbidden log effects. |
| `backend/tests/integration/test_optional_auth_transport.py` | Local HTTP JWKS outage and recovery through real PyJWT verification. |
| `backend/tests/integration/test_explicit_bootstrap.py` | Existing zero-SQL checks for identity dependencies, including optional auth. |
| `frontend/src/lib/logger.ts` | Read-only compatibility inspection: fetch and sendBeacon supply no Authorization header; requests remain anonymous. |

Load this contract, auth/log modules and their tests before continuing. Broaden inspection
if another optional identity consumer appears. Other feature work is not included.

## Problem, goal and acceptance criteria

The shared optional-auth helper suppressed all authentication HTTP errors. A separate
mounted logging helper also suppressed all token/provider failures and accepted an
anonymous event. Fixing the unused shared helper alone would leave reachable behavior unchanged.

The approved issue requires:

1. Missing credentials are the only implicit anonymous case.
2. Invalid credentials do not masquerade as anonymous.
3. JWKS/provider outages remain 503.
4. Cross-user and admin tests pass.

Anonymous logging remains intentional. Protected routes still require credentials.
Supplied payload `userId` never establishes identity. A denied request must not write
frontend log entries, including partially processing a batch.

## Scope, design and risk

**Critical risk; full documentation:** authentication and attribution boundary.
Two production files, no new abstraction or persistence. The issue's 3–8-file estimate
is not a reason to add files; this solution remains below the 500-production-line budget.

`get_optional_user_id` owns presence policy. Required identity validation owns JWT claims
and existing error mapping. Logging owns ingestion and its existing weighted IP budget. Each route checks that budget,
then explicitly calls the shared identity rule outside the logging try/except. This preserves
401/503 without bypassing the pre-authentication limit. No duplicate identity helper remains.

FastAPI `HTTPBearer(auto_error=False)` returns None for both absent and malformed headers
(verified against installed FastAPI 0.138.0). Inspect raw header presence to prevent empty,
unsupported-scheme and incomplete Bearer credentials from entering the anonymous path.
The shared required validator checks a nonempty string subject and preserves safe 401/503.

No new database writes, mutable global state, retry loops, dependencies, schema, API payload,
frontend UI, JWT algorithm/cache policy, pricing or preview rules. No raw tokens enter
new logs. Existing broader logging content/retention and rate-limit design are not changed.
Authentication follows the endpoint-specific logging limiter. The global middleware also
runs first, but its token-derived key cannot replace the endpoint IP budget when an attacker
rotates credentials. No throughput claim is made.

## Implementation plan and initial evidence (superseded where corrected)

1. Verify predecessor merge/green PR CI, update main, retire old merged local branch.
2. Inspect shared helper, mounted routers, duplicate attribution logic and frontend caller.
3. Establish unchanged focused baseline; write mounted-route regressions and observe red.
4. Correct shared policy and integrate both actual consumers; update old contract tests.
5. Verify token/adversarial cases, local JWKS transport, affected native checks, and fresh review.
6. Record remaining gates; leave issue open for final verification/owner delivery.

Baseline (unchanged PRI-20 implementation): focused auth/bootstrap/route/admin/log suite,
56 passed. New route tests before production edits: 28 failed, 6 passed; failures were
HTTP 200 instead of expected 401/503, not setup/import errors. After correction the expanded
focused suite passed 88. Existing tests expecting invalid-token anonymity were changed
because that behavior is explicitly prohibited by PRI-21; no skip/threshold weakening.
Logs: `/tmp/pri21-baseline.log`, `/tmp/pri21-red.log`, `/tmp/pri21-green.log`.

| Criterion | Check and independently specified expectation | Wrong implementation rejected |
| --- | --- | --- |
| 1 | Both routes: absent header 200, anonymous attribution, no JWKS access; empty/Basic/incomplete Bearer 401. | Treat all HTTPBearer None results as anonymous. |
| 2 | Signed valid identity wins over spoofed body; expired/wrong issuer/audience/signature/missing-empty-nonstring subject 401; zero log calls. | Catch every verification error or skip subject validation. |
| 3 | Real PyJWKClientConnectionError 503; local HTTP JWKS 503 then valid keyset 200; no log before recovery. | Catch provider error as anonymity or route 500; permanently cache failure. |
| 4 | Existing route-security/admin tests; shared no-SQL/bootstrap tests. | Drop path ownership/admin restrictions or reintroduce auth writes. |

Test fixtures use ephemeral synthetic keys, SQLite and loopback HTTP only. Signature and
claims verification are real; most route tests replace only key lookup. The transport test
runs real PyJWT retrieval against a local server and closes it after each case. These do
not establish live Supabase outage behavior or deployed readiness.

## Compatibility, rollout and rollback

No HTTP success payload or schema changes. Current frontend logger and beacon remain
compatible because they omit Authorization; no UI/browser flow changed. Any client supplying
bad credentials now gets 401, and provider failure yields 503, rather than anonymous 200.
Clients may retry 503 according to their existing bounded policy; no automatic replay added.
Backend-only rollout, no migration. Observe log-ingestion 401/503 rates without tokens or
payloads. Reverting the two production files restores prior behavior but reopens this
fail-open boundary; prefer a scoped forward fix. No data backfill/recovery needed.

## Verification scope and remaining gates

Required local command: `make verify-backend-ci PYTHON=/tmp/pri19-audit.WWLmok/venv/bin/python`
(Python 3.11; dummy credentials/SQLite from Makefile). Scoped commands use
`python -m pytest <paths> -q -o addopts=''` with explicit test provider/database settings.
Contract tooling checks use Node 22 and the same Python. Hosted CI requires backend/frontend,
Docker, PostgreSQL and secret scan on submitted revision; main's successful PRI-20 run
is predecessor evidence only.

Frontend full build/browser, new PostgreSQL concurrency/migrations and accessibility are
not locally rerun for this change: no UI/client/schema/transaction changes. Existing
preview/security tests verify the affected route boundary. Docker/hosted release checks
remain pending until submission; production access/deployment is not authorized.

Initial local disk exhaustion was relieved by removing only this worktree's ignored
regenerable Next build cache; no source or audit evidence deleted. Capacity later recovered to approximately 3.8 GiB; no additional cleanup was performed. Original checkout's unrelated edits are excluded.

## References and review status

Supabase JWT verification guidance and changelog reviewed 2026-09-21:
[JWT documentation](https://supabase.com/docs/guides/auth/jwts),
[changelog](https://supabase.com/changelog.md). No relevant provider API change is needed.
Locked PyJWT 2.13.0 and installed FastAPI 0.138.0 behavior inspected; no upgrade proposed.

Initial independent review completed in one round; final audit and correction review use
rounds two and three of the same three-round budget. See the final audit for the current
verdict. Implementation/gates do not authorize delivery. PRI-21 remains In Progress.

## Historical verification — pre-audit implementation

Tested source: main base above plus the complete uncommitted snapshot
`cdf44e56e935b26fcbed81eed35a9978e2cf9d3da6dba18f28fe2d7ca3d3e7b7` (757 files).
This was the implementation snapshot before the final audit correction. Its results are
historical, not current verification of the rate-limit fix. Two production files, 41 changed production lines; seven total
changed/new source, test and documentation files. No staged changes.

| Command/procedure | Result | Evidence and limitation |
| --- | --- | --- |
| `make verify-backend-ci PYTHON=/tmp/pri19-audit.WWLmok/venv/bin/python` from repo root | Passed | Final run: 659 passed, 15 skipped, 88.50% coverage; Ruff and dependency audit passed. `/tmp/pri21-backend-final.log`. |
| `make verify-contracts PYTHON=/tmp/pri19-audit.WWLmok/venv/bin/python` with Node 22 on PATH | Passed | Four tooling tests, tooling lint and generated-contract freshness. `/tmp/pri21-contracts.log`. |
| `python -m pytest tests/core/test_auth.py tests/api/v1/test_logs_security.py tests/api/v1/test_route_security.py tests/api/v1/test_admin_metrics.py tests/integration/test_explicit_bootstrap.py -q -o addopts=''` from backend | Passed | 88 focused tests; `/tmp/pri21-green.log`. |
| `python -m pytest tests/integration/test_optional_auth_transport.py -q -o addopts=''` from backend | Passed | Both real loopback-JWKS cases; `/tmp/pri21-transport.log`. Initial invocation from repo root failed path lookup, then rerun correctly; setup failure is not red evidence. |
| Scoped Ruff for auth/log modules and new route/transport tests; `git diff --check` | Passed | No new syntax/unused-import or diff-whitespace errors. |
| Source-manifest check before/after native checks | Passed | Whole-source provenance current before evidence-only document update. |
| Hosted CI and Docker on PRI-21 | Not run | Change remains uncommitted/unpushed. PR #57/main CI success is predecessor evidence only. |
| New PG/migration, frontend build/browser or live-provider checks | Not run | No changed persistence/UI/client/algorithm; no authorized deployed access. |

The 15 existing skips are 10 dormant Stripe cases, 4 PG-only cases, and 1 hardcoded SQLite-lock case.
No skip was added. Native target intentionally excludes live-model golden checks.
Initial backend gate: 657 passed before transport-test addition; final 659-test run supersedes it.
No claim that SQLite proves PostgreSQL concurrency. Existing profile-schema mismatch from
PRI-20 remains outside this authentication change.

PR #57 post-merge CI finished successfully:
[main CI](https://github.com/NagarjunMa/LinkedinAutomation/actions/runs/35680410527).
That closes the predecessor's hosted gates, not its production-job/deployment prerequisites.

## Initial independent review and acceptance (historical)

Fresh-context reviewer `/root/pri21_independent_review` found **no material findings**.
Exact model ID is unavailable; no cross-model claim. One round used. The reviewer
verified an isolated 757-file copy against the captured source before/after execution,
then passed 90 focused tests, 18 additional mounted-route adversarial cases and 6 actual-app
preview-mode cases. No production changes or recursive reviews were performed.
Immutable report: `/tmp/pri21-independent-review.md`; executable additional probe:
`/tmp/pri21-independent-probe.py`. The reviewer read the supplied Linear contract but did
not independently fetch Linear; the coordinator fetched and verified the PrismPro issue.

At that snapshot, the four issue criteria passed locally: absent-header-only anonymity, explicit credential
rejection, provider 503 with recovery, and preserved cross-user/admin restrictions. Source
review confirms shared validation ownership and no duplicated logging identity policy.
That initial review missed rate-limit ordering. Final audit finding PRI21-FINAL-001 and
its correction invalidate these prior results for the changed path; consult the final audit. Hosted CI/secret scan/Docker and deployed verification remain unestablished for
PRI-21; no commit/push/merge/deployment has occurred.

Scoped lesson: parsed credentials alone cannot distinguish missing credentials from a
rejected Authorization header when HTTPBearer has auto_error disabled. Preserve header
presence at this optional-auth boundary and keep malformed-header route regressions. Also
trace semantically equivalent consumers: fixing an unused shared helper would have missed
the mounted logging fallback. No broader identity-policy rewrite is implied.

Final-audit lesson: authentication must precede event writes but must not bypass an existing
pre-authentication abuse budget. A global limiter keyed by supplied token text is not evidence
of preserved IP limiting. Test rotating credentials and batch weight at the actual route.
