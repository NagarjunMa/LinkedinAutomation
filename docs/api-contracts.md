# API transport contract generation

PRI-9 establishes generation and drift detection, not migration of API consumers.
Pydantic/FastAPI declarations remain the source of truth. Handwritten frontend domain
models and existing API clients are unchanged; resume consumer migration is PRI-10.

## Commands

Install `backend/requirements.lock` with Python 3.11 and run `npm ci` in `frontend`
with Node 22. Then, from the repository root:

```sh
make contracts-generate
make contracts-check
make verify-contracts
```

Equivalent frontend scripts are `npm run contracts:generate`,
`npm run contracts:check`, and `npm run test:contracts`. Set `PYTHON` to the supported
Python executable if needed. Generation does not require a running server, database,
production credentials, or provider calls.

Commit both `frontend/src/generated/api/openapi.json` and `types.ts` together with
the backend declaration changes. Never hand-edit these generated artifacts. The
exact generator version and its transitive dependencies are pinned in the npm lockfile.
Object keys are sorted; array order is preserved because it can carry schema semantics.
There are no timestamps or machine paths in generated output.

`contracts-check` regenerates in memory and compares both files byte-for-byte. It
returns nonzero for missing/stale artifacts without rewriting them. This detects
drift even when a stale file has already been committed; it does not rely on Git's
dirty-state output. Backend exporter tests run in the existing backend pytest suite;
generator tests and drift checks run in the existing frontend CI job and
`make verify-frontend-ci` / `make verify-ci`. Frontend CI therefore also installs the
locked Python dependencies. A passing generator cannot validate undeclared responses.

## Export boundary

The exporter imports the actual application in a fresh Python subprocess, with a
complete fixed dummy environment, an empty temporary working directory, disabled
dotenv loading, and Python isolated mode. It does not run lifespan hooks or invoke
endpoints/dependencies. Python socket audit events are blocked to catch accidental
import-time network access; this is not a sandbox for executing untrusted Python.
Import-time logs stay in the temporary directory and are not schema artifacts.

An explicit client namespace allowlist covers the existing resume, JD, credit,
export, tailored-library, job/application, profile/settings, logging, analytics,
waitlist, and public-preview routes. Admin dependencies (including inherited ones),
operational routes outside that list, hidden routes, dormant billing, and legacy
extraction are excluded **before** component schemas are assembled. New client
namespaces require an intentional allowlist update and tests. Production preview
flags remain unchanged; this tooling does not expose an HTTP OpenAPI endpoint.

The pinned FastAPI version uses `iter_route_contexts` for included routers; the
exporter preserves effective prefixes, dependencies and operation IDs. Review this
integration when upgrading FastAPI. TypeScript generation accepts only local JSON
references, without remote schema resolution. Authentication scheme declarations
remain in the contract but contain no credentials.

## Current limitations and review

Several existing JD/credit/job/download responses have no declared response model. Their
schemas remain unconstrained rather than fabricated. Before replacing handwritten
consumer types, add accurate backend declarations and response tests in the
appropriate follow-up issue. This change does not prove runtime response conformity,
authorization, or LLM grounding. Optional fields remain optional even with defaults;
date/time values stay wire-format strings. Review upload/binary handling when migrating
consumers rather than treating generated types as runtime validators.

Generated snapshots are mechanically large; review their paths, schemas, enums,
nullability and operation IDs separately from the small handwritten tooling diff.
The generator itself requires no runtime deployment or database migration. Its rollback
removes the tooling and CI check; existing clients continue using their current types. Never suppress drift or
weaken existing gates to land an incompatible schema change.

## Resume response contracts (PRI-61)

The six resume JSON endpoints now declare response models. HTTP envelopes live in
`backend/app/schemas/resume_responses.py`, reusing existing nested resume schemas;
the LLM's evaluation schema and business services are unchanged. List/detail retain
legacy aliases (`totalCount`, evaluation score aliases, and duplicate document IDs),
nulls, and the service's timestamp strings. Delete still returns an empty 204.

Invalid response data produces a generic 500 and a static error log without exception
inputs, resume text, or identifiers. This is response-shape validation, not factual
grounding. Validation happens after service execution: a 500 does not guarantee that
a write or credit debit was rolled back, so clients must not blindly retry mutations.

Deploy these backward-compatible backend declarations before migrating consumers in
PRI-10. No database migration is needed. Revert the response declarations, scoped
error handling and generated changes to roll back before consumer migration. After
clients adopt these contracts, coordinate rollback with those clients.

Implementation references (checked 2026-09-13):

