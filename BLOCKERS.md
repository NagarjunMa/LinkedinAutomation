# Known gaps and release evidence

Reconciled against main `e53bea8` on 2026-09-18 for PRI-18. This replaces the
stale May review list; it is not a complete security audit or a launch approval.
PrismPro Linear owns issue status and prioritization. No runtime fixes are made here.

## Earlier findings addressed in code

| Earlier concern | Current evidence / limit |
| --- | --- |
| Uploads depended on local disk | [Upload workflow](backend/app/services/resume/upload_workflow.py) persists pending/ready/deleting state around private Storage operations. Operational reconciliation still needs monitoring. |
| Credit debit locked the wrong row | [Ledger](backend/app/services/credits/ledger.py) locks the matching User row; PostgreSQL concurrency tests are a hosted gate. |
| Rewriter lacked bounded shared retries | [Rewriter](backend/app/services/resume/rewriter.py) uses the shared retry policy; see [model manifests](docs/model-manifests.md). |
| Tailoring trusted unknown/project bullet text | [Tailor](backend/app/services/jd/tailor.py) builds canonical experience/project lookup and rejects unknown IDs or mismatched source text. This is not full evidence-ledger grounding. |
| JWT signature verification disabled | [Auth](backend/app/core/auth.py) verifies ES256 through JWKS with issuer/audience checks. Live configuration and isolation must still be verified. |
| No stored-export concurrency cap | [Export service](backend/app/application/export_service.py) has a process-local semaphore of three and acquisition timeout. It is not a global or per-user bound for every render path. |
| Active renderer relied on file-URI stylesheets | [Template engine](backend/app/services/pdf/template_engine.py) inlines styles for the current renderer. PDF visual QA is still required. |
| Mixed legacy/current resume schema and dormant profile runtime | Current schemas are separated; PRI-16 removed retired profile runtime. Historical migrations remain intentionally. |

The old generic dead-file checklist is superseded by scoped removal evidence
and architecture tests, not blanket permission to delete matching filenames.

## Unresolved source-backed findings

| Finding | Evidence and required follow-up |
| --- | --- |
| Browser lifecycle/resource bounds | [Renderer](backend/app/services/pdf/renderer.py) caches Playwright/browser per thread without explicit browser shutdown. Context cleanup is present; bounded export requests do not establish bounded lifetime across threads and other render callers. Backend owner: measure and review lifecycle/concurrency separately. |
| Failed-export audit persistence depends on refund transaction | [Export service](backend/app/application/export_service.py) stages error rows; [paid operation](backend/app/application/credits.py) commits on refund, but rolls back if refund fails. Backend owner: define/test independent failure-record durability and reconciliation. |
| Stored render latency is absent | Export rows do not receive `render_ms`; renderer emits structured latency logs. Backend owner: decide whether to populate or retire the column in a separate change. |

Do not assign invented issue numbers or mark these resolved from documentation
changes. Confirm matching Linear ownership before starting remediation.

## Required release evidence

Use the [readiness checklist](DEPLOYMENT_READINESS_CHECKLIST.md) and
[runbook](docs/production-mvp-runbook.md). In particular:

- Public preview stays restricted; internal product QA does not authorize launch.
- Hosted CI must pass on the actual change; local tests do not replace PostgreSQL,
  Docker or secret scanning. CI does not build the separate root Dockerfile.
- Supabase grants/RLS, private Storage, auth settings, scheduled-job execution and
  deployed smoke need current, environment-specific evidence.
- Credit schedule/backfill changes need concurrency/idempotency review; do not
  execute the historical ad-hoc SQL as a shortcut.
- PDF layout, user isolation and recovery require human review.
- PRI-17's root-image and explicit review evidence remain recorded on its issue;
  starting PRI-18 does not silently close those gates.

Use historical June smoke/audit results as provenance only. Record new evidence
with revision, environment, date, reviewer and remaining risks; keep personal data
and secrets out of tickets.
