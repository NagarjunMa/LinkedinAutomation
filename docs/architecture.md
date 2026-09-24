# Architecture and durable context

Reviewed 2026-09-18 for PRI-18. Approved specifications are stored in the
[PrismPro Linear project](https://linear.app/prismpro/project/prismpro-c4d88eed0985),
not solely in a contributor's checkout. Team access to that project is required.

## Approved target specifications

- [Target product architecture](https://linear.app/prismpro/document/prismpro-target-product-architecture-3456902f9954):
  canonical evidence history, ownership, model boundaries and artifact lineage.
- [Resume requirements and grounded generation](https://linear.app/prismpro/document/prismpro-resume-requirements-and-grounded-generation-a923d2b53a7d):
  deterministic evidence selection, safe render, optional wording proposal,
  closed validation reasons and fallback.
- [Implementation sequence](https://linear.app/prismpro/document/prismpro-approved-implementation-sequence-2026-08-09-snapshot-cd17ef0e4d68):
  phased contracts, evaluation, persistence, controller, UI and release gates.

These preserve the approved 2026-08-09 specifications, published on 2026-09-18.
Their former local filenames were `11-target-product-architecture.md`,
`13-resume-requirements-and-grounded-generation.md` and
`06-implementation-sequence.md`. Do not require those ignored files to exist
in a fresh clone. Supplementary discovery references are provenance; they have
not all been published. Retrieve/review a missing phase dependency before that
phase starts, and record the gap in Linear if it is unavailable.

The newer branch policy in [repository guidance](../CLAUDE.md) overrides old
`feat/` and unnumbered example branch names. Target sequence order remains intact.
Amendments need owner approval and must be recorded in the applicable Linear
document and issue; do not create a competing canonical copy in local notes.

## Current implementation versus target

Current code has a Next.js frontend, FastAPI delivery/application/service layers,
SQLAlchemy/Alembic persistence, Supabase Auth/private Storage, resume/JD model
calls and Playwright PDF rendering. See [API contracts](api-contracts.md),
[model manifests](model-manifests.md), [LLM telemetry](llm-telemetry.md) and
[local infrastructure](local-infrastructure.md).

The proposed evidence ledger, interview controller, confirmed-evidence bullet
plans and claim-revision lineage are target work. Existing parsing, model schemas,
retry bounds and source-bullet checks do not prove those target guarantees.
Do not advertise deterministic factual generation or LLM-disabled artifacts
until their corresponding acceptance and release gates pass.

Public preview, internal product testing and a full product launch are separate
release states. [README](../README.md) describes repository defaults;
[the checklist](../DEPLOYMENT_READINESS_CHECKLIST.md) defines required evidence.
No document synchronization in PRI-18 changes application behavior.

Parser evaluation: [PRI-19 AnyDoc benchmark](anydoc-benchmark.md) records the synthetic corpus, verified code locations, limits and adoption decision; it does not change the production parser.

Account setup: [PRI-20 explicit bootstrap](account-bootstrap.md) defines the
read-only authentication boundary, transactional first-account allowance and
existing database job's recurring-grant ownership, with rollout prerequisites.

Optional identity: [PRI-21 optional authentication](optional-authentication.md) owns
absent-versus-invalid credentials and shared frontend-log attribution behavior.

Credit serialization: [PRI-22 credit locking](credit-locking.md) defines supported
transaction modes, fail-closed locks and paid-operation rollback behavior.

Backend image privileges: [PRI-24 container runtime](backend-container-runtime.md)
defines the non-root account, writable paths, browser-sandbox limit and image
smoke gate.
