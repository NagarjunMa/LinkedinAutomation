# PRI-5 Final Pre-Merge Audit

**Audit date:** 2026-09-07 UTC

**Issue:** PRI-5 — Build the public-preview landing page, secure waitlist, and access lockdown

**Branch:** `codex/pri-5-publishing-trailer`

**Audited code commit:** `de54bf60064286127933b02bc6d6aac6321fe678`

**Merge base (`origin/main`):** `1270e849e5021e50d5cf170389ed25b4c313e2cf`

**Final risk tier:** Critical

## Decision

**Do not mark PRI-5 complete or merge for production release yet.** The complete 69-file merge-base diff was reviewed, all locally executable code checks pass after the corrections below, and no unresolved material code finding remains. Production-only acceptance criteria are still unverified, and the currently deployed public services are not running this branch, so release approval remains blocked.

Critical risk is appropriate because this change introduces an unauthenticated, internet-facing PII intake path, changes authentication and product-route availability, adds a database migration and RLS boundary, and depends on coordinated production configuration.

## Acceptance-Criteria Assessment

### Satisfied in code and local verification

- The root route is the public landing page with a single waitlist conversion path; joining does not create an account.
- Duplicate waitlist submissions return a neutral, idempotent response.
- Product concepts are clearly marked as concepts and do not expose working product controls.
- Frontend login, onboarding, dashboard, and auth callbacks fail closed in public-preview mode.
- Backend product APIs fail closed in public-preview mode while health, waitlist, and allow-listed event collection remain reachable.
- Waitlist input is strictly validated, body-size constrained, honeypot protected, rate limited, deduplicated, and not logged.
- The waitlist table uses a unique email constraint, retention deadline, RLS, and explicit privilege revocation from public browser roles.
- The retention migration installs a daily `pg_cron` cleanup job when `pg_cron` is available, and the release verifier requires both the exact active schedule and a recorded successful run.
- CORS is configuration driven, and public responses use `no-store` where required.
- Production configuration fails closed unless both preview flags, the exact canonical HTTPS frontend origin, and a single backend process/replica are configured.
- A read-only-by-default release verifier checks deployed routes, CORS, Supabase Auth settings, migration revision, RLS, role revocation, and retention scheduling; its opt-in write smoke additionally checks body limits, duplicate neutrality, persistence, and rate limiting, then removes its generated record.
- Privacy and terms pages explain preview collection, retention, and user-request handling.
- Desktop/mobile layout, keyboard theme control, dark theme, and reduced-motion behavior are covered by end-to-end checks.

### Open production gates

- Configure both public-preview flags and the exact canonical HTTPS production frontend origin in the deployed environment.
- Disable Supabase public email signup and anonymous sign-in through the production project configuration.
- Apply the migration to production and verify RLS, browser-role revocation, the installed retention schedule, and at least one successful retention run.
- Run exactly one backend replica and one Uvicorn worker until rate limiting is distributed, then verify the trusted-proxy/client-IP path at production ingress.
- Validate the support access/export/deletion workflow against a controlled record before collecting production data.
- Run the full read-only and write production verifier, CI secret scanning, and production smoke tests.

## Findings Corrected During Audit

1. **Structured-data rendering:** Replaced `next/script` JSON-LD injection with the framework-recommended native script element, escaped `<` in serialized JSON, and added an end-to-end assertion that exactly one valid `SoftwareApplication` object is emitted.
2. **WCAG color contrast:** Raised low-opacity secondary landing-page text tokens. A post-fix axe scan reports zero violations in both light and dark themes with reduced-motion enabled.
3. **Interaction coverage:** Added end-to-end coverage for keyboard-operable theme selection, system dark theme, reduced motion, and structured metadata.
4. **Fail-closed production configuration:** Added exact-origin validation plus single-replica/single-worker enforcement for production preview deployments.
5. **Retention automation and evidence:** Added an idempotent `pg_cron` migration and a verifier that checks the schedule and successful execution history.
6. **Cross-browser hydration:** Kept server-rendered landing content stable until client hydration, delayed motion-preference adaptation until hydration, and prevented local HTTP WebKit runs from being upgraded to HTTPS.
7. **Backend preview boundary and health privacy:** Replaced product-path blocking with an explicit public-preview allow-list, blocking root, API documentation, OpenAPI, metrics, and all other backend surfaces. Production health responses are now minimal and non-cacheable, and the non-production dashboard smoke asserts that no hydration error occurs.

## Risk Review

| Area | Assessment |
| --- | --- |
| Correctness | Request validation, neutral duplicate semantics, route allow-listing, auth callback blocking, exact production configuration, and both migration upgrade/downgrade paths are covered. |
| Architecture | The public-preview policy is centralized on both frontend and backend. Operational flags must remain synchronized. |
| Security | Fail-closed defaults, body limits, validation, RLS, privilege revocation, CORS configuration, and production dependency audits pass. Multi-replica rate limiting remains an explicit rollout constraint. |
| Privacy | Email and optional profile context are purpose-limited with consent metadata and expiry timestamps. Retention scheduling is implemented; production execution history and the support workflow remain gates. |
| Reliability | Database uniqueness supplies cross-request idempotency. The in-memory limiter is intentionally limited to a single process until distributed enforcement exists. |
| Performance / memory | Landing assets build statically; request bodies and limiter state are bounded. No unbounded per-request payload or PII cache was found. |
| Cost | No paid external service or uncontrolled background workload was introduced. Retention cleanup is a small scheduled database task. |
| Compatibility | Node 22 production build, Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari, PostgreSQL migration rehearsal, and existing backend/frontend suites pass. Firefox system-color emulation is skipped because this local Playwright/macOS combination resets the emulated preference across navigation; manual dark-theme coverage passes in Firefox. |
| Regression | Product data, internal development surfaces, webhooks, documentation, OpenAPI, metrics, and health behavior were reviewed against the allow-list and covered by backend/frontend regression suites. The authenticated-dashboard hydration warning was corrected and the smoke test now fails if a page-level hydration error recurs. |

