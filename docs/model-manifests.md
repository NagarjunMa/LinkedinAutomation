# Current resume/JD model manifests

PRI-13 centralizes the five existing OpenAI call configurations in
`backend/app/core/openai_client.py`. This is a compatibility refactor, not a new
generation or factual-grounding policy.

| Call | Response contract | Temperature |
| --- | --- | --- |
| evaluator | EvaluationReport.v1 (JSON object mode) | 0.2 |
| rewriter | RewriteResult.v1 (JSON object mode) | 0.4 |
| extractor | JDExtraction.v1 (SDK structured parse) | 0.1 |
| tailor | DiffPlan.v1 (SDK structured parse) | 0.3 |
| tailor_options | BulletDiff.v1 (SDK structured parse) | 0.4 |

All use the unchanged `gpt-4o-2024-08-06` snapshot and prompt version `1`.
Each immutable manifest records provider, model snapshot, prompt name/version,
template hash, schema version, and temperature parameters. Schema versions label
the existing response contracts; they do not introduce new API fields.

## Configuration and injection

FastAPI's `get_model_runtime` dependency supplies a lazy client factory and an
immutable snapshot of the manifest mapping to the resume/JD application services.
Those services pass the same runtime to the model calls. Non-AI operations do not
create an OpenAI client. Existing direct service calls retain default configuration.
Tests can override the dependency with `ModelRuntime(client_factory=...,
manifests=...)`; fake clients implement only the SDK methods needed by the test.
Injected client lifecycle belongs to its caller; the existing cached production
client lifecycle is unchanged. Configuration is internal, never an API input.

The existing `ResumeEvaluationV2.model_version` is read from the evaluator
manifest used for the call. This is the requested snapshot, not provider-returned
attestation. JD evaluations have no model metadata columns today. This change
does not persist full manifests, create a run store, or hide metadata in domain
JSON. Full run provenance requires separately planned persistence work.

## Maintaining versions

Prompt text remains in its service. The hash is SHA-256 of compact UTF-8 JSON
`[system_prompt, user_template]`, using `ensure_ascii=False` and separators
`(',', ':')`. It excludes rendered resume/JD content. Tests lock each hash and
the exact outgoing messages, schema/mode, model, and temperature.

For a future approved prompt change, increment its prompt version, recompute its
hash, update independent request expectations, and run the appropriate quality
evaluations. For response-schema changes, also review/update the schema version.
Do not merely regenerate hashes to dismiss unexpected drift. Hashes detect source
drift in CI; this is not runtime prompt attestation or proof of output truth.

No prompt or response content is added to ordinary logs. Credentials remain in
the existing settings/client boundary, not manifests. Existing cost estimates
still assume the current model: changing a model requires a separate pricing,
capability, quality, and rollout review, not just a manifest edit.

## Verification and rollout

Run `make verify-backend-ci` and `make verify-contracts`. The manifest tests cover
fake client/config injection through all five service paths and API dependency
overrides, immutable configuration, exact requests, safe logging, and stored
evaluation model metadata. Provider interactions use fixtures, not paid calls.

Backend-only rollout; no migration, dependency upgrade, or frontend coordination
required. Roll back by reverting the refactor. Hosted CI and owner review are
still required before merge. Monitor existing model-call errors, latency and
cost telemetry without collecting private prompt/response content. Existing
retry/quota and unknown-bullet-ID behavior is unchanged and belongs to PRI-14.

Reference checked 2026-09-15: [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
The existing JSON-object and schema-parse modes are intentionally preserved.
