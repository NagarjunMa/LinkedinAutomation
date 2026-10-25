# PRI-67: frontend dependency remediation

Date: 2026-10-25. Canonical plan, acceptance criteria, current verification results,
review findings and delivery status: [PRI-67](https://linear.app/prismpro/issue/PRI-67/patch-october-frontend-dependency-advisories-without-weakening).
Documentation mode: full, using the Linear change contract and this technical record.

## Scope and source

Target: `main`, base/merge base `d0c223db993dbbfc2276d54704ddf78e5648dd6e`.
Branch: `security/pri-67-frontend-dependency-advisories`.
This changes frontend dependency families and the minimum Zod compatibility code.
The local image smoke also identified a hostname/probe mismatch; include the
frontend image bind setting and a CI container-health regression gate in this slice.
Backend dependencies, rate limiting, production configuration, deployment and new
product capabilities remain separate work. No API or database migration is needed.

| Dependency | Previous lock | Updated lock |
| --- | --- | --- |
| Next.js / eslint-config-next | 16.3.8 | 16.4.3 |
| sharp | 0.35.4 | 0.35.5 |
| Zod | 3.25.76 | 4.6.7 |
| happy-dom | 20.9.0 | 21.0.4 |
| Vitest / coverage-v8 | 5.0.0 | 5.0.5 |
| Vite | 7.3.6 | 7.3.7 |
| source-map-js | 1.2.1 | 1.2.2 |
| Undici | 7.29.1 | 7.30.1 |

Use Node 22 (validated locally with 22.23.4). Vitest requires at least 22.12.0
on the Node 22 line. Preserve the existing root-glob adapter and npm override;
its tests continue to enforce the supported ESLint consumer boundary.

## Behavior and regression contract

Generated backend transport types remain unchanged. Both response parsers retain
runtime validation, status checks, generated output-type checks and private generic
errors without original response data or validation causes. Defaults, nulls and
optional fields continue to match existing renderers. Form field errors, salary
cross-field rules, skill limits and education date coercion remain covered.

Zod 4 returns `.default()` values directly. The existing omitted-skills regression
test failed after the dependency upgrade because `{}` bypassed child defaults.
Use `.prefault({})` at that boundary so the existing `{ hard: [], soft: [] }`
output is preserved. Zod 4's `ZodType<Output>` retains unknown input by default;
removing the obsolete `ZodTypeDef` generic does not remove runtime validation.
Form error paths now accept `PropertyKey` and stringify keys before joining.

The image-health regression check failed against the first rebuilt image: the
standalone server bound Docker's hostname and refused localhost connections.
Setting the runner bind address explicitly allows loopback connections. The CI
smoke then caught Alpine's `wget localhost` resolving IPv6 against an IPv4 listener;
use `127.0.0.1` explicitly in the probe as well. Node fetch's IPv4 fallback is not
evidence that BusyBox's actual probe works.
The Dockerfile was unchanged at the original base; without an old-image runtime
reproduction, this finding's origin remains unknown. It is fixed as a discovered
packaging requirement rather than attributed to the dependency update.

The dependency audit was the initial failing security gate. The focused validation
suite passed before upgrading, failed on omitted-skills normalization after the
upgrade, and passed after the compatibility correction. New profile tests are
characterization coverage, not a claim of retroactive TDD for existing behavior.

## Verification and risk

Final risk tier: **Critical**, because the update remediates web framework code
execution advisories and changes a validation dependency across private-data
boundaries. Advisory severity does not establish exploitability: the published SVG
image issue describes Linux/glibc, while the frontend image uses Alpine/musl.
No exploit is sent to a deployed service.

| Criterion / material failure | Required evidence |
| --- | --- |
| Vulnerable packages remain in either dependency tree | Clean `npm ci`; `npm audit --omit=dev --audit-level=high`; `npm audit --include=dev --audit-level=high`, both zero advisories |
| Manifest/lock drift, generated API drift or build incompatibility | `make verify-frontend-ci` under Node 22, including contract-tool tests, lint, TypeScript, webpack build, coverage and MVP Playwright smoke |
| Defaults/nulls change or malformed private payloads are accepted/disclosed | Resume/workflow response-contract tests plus profile validation tests; preserve generic API errors |
| Preview opens account routes or breaks consent/PII-safe analytics | `PRISM_PRO_PUBLIC_PREVIEW_ONLY=true` landing-page Chromium suite with mocked waitlist/events |
| Production CSS, focus treatment or nonce CSP fails | Production build served locally; existing compiled-theme and nonce-CSP browser tests, then public-preview landing suite |
| Native packaging or Linux dependency resolution breaks | Frontend and combined Docker builds; hosted CI remains a separate gate |
| Standalone server starts but its health probe fails | CI `Frontend image health smoke` requires Docker health status `healthy`; the runner binds `HOSTNAME=0.0.0.0` and probes IPv4 loopback `127.0.0.1` |
| A material regression escapes implementation self-review | Fresh-context independent review of the complete dirty-source snapshot; owner review before delivery |

Correctness/architecture: retain the existing parser responsibilities and generated
contracts. Security/privacy/data integrity: retain validation, response redaction,
preview lockdown and CSP; no new data collection or storage path. Reliability and
compatibility: clean installation, builds and browser flows validate the affected
runtime boundaries. Performance/memory/cost: no new requests, loops, retained state,
workers or paid operations; no claim of measured improvement. Accessibility:
existing focus, forced-colors, mobile and reduced-motion checks remain gates.
The image bind/probe settings permit loopback health checks while retaining
the same exposed port and non-root runtime user. The CI smoke uses synthetic build
configuration and preview lockdown, publishes no ports, bounds its wait, and cleans
up its own container on success or failure.
Concurrency/idempotency, database recovery and migration behavior have no changed
implementation in this slice. Existing repository-wide audit findings remain open.

## Rollout and rollback

Require independent and owner review, then a separately authorized commit/PR.
Hosted frontend/backend checks, secret scanning and applicable image checks must
be assessed on that revision; earlier main CI is historical evidence only. Keep
PRI-67 open while required gates are pending. Deploy only with separate authority,
retain preview restrictions, and smoke the deployed landing/CSP before accepting
traffic. This patch does not complete PRI-28's production verification.

Rollback dependency manifest, lockfile and Zod compatibility changes together,
preferably by restoring the prior known image. That image restores known advisory
exposure, so it is only a temporary recovery option pending a corrected image.

## Primary references

Accessed 2026-10-25:

- [Next.js 16.4.3 release](https://github.com/vercel/next.js/releases/tag/v16.4.3)
- [Next.js SVG image advisory](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw)
- [Zod 4 migration guide](https://zod.dev/v4/changelog)
- [happy-dom advisory](https://github.com/capricorn86/happy-dom/security/advisories/GHSA-834v-8h66-3h79)
- [Vitest advisory](https://github.com/vitest-dev/vitest/security/advisories/GHSA-qxg6-89mg-rqv8)
