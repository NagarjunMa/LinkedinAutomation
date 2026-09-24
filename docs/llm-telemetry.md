# PRI-23 — LLM telemetry privacy and pricing

Status: locally verified, awaiting hosted and rollout evidence, 2026-09-23. This is the full feature record
for a Critical change to ordinary production logs. The verified issue and plan
are [PRI-23](https://linear.app/prismpro/issue/PRI-23/make-llm-telemetry-privacy-safe-and-model-price-accurate).

## Execution context

- Base: clean `main` at `ce122daa9ecebe77a12373d3ccead4fba5b6f853`.
- Branch: `security/pri-23-privacy-safe-llm-telemetry` in the isolated
  `linkedin-automation-pri-23` worktree. The original checkout has unrelated
  frontend edits and is outside this change.
- Current sources: `backend/app/core/llm_logging.py` owns aggregate events and
  price calculation; `openai_client.py` owns immutable manifest pricing;
  `model_retry.py` supplies actual attempt numbers. Five calls in resume and JD
  services pass their exact manifest and provider-returned model ID. This is
  seven production files. The disabled legacy route is tracked separately in
  [PRI-64](https://linear.app/prismpro/issue/PRI-64/make-dormant-legacy-llm-job-extraction-logs-privacy-safe-before).
- Next step: owner-directed delivery, hosted gates and log-consumer rollout
  checks. No commit/push or production change has been made.

## Contract and risk

Active manifest-backed LLM logs previously included raw user IDs and cost
calculated from global placeholder rates. A log collector and its operators
are outside the user-content trust boundary, so this is Critical privacy work.
The disabled legacy route has further logging leaks; it must remain disabled
until PRI-64 verifies that whole route.

Acceptance criteria from PRI-23:

1. Active LLM records contain no raw user ID, prompt, response, resume, JD,
   or claim text. Operation labels are internal aggregate keys. Per-user log
   attribution is intentionally removed; no new secret or HMAC key is needed.
2. An estimate requires versioned pricing for the exact requested and returned
   model snapshot, plus input/output and cached-input token counts. Any missing
   or inconsistent input yields `cost_usd: null` and `cost_status: unavailable`.
3. Safe telemetry retains latency, input/output tokens, closed failure category,
   actual retry count, and fallback-used fields. The active model calls have no
   fallback path, so their `fallback_used` value is false. Provider exception
   messages remain in raised errors for existing callers, never in telemetry.
4. Negative tests inspect both formatted logs and raw log-record metadata for
   prohibited fields.

Request payloads, responses, retry limits, external API contracts, auth,
storage and model prompts remain as before. No new schema, dependency or
frontend work. The log schema changes internally: `llm_cost` becomes
`llm_usage`, per-user attribution disappears, and unknown cost is null rather
than fabricated zero. Log consumers must update queries during rollout.

## Design decisions

The current five manifest-backed calls already share `ModelRuntime`; pricing
belongs on the same immutable `ModelManifest` because it must change with the
exact model snapshot. Validation rejects a manifest whose pricing names a
different snapshot. `llm_logging` calculates prices from validated numeric
usage only and emits operation aggregates. It does not read user IDs or content.

The published standard `gpt-4o-2024-08-06` rates recorded in the manifest are
$2.50 per million uncached input tokens, $1.25 per million cached input tokens,
and $10.00 per million output tokens, with a 2026-09-23 observation version.
[OpenAI's prompt-caching announcement](https://openai.com/index/api-prompt-caching/)
lists those rates and the `cached_tokens` usage field; the
[current GPT-4o model page](https://developers.openai.com/api/docs/models/gpt-4o)
still lists the same standard rates when checked 2026-09-23. This is an estimate for
standard calls, not a bill, discount attestation or future pricing guarantee.
If the returned model ID or cached-token detail is absent, no cost is emitted.

Tenacity's existing retry policy stays authoritative. Its before-attempt hook
sets an async-task-local attempt number; the next call resets it to one. The
logger records each provider attempt through response validation in `llm_call`;
invalid response schemas are failures. Usage is recorded after a provider
response even if later validation fails. No provider retry or fallback policy changed.

## Evaluations

| Criterion | Check that rejects a plausible wrong implementation | Current result |
| --- | --- | --- |
| No PII/content | Synthetic user/resume/JD/error sentinels are absent from active formatted and raw records | Focused tests passed |
| Exact price or unavailable | Independently calculated cached-token example, changed response model, absent cache detail, invalid usage and mismatched pricing manifest | Focused tests passed |
| Operational dimensions | Real Tenacity retry-with path records attempts 0 and 1 with safe failure categories; invalid evaluator schema records a safe failure; active calls record fallback false | Focused tests passed |
| Compatibility | Existing five-call request/manifest and retry tests, plus changed evaluator log contract | Final narrowed-source backend gate passed: 692 passed, 26 skipped, 88.82% coverage |

Behavioral red phase on the unchanged base: active-path tests failed for raw
IDs, fabricated cost and omitted failure events. A further invalid-schema test failed because the attempt
was recorded as successful; it passed after validation moved inside the measured
attempt. These were assertion failures, not setup failures. The
existing log-cost test was updated to the approved unavailable-cost behavior;
custom-model tests explicitly remove inherited pricing and a negative test
rejects a mismatched priced manifest. No test or threshold was weakened.

Focused command from `backend` with synthetic environment values:

`python3.11 -m pytest tests/core/test_llm_telemetry.py tests/services/resume/test_evaluator.py tests/core/test_model_manifests.py tests/core/test_model_retries.py -q -o addopts=''`

On the narrowed diff, 174 focused tests passed with one known Starlette
deprecation warning. `make verify-backend-ci` passed after the final raw-record
assertion: backend Ruff, 692 passed/26 skipped with 88.82% coverage (80% floor),
and `pip_audit` found no known vulnerabilities. `make verify-contracts` passed after
installing the lockfile-pinned frontend dependencies in this isolated worktree.
The independent read-only review found the initial scope overrun, then reviewed
the narrowed source manifest `f5ba9ddf2b49739f634dc008d7b684eedfc6b35608a729c435737af49f817295`
and found no material active-path defect. It checked source and diff freshness
but did not independently run tests. Hosted checks are not yet claimed.

## Final local audit, 2026-09-23

The reviewed integration target is `main` at
`ce122daa9ecebe77a12373d3ccead4fba5b6f853`; the branch still has no commit
beyond that base. The audit included all staged, unstaged and untracked files in
the isolated worktree. The original checkout's frontend edits remain excluded.
Risk remains Critical because structured LLM records cross the private-content
boundary. The prior fresh-context review's source verdict remains applicable:
the final code and tests match its reviewed snapshot; subsequent edits were
documentation-only. Seven production files (311 added/deleted production lines)
remain within the approved PRI-23 budget. No material active-path finding remains.

Acceptance mapping: active records omit user/content in formatted and raw
metadata; exact-snapshot rates and cache counts produce estimates, otherwise
cost is unavailable; all five callers emit latency, usage, closed failure,
retry and false fallback dimensions. Negative tests cover private identifiers,
provider error content and invalid schemas. The disabled legacy route is not
covered; PRI-64 must be completed before that flag is enabled.

- `make verify-ci`: backend Ruff, 692 passed/26 skipped, 88.82% coverage and
  dependency audit passed; contracts, frontend lint and type check passed.
  Frontend build then failed with local `ENOSPC`. This was a blocked attempt,
  not a passing gate.
- The final `CI=1 make verify-ci` rerun passed end to end on unchanged code and
  tests after space was restored: backend, contracts, frontend lint/types/build,
  253 unit tests, 8/8 MVP browser tests and both dependency audits.
- After clearing generated `.next` and disposable npm cache, an initial local
  frontend run built and passed unit coverage, but one of eight parallel MVP
  browser tests timed out. That unchanged test passed alone. The complete
  `CI=1 make verify-frontend-ci` rerun passed: contracts current, lint/types/
  build passed, 253 frontend unit tests passed, 8/8 MVP browser tests passed
  with the CI configuration's one worker, and production npm audit found zero
  vulnerabilities. This supports a timing-sensitive local test, not a proven
  PRI-23 regression or a claim that it cannot recur.
- The CI-only public-preview landing smoke passed 8/8 with the same isolated
  synthetic environment. A synthetic private-ID/error test through
  `RailwayOptimizedFormatter` passed after supplying the required local
  database setting. The first formatter attempt failed during configuration
  setup and is not counted as a test result. `git diff --check` passed.

The backend suite's 26 skips are Stripe/billing and PostgreSQL concurrency
cases under its SQLite/default flags. No real-provider golden call was run.
Hosted PostgreSQL migration/concurrency, Docker builds, TruffleHog scan, and
production log collector/dashboard queries are not verified locally; Docker's
daemon was unavailable and the local PostgreSQL instance was not treated as
an isolated test database. These remain required delivery/rollout evidence,
not passing checks. No database, public API, migration or frontend source
changed. Deployment should update dashboards/alerts for `llm_usage` and null
cost before relying on these events; rollback restores raw-ID logging and is
therefore less safe than a forward correction.

## Rollout and recovery

This is a backend-only log contract change, without migration or backfill.
Deploy only after log dashboards/alerts that read `llm_cost` or `user_id` are
updated to operation aggregates and nullable estimated cost. Confirm the
production log formatter/collector does not add provider exception text.
Rollback by reverting the code change if necessary, but that restores the
private-ID logging; prefer a scoped forward correction. The disabled legacy
route must not be enabled before PRI-64 is complete. This task does
not authorize a deployment or real-provider request.
