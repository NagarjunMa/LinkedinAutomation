# PRI-5 Final Pre-Merge Audit

**Audit date:** 2026-09-07 UTC

**Issue:** PRI-5 — Build the public-preview landing page, secure waitlist, and access lockdown

**Branch:** `codex/pri-5-publishing-trailer`

**Audited baseline:** `86b7996226e53898ea3c2197c5f25a1cb277967f`

**Merge base (`origin/main`):** `1270e849e5021e50d5cf170389ed25b4c313e2cf`

**Final risk tier:** Critical

## Decision

**Do not mark PRI-5 complete or merge for production release yet.** The complete 57-file merge-base diff was reviewed, all locally executable code checks pass after the corrections below, and no unresolved material code finding remains. Production-only acceptance criteria are still unverified and must be completed before release approval.

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
- CORS is configuration driven, and public responses use `no-store` where required.
- Privacy and terms pages explain preview collection, retention, and user-request handling.
- Desktop/mobile layout, keyboard theme control, dark theme, and reduced-motion behavior are covered by end-to-end checks.

### Open production gates

- Confirm both frontend and backend public-preview flags are enabled in the deployed environment.
- Disable Supabase public email signup and anonymous sign-in, then verify existing-user sign-in is unavailable through every public entry point.
- Apply the migration to production and run production waitlist, duplicate-submission, access-lockdown, auth-callback, health, and CORS smoke tests.
- Configure the exact production frontend origin; wildcard production CORS is not acceptable.
- Run one backend replica until rate limiting is moved to a distributed or edge-enforced store, then verify the trusted-proxy/client-IP path at the production ingress.
- Schedule `backend/scripts/purge_expired_waitlist.py` and verify the support process for access/deletion requests before collecting production data.

## Findings Corrected During Audit

1. **Structured-data rendering:** Replaced `next/script` JSON-LD injection with the framework-recommended native script element, escaped `<` in serialized JSON, and added an end-to-end assertion that exactly one valid `SoftwareApplication` object is emitted.
2. **WCAG color contrast:** Raised low-opacity secondary landing-page text tokens. A post-fix axe scan reports zero violations in both light and dark themes with reduced-motion enabled.
3. **Interaction coverage:** Added end-to-end coverage for keyboard-operable theme selection, system dark theme, reduced motion, and structured metadata.

## Risk Review

| Area | Assessment |
| --- | --- |
| Correctness | Request validation, neutral duplicate semantics, route allow-listing, auth callback blocking, and migration upgrade/downgrade paths are covered. |
| Architecture | The public-preview policy is centralized on both frontend and backend. Operational flags must remain synchronized. |
| Security | Fail-closed defaults, body limits, validation, RLS, privilege revocation, CORS configuration, and production dependency audits pass. Multi-replica rate limiting remains an explicit rollout constraint. |
| Privacy | Email and optional profile context are purpose-limited with consent metadata and expiry timestamps. The purge schedule and support workflow remain production gates. |
| Reliability | Database uniqueness supplies cross-request idempotency. The in-memory limiter is intentionally limited to a single process until distributed enforcement exists. |
| Performance / memory | Landing assets build statically; request bodies and limiter state are bounded. No unbounded per-request payload or PII cache was found. |
| Cost | No paid external service or uncontrolled background workload was introduced. Retention cleanup is a small scheduled database task. |
| Compatibility | Node 22 production build, Chromium desktop/mobile flows, PostgreSQL migration rehearsal, and existing backend/frontend suites pass. Firefox and WebKit were not locally installed. |
| Regression | Product data, internal development surfaces, webhooks, and health behavior were reviewed against the allow-list and covered by backend/frontend regression suites. |

## Verification Evidence

### Passed

- `git diff --check`
- Complete diff review: 57 files, 2,741 additions, 1,165 deletions against the merge base
- Backend: `pytest` — 295 passed, 12 skipped, 86.10% coverage
- Backend: Ruff — passed
- Backend production dependencies: `pip-audit -r requirements.lock` — no known vulnerabilities
- Frontend: ESLint — passed with zero warnings
- Frontend: `tsc --noEmit` — passed after the production build regenerated Next types
- Frontend: Vitest coverage — 31 files / 117 tests passed; 87.30% statements, 75.67% branches, 78.94% functions
- Frontend production dependencies: `npm audit --omit=dev --audit-level=high` — zero vulnerabilities
- Frontend: Next.js 16.3 production build under repository CI runtime Node 22 — passed; 25 routes generated
- End-to-end public-preview landing page: Chromium + Mobile Chrome — 14 passed
- End-to-end non-preview regression smoke: Chromium — 3 passed
- Accessibility: axe light/dark/reduced-motion audit — zero violations
- PostgreSQL: clean full upgrade, RLS/role privilege assertions, and downgrade to `c4e7a2f91b30` — passed

### Skipped or blocked

- Twelve backend tests were skipped by the native suite: dormant Stripe paths and PostgreSQL-only concurrency cases not exercised by the default SQLite test run. The waitlist PostgreSQL migration and constraint behavior were checked separately against local PostgreSQL.
- Docker image builds were attempted but blocked because the local Docker engine did not respond.
- Firefox, WebKit, and Mobile Safari Playwright projects were not run because those browser binaries are not installed locally; CI should run the configured browser matrix if available.
- TruffleHog is CI-only in this repository and was not installed locally. Manual diff inspection found no committed credential, and the configured CI secret-scan gate must pass before merge.
- Production configuration and smoke checks cannot be completed from the local audit environment.

## Rollout

1. Back up the production database and record the currently deployed application revisions.
2. Apply the additive waitlist migration and verify RLS plus `PUBLIC`, `anon`, and `authenticated` privilege revocation.
3. Configure exact production CORS, synchronized frontend/backend public-preview flags, secrets, and one backend replica.
4. Disable Supabase public and anonymous signup before exposing the landing page.
5. Schedule retention cleanup and validate the support access/deletion runbook.
6. Deploy backend, then frontend; run health, waitlist, duplicate, rate-limit, CORS, auth-callback, and product-route denial smoke tests.
7. Monitor 4xx/5xx rates, waitlist insert failures, database saturation, and unexpected auth or product-route traffic without logging submitted PII.

## Rollback

1. Remove public traffic or return the static maintenance response, then redeploy the previously recorded frontend/backend revisions.
2. Keep the additive waitlist table in place by default so submitted consent records are not lost; stop new writes and preserve retention/deletion obligations.
3. Use the Alembic downgrade only if no waitlist records must be retained (or after an approved, encrypted export), because it drops the table.
4. Re-run health and access-denial smoke tests after rollback and document any data-handling follow-up.
