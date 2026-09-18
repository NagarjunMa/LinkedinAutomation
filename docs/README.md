# PrismPro documentation

## Supported entrypoints

Use this allowlist for setup, architecture and release decisions. Other documents
are historical or specialized evidence, not an alternative launch procedure.

| Need | Maintained source |
| --- | --- |
| Product state, stack, local setup | [Repository README](../README.md) |
| Contributor workflow | [Repository guidance](../CLAUDE.md) and applicable AGENTS instructions |
| Approved target design and implementation sequence | [Architecture routing](architecture.md) |
| Deployment and migration safety | [Deployment entrypoint](../DEPLOYMENT.md) |
| Environment, auth, storage and release operations | [Production runbook](production-mvp-runbook.md) |
| Required release evidence | [Readiness checklist](../DEPLOYMENT_READINESS_CHECKLIST.md) |
| Source-backed unresolved findings | [Known gaps](../BLOCKERS.md) |
| Compose and dependency boundaries | [Local infrastructure](local-infrastructure.md) |
| Generated API boundary and client conventions | [API contracts](api-contracts.md) |
| Current model/prompt ownership and retry policy | [Model manifests](model-manifests.md) |

## Historical material

Email automation, Gmail/Arcade integration, Celery tracking, job-search marketing
guides, old frontend setup notes, `TECH_DEBT.md`, `progress.txt`, and dated
`superpowers/plans` / `superpowers/specs` record earlier designs or observations.
They do not authorize enabling those systems or establish current implementation.
The monthly-credit SQL guide is also historical pending operator reconciliation;
use the runbook's credit safety gate before executing any grant or schedule.

Retain historical files for provenance; use Git history for superseded versions
of maintained guides. Do not copy their commands into a release plan without
checking current code and obtaining approval.

## Authority and updates

Linear PrismPro issues own task status, blockers and approved amendments.
Linked architecture documents describe the intended product, not delivered
features. Source code, locks and CI describe current implementation; deployment
evidence establishes what actually runs. If these disagree, record the discrepancy
and resolve it explicitly rather than silently treating any one as a launch pass.

Changes to supported commands or architecture should update the relevant source
and its links in the same review. Never add secrets, production identifiers,
resumes, transcripts or private evaluation data to documentation.
