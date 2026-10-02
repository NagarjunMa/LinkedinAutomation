# PRI-65: pypdf dependency security repair

Updated: 2026-10-01. Status: implemented; local application gates passed; delivery pending.

### Problem

Main CI at 12ceed285ddb77c04b3bbf1b62810ec95b89dea6 fails its backend dependency audit: pypdf 6.17.0 has seven reported advisories. This prevents Docker checks and blocks PRI-28 production verification. Run: https://github.com/NagarjunMa/LinkedinAutomation/actions/runs/36889685081.

### Goal

Clear all current dependency audit findings in one reviewed repair while preserving resume PDF behavior.

### Implementation Plan

Owner authorized the fix and a narrow repair branch while main CI is red on 2026-10-01. Raise pypdf's floor to >=6.19.0,<7 in backend/requirements.in and regenerate backend/requirements.lock with Python 3.11/pip-tools, targeting pypdf==6.19.0. Preserve all other package versions. Record evidence in docs/dependency-security.md and link it from the dependency guide. Run PDF/upload regressions, clean-environment dependency compatibility, make verify-backend-ci, make verify-frontend-ci, and fresh complete backend/frontend audits. Obtain a fresh independent review. Hosted PR checks, merge and post-merge CI remain release gates; commit/push/merge require owner authorization.

### Security Considerations

Initial risk: Significant — a production PDF library changes, but authentication, authorization, billing and application security-control logic do not. PdfReader is used on generated exports for visible-content validation and page counts; PdfWriter also creates test fixtures. Do not change upload limits, audit exclusions, CI gates, production credentials or live data. No major-version upgrade. No migration. Roll forward to a fixed version for recovery; reverting to 6.17.0 reintroduces the audit findings.

### Expected Files / Components

backend/requirements.in; backend/requirements.lock; docs/dependency-security.md; docs/local-infrastructure.md. Existing PDF renderer/template/export/upload tests supply compatibility coverage.

### Acceptance Criteria

1. All currently reported backend and frontend dependency vulnerabilities are cleared by fresh full-lock audits, with no ignored findings or skipped packages.
2. Only pypdf changes in the package inventory; an isolated Python 3.11 environment installs the lock and passes pip check.
3. Existing PDF rendering, page count, layout, links, re-upload and upload rejection tests pass; both repository-native application gates pass without weakened checks.
4. Independent review has no unresolved material findings; exact base, final source and validation evidence are recorded.
5. Hosted PR CI, owner review, merge and green main CI are required before closure and PRI-28 verification.

### Implementation Progress

Baseline: fresh PyPI audit examined 92 locked Python packages, identifying only pypdf (seven advisories); full npm audit including development dependencies reports zero vulnerabilities across 912 dependencies. No packages skipped. This dependency configuration change uses the existing failing audit as red evidence and native lock/audit/behavior validation; no test asserting a literal version will be added.

### Decisions / Deviations

Full feature record for Significant risk. Keep this repair separate from PRI-28. Source of fix: https://github.com/py-pdf/pypdf/releases/tag/6.19.0 (inspected 2026-10-01). A prior local audit passed but now both local and hosted audits fail; cache versus advisory publication timing is unproven. No cache-cause claim or audit bypass is justified.

### Execution Context

- Base: `12ceed285ddb77c04b3bbf1b62810ec95b89dea6` (`main`).
- Branch: `security/pri-65-pypdf-security-update`; owner authorized implementation, including the exception to start this repair while main CI is red, and authorized commit/push on 2026-10-01.
- Skill: available `production-engineering-loop` v0.6.0; the requested `engineering-loop` catalog alias is unavailable. The repository checklist also applies.
- Verified source: `backend/app/services/pdf/renderer.py` owns `PdfReader` use; `backend/app/application/export_service.py` calls it through the existing export boundary. Both Dockerfiles and CI install `backend/requirements.lock`.
- Existing compatibility checks: `backend/tests/services/pdf/`, `backend/tests/services/resume/test_file_security.py`, and export/API tests covered by the native backend suite.
- Baseline audit logs: `/tmp/prismpro-dependencies-backend.json` (92 packages, seven pypdf findings, no skips) and `/tmp/prismpro-dependencies-frontend.json` (912 dependencies including dev, zero findings).
- Next step: complete the authorized commit/push, then hosted PR checks and owner review. Independent review found no material issues and is recorded in Linear PRI-65; merge and deployment require separate authorization.