- [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/)
- [Scoped APIRoute handling](https://fastapi.tiangolo.com/how-to/custom-request-and-route/)

## JD/export/credit frontend migration (PRI-11)

`workflow-contracts.ts` derives request/response types from generated paths and
components. `types-v2.ts` re-exports them so existing UI imports remain stable;
tailored-library and analytics contracts are not migrated here. Apply commands
retain the complete `ChangeItem` union, and the version-based export command still
requires a non-null version ID rather than allowing the wire schema's empty shape.

`workflow-response-parser.ts` checks successful status codes and nested response
shapes with the existing Zod dependency. UI-required optional collections/nulls
receive declared defaults, but IDs and truth-verification states never do. A null
apply warning becomes undefined for the existing preview component. Validation
failures use static API errors without inputs, causes, logging or mutation retries;
non-success HTTP errors retain the shared client's behavior.

PDF downloads use the generated media-type contract while returning browser Blobs.
They require a full 200 response, application/pdf and non-empty content, preserving
the bytes without claiming to validate PDF safety or factual grounding. Path IDs
are encoded as individual segments. No backend, model, billing, authentication,
dependency or generated-artifact changes are included.

Deploy after the PRI-62 backend prerequisite. Rollback reverts this frontend
migration without a database migration. Watch static response-validation failures
and download failures; do not attach JD/resume content to telemetry.

## Resume v2 client migration (PRI-10)

`resume-contracts.ts` derives the v2 client's seven operation contracts from the
generated paths/components. `types-v2.ts` re-exports these names for existing
callers. The editor document model derives from the upload contract with present
collections and nullable fields; the response parser supplies only defaults
already declared by the backend. IDs, raw text, scores and required fields never
receive fabricated fallbacks.

Editor `ChangeItem` commands narrow the generated transport schema to a
discriminated union: each action requires its non-null fields and excludes fields
belonging to other actions. `VersionRequest` uses those commands while retaining
the generated envelope. Resume and JD callers share this safeguard; compile-time
regressions run through `tsc`/the production build, not Vitest alone. This does not
add runtime request validation or change the backend's permissive request schema.

The existing Zod dependency validates successful response bodies and exact success
statuses through the shared client's response-parser callback. Malformed JSON or
invalid schemas produce the static `APIError('Invalid resume response')` without
payloads, identifiers, validation causes or logging. Declared fields are retained;
unknown additive fields are ignored. Existing HTTP failure handling and session
authentication remain owned by the shared client. No retries are introduced.

Runtime schemas are checked against generated output types and covered by negative
and compatibility tests; generated types alone do not validate JSON or facts.
Older `resume.ts`/`enhanced-api.ts` compatibility adapters and legacy UI models are
outside this v2-client slice. The new list/detail/delete methods expose transport
responses, not the older adapters' UI projections.

Deploy only after the PRI-61 backend prerequisite. No migrations or dependency
upgrades are required. Rollback reverts the frontend migration and leaves the
backward-compatible backend contracts in place. A server write may have completed
before a response fails validation; do not blindly retry mutations.

Primary references (checked 2026-09-12):

- [FastAPI OpenAPI generation](https://fastapi.tiangolo.com/how-to/extending-openapi/)
- [openapi-typescript Node API](https://openapi-ts.dev/node)

## JD/export/credit response prerequisite (PRI-62)

JD analysis now declares `JDAnalysisResponse`, reusing the existing `JDExtraction`
and `DiffPlan` models. Credit balance declares `CreditBalanceResponse`; it retains
the ledger's integer result without clamping or changing debit/refund behavior.
PDF download declares only `application/pdf` with a binary schema. It still returns
the same bytes, attachment filename and `private, no-store` headers; clients must
decode it as a Blob rather than JSON.

JD and credit routers opt into `PrivateResponseRoute`, the shared mechanism
extracted from PRI-61's resume handler. Invalid response bodies return a static 500
without logging validation inputs, identifiers or exception tracebacks. This also
contains response-validation failures on JD apply/options. Existing application
errors and request validation are unchanged. Resume-specific error text and log
category remain unchanged through `ResumeResponseRoute`.

No frontend consumers, model prompts, business services, dependencies or migrations
change. Deploy this backend prerequisite before PRI-11. Response validation can
follow committed work and does not undo it; do not automatically retry mutations.
Before client migration, rollback reverts these declarations, shared helper and
generated artifacts; after adoption coordinate with the frontend rollback.

Implementation references (checked 2026-09-14):

- [FastAPI additional response media types](https://fastapi.tiangolo.com/advanced/additional-responses/)
- [Scoped APIRoute handling](https://fastapi.tiangolo.com/how-to/custom-request-and-route/)