## Verification Evidence

### Passed

- `git diff --check`
- Complete diff review: 69 files, 3,893 additions, 1,219 deletions against the merge base, including this audit record
- Repository-native `make verify-ci` from a clean worktree at the audited commit — passed
- Backend: `pytest` from that clean worktree — 314 passed, 12 skipped, 86.70% coverage
- Backend: Ruff — passed
- Backend production dependencies: `pip-audit -r requirements.lock` — no known vulnerabilities
- Frontend: ESLint — passed with zero warnings
- Frontend: `tsc --noEmit` — passed after the production build regenerated Next types
- Frontend: Vitest coverage — 31 files / 117 tests passed; 87.30% statements, 75.67% branches, 78.94% functions
- Frontend production dependencies: `npm audit --omit=dev --audit-level=high` — zero vulnerabilities
- Frontend: Next.js 16.3 production build under repository CI runtime Node 22 — passed; 25 routes generated
- End-to-end public-preview landing page: Chromium, Firefox, WebKit, Mobile Chrome, and Mobile Safari — 39 passed, 1 Firefox environment-emulation test skipped
- End-to-end non-preview regression smoke: Chromium — 3 passed, including an assertion that no hydration error is emitted
- Accessibility: axe light/dark/reduced-motion audit — zero violations
- PostgreSQL: clean full upgrade through `2026_09_07_schedule_waitlist_retention`, RLS/role privilege assertions, downgrade to the prior revision, and re-upgrade — passed
- Release verifier: unit coverage for origin normalization and Supabase Auth configuration; deployed checks cover health cache policy and denial of root, docs, Redoc, OpenAPI, and metrics; missing-input execution fails cleanly without a traceback

### Live deployment probe — 2026-09-07 UTC

- `https://www.prismpro.live/` returns an older application build, and `/login` still returns `200`; the PRI-5 public-preview route lockdown is not deployed.
- `https://api.prismpro.live/health` returns `503` and the existing deployment exposes an internal database connection failure. The audited branch masks this detail and returns a minimal non-cacheable production response.
- `https://api.prismpro.live/docs` returns `200`; the audited branch blocks documentation and all non-allow-listed backend surfaces while public preview is enabled.
- The current public deployment must not be treated as the verified PRI-5 release or used to collect production waitlist data. Redeployment and both verifier modes remain mandatory.

### Skipped or blocked

- Twelve backend tests were skipped by the native suite: dormant Stripe paths and PostgreSQL-only concurrency cases not exercised by the default SQLite test run. The waitlist PostgreSQL migration and constraint behavior were checked separately against local PostgreSQL.
- Docker image builds were attempted but blocked because the installed local Docker engine did not respond.
- The Firefox system-color-preference emulation case was skipped because the local Playwright Firefox/macOS runtime resets `colorScheme` across navigation. Firefox dark-theme interaction and the remainder of the five-project matrix passed.
- TruffleHog is CI-only in this repository and was not installed locally. Manual diff inspection found no committed credential, and the configured CI secret-scan gate must pass before merge.
- The available Supabase CLI session exposes unrelated projects and this repository is not linked, so the production Auth setting, migration, scheduled-job history, and write smoke were not changed or asserted from this environment.
- GitHub CLI authentication is invalid. A signed-in browser session can access the repository, but no pull request exists for this branch, so PR-triggered hosted CI and its secret-scan result have not run.
- The available signed-in Supabase organization contains only unrelated projects, and the available Railway workspace contains no PrismPro service. No unrelated project was modified. Access to the PrismPro production Supabase and Railway workspaces is required to complete production configuration, ingress behavior, replica count, support deletion workflow, and deployed smoke checks.

## Rollout

1. Back up the production database and record the currently deployed application revisions.
2. Apply both additive waitlist migrations and verify RLS plus `PUBLIC`, `anon`, and `authenticated` privilege revocation, the exact daily retention schedule, and a successful job run.
3. Configure exact production CORS, synchronized frontend/backend public-preview flags, secrets, and one backend replica.
4. Disable Supabase public and anonymous signup before exposing the landing page.
5. Validate the support access/export/deletion runbook against a controlled record.
6. Deploy backend, then frontend; run `backend/scripts/verify_public_preview_release.py` read-only first and then with `--write-smoke` using dedicated verification credentials.
7. Monitor 4xx/5xx rates, waitlist insert failures, database saturation, and unexpected auth or product-route traffic without logging submitted PII.

## Rollback

1. Remove public traffic or return the static maintenance response, then redeploy the previously recorded frontend/backend revisions.
2. Keep the additive waitlist table in place by default so submitted consent records are not lost; stop new writes and preserve retention/deletion obligations.
3. Use the Alembic downgrade only if no waitlist records must be retained (or after an approved, encrypted export), because it drops the table.
4. Re-run health and access-denial smoke tests after rollback and document any data-handling follow-up.