### Acceptance Evidence (2026-10-01)

| Criterion | Evidence | Current result |
| --- | --- | --- |
| 1 — no current audit findings | Fresh-cache `pip_audit -r requirements.lock --format json` and `npm audit --include=dev --json` | Passed: 92 Python packages, no skips; 912 frontend dependencies; zero findings in both |
| 2 — bounded, compatible dependency change | Inventory comparison with base; clean Python 3.11.1 install of lock plus CI tools; `python -m pip check` | Passed: only pypdf 6.17.0 → 6.19.0; no broken requirements |
| 3 — existing behavior/gates | `make verify-backend-ci` and `make verify-frontend-ci` in the clean environment, supported Node 24.19.0 | Passed: 703 backend tests, 26 skips, 88.84% coverage; 256 frontend unit tests and nine browser smoke tests, contracts/lint/types/build/audits. Hosted CI uses Node 22 |
| 4 — independent review | Fresh-context reviewer against the implementation snapshot | No material findings; 53 independent PDF/upload tests passed. Report recorded in Linear PRI-65; subsequent edits only record owner authorization and this result |
| 5 — delivery | Hosted PR CI, review, merge and main CI | Pending; owner authorized commit/push on 2026-10-01. Merge/deployment not authorized |

Local Docker verification is blocked: two bounded daemon queries timed out,
including after opening Docker Desktop. No restart, volume deletion or daemon
configuration change was attempted. PostgreSQL/container gates must pass on the
updated revision in hosted CI; earlier main results are historical, not passes
for this dependency change.

Current audit outputs: `/tmp/pri65-backend-audit.json` and
`/tmp/pri65-frontend-audit.json`. Clean install: `/tmp/pri65-clean-install.log`.
Final application gates: `/tmp/pri65-backend-retry.log` and
`/tmp/pri65-frontend-ci.log`. The initial combined run
(`/tmp/pri65-verify-ci.log`) had one startup-subprocess failure (702 passed,
26 skipped); that exact configuration passed in isolation, then all 703 passed
on the complete backend rerun. No source/test adjustment was made. The precise
cause of the first failure was not established.

The two targeted pip-tools generation runs succeeded. A later optional
byte-repeatability check failed during a package download with `ENOSPC`
(`/tmp/pri65-lock-repro.log`); it did not change the lock, and is not recorded as
a pass. Approximately 700 MiB remained at diagnosis. The previous local Next.js
build's rebuildable cache was removed before the successful frontend gate. No
personal data or Docker volumes were removed. Inventory comparison confirms the
92-package lock changes only pypdf. Clean install and `pip check` passed.

### Compatibility, Review Scope And Recovery

The single canonical floor remains in requirements.in; CI and both backend
container builds consume requirements.lock. Inventory comparison and lock
regeneration guard against unrelated version drift; no abstraction, business
rule or API contract changes are introduced. Existing rendering tests check
visible content, page count and dimensions, fonts, contact links, export/re-upload
round trips, timeouts and invalid uploads. No new test that merely asserts a
literal dependency version is needed for this configuration repair.

Review correctness, dependency integrity, PDF compatibility, security/audit
coverage, error behavior, and diff hygiene. Authorization/privacy, transaction
concurrency, stored data, accessibility, telemetry and pricing implementations
are unchanged; their existing regression gates still apply. No performance or
memory improvement is claimed for the application from this upgrade.

Deployment requires rebuilding the backend image from the updated lock after
owner approval and green hosted checks. No migration or data transformation is
needed. Reverting the lock is technically possible but restores known findings;
prefer a forward fix if a compatibility regression appears. This task performs
no deployment or production mutation.

Source review date: 2026-10-01. Maintainer releases inspected:
[6.18.0](https://github.com/py-pdf/pypdf/releases/tag/6.18.0),
[6.18.1](https://github.com/py-pdf/pypdf/releases/tag/6.18.1), and
[6.19.0](https://github.com/py-pdf/pypdf/releases/tag/6.19.0).
The audit reports fix versions at or below 6.19.0 for all seven baseline
advisories. Audits establish current reported findings, not a permanent absence
of vulnerabilities. Refresh the complete dependency audit near release; do not
infer that a prior passing result establishes current advisory coverage.
