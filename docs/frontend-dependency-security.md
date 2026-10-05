# PRI-66 — frontend dependency security

Current status: the remaining development dependency has been removed through a
scoped lint adapter. Both audits now pass; see **Remaining tooling remediation**
below for current evidence and review limits. Earlier audit sections are historical.

## Contract and scope

Owner authorized investigation and implementation on 2026-10-04. Base:
`dbebb1c830b0384f39d5d820fe7bdccb1c96e342` (`main`). Branch:
`security/pri-66-remove-braces-dependency`. The PRI-28 documentation commit
`5ac8762` remains on its separate branch.

Risk: **Significant**. Replacing the shared CSS compiler affects every frontend
route. Preserve design tokens, responsive layout, accessible focus, and resume
upload/evaluation/tailoring/preview behavior. No API, authentication, database,
deployment, or product redesign is included. Audits and their thresholds remain
unchanged. Full removal from the installed dependency graph is now locally verified;
independent review of the new tooling increment has passed; delivery gates remain pending.

## Findings and alternatives

Sources checked 2026-10-04:

- [braces advisory GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm):
  stack-exhaustion denial of service; no patched release listed. npm's latest
  `braces` is still 3.0.3. This does not establish a remotely reachable app exploit.
- [Tailwind migration guide](https://tailwindcss.com/docs/upgrade-guide), installed
  Next 16.3.8 CSS guide, and npm package metadata govern the integration changes.
- [tinyglobby](https://github.com/SuperchupuDev/tinyglobby) is a maintained glob
  alternative, but is not an interchangeable package alias for this consumer.

| Option | Evaluation |
| --- | --- |
| Update braces / Tailwind within v3 | No patched braces release; the dependency chain remains. |
| Migrate Tailwind to v4 | Selected for the production path. Removes Tailwind's chokidar/micromatch/braces chain using the supported PostCSS integration. |
| Move Tailwind to devDependencies | Changes audit filtering, not vulnerable code; rejected as a remediation. |
| Ignore the advisory / force an audit fix | Rejected. The audit recommends breaking dependency changes that need compatibility review. |
| Upgrade the remaining Next ESLint stack | Latest config/plugin remains 16.3.8 and depends on fast-glob 3.3.1 → micromatch 4.0.8 → braces 3.0.3. No compatible patched upstream release found. |
| Alias fast-glob to tinyglobby 0.2.17 | Rejected after a fixture comparison: literal directory patterns expand into descendants, absolute patterns return relative paths, and trailing-slash behavior differs. Next's root-directory resolver expects fast-glob semantics. |
| Downgrade eslint-config-next to 14.2.35 | npm suggests this for the development audit; rejected because it mismatches Next 16 and changes the lint contract. |
| Maintain a scoped glob adapter | Selected after owner authorized the remaining repair. Uses maintained glob 13.0.6 with explicit compatibility tests; creates a small local maintenance obligation, not an upstream fix. |

## Implementation and compatibility

- `frontend/package.json` and lock: pin Tailwind and `@tailwindcss/postcss` to
  4.3.3; remove unused autoprefixer and overrides whose dependency paths vanished.
  Remove the micromatch/picomatch override after replacing the remaining ESLint path.
- `frontend/postcss.config.mjs`: use the v4 plugin, which handles prefixing.
- `frontend/src/app/globals.css`: import v4, explicitly scan `src`, load the
  existing theme config, preserve button cursors and default placeholder color.
- `frontend/tailwind.config.mjs`: retain semantic/brand tokens, radius values,
  animation plugin and the old small-shadow/blur scales. Use an ESM plugin import.
- Components: mechanical `outline-none` → `outline-hidden` and
  `flex-shrink-0` → `shrink-0` substitutions; migrate removed opacity utilities
  to color alpha modifiers; convert CSS-variable shorthand to v4 parentheses.
  These low-line-count substitutions span many files;
  they are one compiler-compatibility change, not separate feature development.
- `frontend/tests/e2e/mvp-smoke.spec.ts`: exercise compiled colors, radii, border,
  shadow, blur, shrink behavior, normal/high-contrast focus and variable-driven
  dimensions/origins/chart colors alongside existing flows.

Tailwind 4 requires Safari 16.4+, Chrome 111+, Firefox 128+. Older browsers are not
covered. Native cascade layers, modern palette values and hover-capability media
queries are v4 behavior; this is not a claim of pixel identity on every route.
The existing design tokens remain canonical. Modern opacity modifiers also make
the declared alpha work with variable-based application colors.

## Evaluations and execution context

The audit itself is the red dependency regression: the baseline production audit
reported five high affected package entries for one underlying advisory.
Dependency/configuration changes are validated with lock/install/build/audit
checks rather than a test that merely asserts version strings.

Baseline: all nine existing MVP browser tests passed, and the added style
characterization passed on v3. During migration, the outline check failed.
Controls now use `outline-hidden`; the check verifies the actual accessibility
contract in forced-colors mode because v4 encodes the normal-mode outline
differently. All nine original flows and the focused new check subsequently passed.

| Criterion | Evidence/status |
| --- | --- |
| Resolve production audit without weakening it | Passed: `npm audit --omit=dev --audit-level=high --json`, zero findings. |
| Full installed dependency graph is clear | Passed after tooling remediation: full audit zero; no braces node remains. |
| Reproducible dependency installation | Passed: `npm ci`; lock unchanged by installation. |
| Frontend contracts/lint/types/build/unit/browser gates | Passed on the corrected final code: 256 unit tests, 10 browser tests, contracts/lint/types/build/production audit (`/tmp/pri66-frontend-ci-final.log`). |
| Public preview / production CSS / visual comparison | Passed after correction: eight public-preview browser tests and two production-mode CSS/CSP checks. Inspected desktop/mobile before/after resume screenshots: layout/content retained; expected opacity/preflight differences documented. |
| Fresh independent review | Round 1 found PRI66-R1. Round 2 independently compiled CSS and passed 16 Chromium assertions; PRI66-R1 resolved, no additional material findings. |
| Hosted Docker, PostgreSQL, secret scan, human review, merge and rollout | Not run for this uncommitted revision. |

Local logs: `/tmp/pri66-audit-before.json`, `/tmp/pri66-audit-production.json`,
`/tmp/pri66-audit-migration-full.json`, `/tmp/pri66-clean-install.log`,
`/tmp/pri66-baseline-browser.log`, `/tmp/pri66-style-baseline.log`,
`/tmp/pri66-style-final.log`, `/tmp/pri66-frontend-ci-final.log`,
`/tmp/pri66-preview-final.log`, `/tmp/pri66-production-browser-final.log`,
`/tmp/pri66-audit-final-full.json`. Full audit: 880 dependencies, five high
affected entries confined to the development ESLint chain.
They contain synthetic fixtures, not production verification.

### Review finding PRI66-R1

P2, confirmed, introduced by migration. V3 shorthand in shared calendar, select,
chart and popover/dropdown origin classes emitted invalid CSS under v4. A browser
regression reproduced expected 32px height becoming 0px. Migrated all consumers
and tested 32px height, 160px max-height, 10px/20px origin, and explicit chart
background/border colors. Red: `/tmp/pri66-variable-red.log`; green:
`/tmp/pri66-variable-green.log`. Normal focus ring also passed; the screenshot
ring difference was not established as a separate defect (animated transition).
Fresh-context reviewer used an isolated copy with 330 before/after hashes equal;
no cross-model claim. Round 2 confirmed the correction with 16 independent
Chromium assertions and no material findings. Its manifest SHA256 is
`0520a60846e9b3fbfa8e423937a94c6a8079fdd749d38c03ae05a78efc1ed4d4`.
Final documentation status updates follow that snapshot; reviewed application
source is unchanged. Parent checks used bundled Node 24.19.0; reviewer used
Node 24.16.0. Hosted Node 22/Linux checks remain pending.

Next incomplete step: complete Docker verification and hosted delivery gates. Keep the issue open until applicable hosted and owner release gates pass.

## Delivery and recovery

No data migration or API compatibility change. Commit/push/merge require owner
authorization. Hosted CI must exercise the Linux native Tailwind build dependencies
in both frontend and combined Docker images. After approval and deployment,
verify landing/login, both themes, narrow/wide dashboard layouts and resume preview
on the deployed revision. Actual Supabase OAuth is a rollout check, not established
by mocked browser tests.

Rollback the coherent compiler/config/class/lock change together and redeploy the
previous artifact. This restores the known production dependency advisory; it is
recovery from a rendering regression, not a security remediation.

Lesson: inspect both production and development graphs. A production audit can
be green while a second consumer still installs the same vulnerable package.

## Review coverage and limits

Reviewed compiler/plugin configuration, generated lock changes, mechanically
updated utility consumers, representative shared controls and Docker/CI wiring.
Normal and forced-color focus, responsive layout, theme colors and preview flows
have local browser evidence. No API/data contracts, concurrency, billing, storage
or database paths changed, so backend behavior/concurrency/migration tests were
not rerun for this frontend-only diff. No performance, cost or memory improvement
is claimed. Runtime and build behavior are supported by local checks; Linux
container behavior and real deployed auth remain release checks. Existing image
loading warnings are not introduced or suppressed by this migration.

## Final pre-merge audit — 2026-10-04

Reviewed the full committed/staged/unstaged scope and the new evidence document
against verified remote main and merge base
`dbebb1c830b0384f39d5d820fe7bdccb1c96e342`. There are no branch commits yet;
PRI-28 remains excluded on its own branch. Final risk remains Significant.
Snapshot manifest SHA256:
`48477f41055ecfc3381f3a7243e22e37c0dd2057b5131ee3b3900f421b81072e`.
All frontend hashes match the previous corrected review and current source.

- **Passed again:** `make verify-frontend-ci` on Node 24.19.0, with synthetic
  service settings and SQLite for offline contract export. 39 unit-test files /
  256 tests, 10 MVP browser tests, contracts, lint, types, production build and
  production dependency audit. Log: `/tmp/pri66-premerge-frontend.log`.
- **Passed:** fresh `npm audit --omit=dev --audit-level=high --json`, zero findings
  (`/tmp/pri66-verification-prod-audit.json`); `git diff --check`; package/lock
  root declarations match. The 41 changed TSX files contain only the reviewed
  utility transformations, with no application-logic changes.
- **Failed / unresolved:** fresh `npm audit --include=dev --json`, five high
  entries for the existing development ESLint dependency chain
  (`/tmp/pri66-verification-full-audit.json`). The official advisory still lists
  no patched braces release. No ignore, audit-threshold change or lint downgrade.
- **Retained evidence:** eight public-preview and two production-mode browser
  checks passed on exactly the same frontend source; not repeated without a
  source or dependency change. Clean-install and independent 16-assertion CSS
  correction evidence also remain applicable.
- **Blocked locally:** Docker daemon did not respond to a bounded 10-second
  `docker info` check. Linux native compiler entries and Node >=20 support were
  inspected; this does not substitute for Linux/Node22 container execution.
  The locally generated standalone artifact contains no braces package directory.
- **Not run:** hosted CI, PostgreSQL/migration/secret-scan jobs, human review,
  deployment and live OAuth/preview rollout. No backend behavior changed.
- **Independent final review:** fresh-context reviewer reported no material
  findings and independently passed 25 Chromium assertions on the snapshot.
  Covered semantic themes, dimensions, focus/forced-colors, responsive utilities,
  screen-reader hiding, gradients, popover colors and cascade-layer overrides.
  All 330 hashes matched before/after. PRI66-R1 remains resolved. No cross-model
  claim. Scratch evidence: `/tmp/pri66-review3-check/frontend/compile.cjs` and
  `browser.cjs`.

Criterion mapping: the production audit and local behavior/install criteria
pass; full dependency remediation remains incomplete; hosted/release approval
criteria remain pending. PRI-66 must stay In Progress. Rollout and rollback
requirements above still apply; no application change was needed during this
audit.


## Remaining tooling remediation — 2026-10-04

Owner requested all remaining fixes while investigating Docker. Risk stays
**Significant**: dependency installation, lint discovery and container build inputs
change. No runtime application logic, auth, API, schema, billing or production
access changes. Earlier browser evidence is historical after a dependency change.

### Design and maintenance

- `frontend/tools/next-root-glob` is a private package named
  `@prismpro/next-root-glob`, installed under the fast-glob import name with an npm
  override scoped to `@next/eslint-plugin-next`. The locked plugin's only use is
  `getRootDirs` with one string and `{ onlyDirectories: true }`.
- Wrap maintained **glob 13.0.6**; retain root spelling, absolute paths, brace and
  extglob matching, descendant-only terminal globstars and symlink directories.
  This deliberately supports that consumer, not the complete fast-glob API.
  Reject unsupported argument shapes/options, patterns longer than 4096 characters
  or nesting deeper than 64 before matching. Root settings are trusted repository
  configuration, not a public input API. These limits are not a sandbox or a total
  traversal budget for arbitrarily broad filesystem patterns.
- `tinyglobby` with corrected directory options was also tested. Its crawler omits
  a matched symlink directory itself, so it was rejected instead of adding a second
  filesystem crawler to compensate. glob passes the symlink fixture.
- No vendored braces implementation or falsified patched version. The replacement
  and its transitive dependencies remain visible to npm audit. `brace-expansion`
  is a different package and remains audited normally.
- The CommonJS adapter has a file-specific ESLint allowance for `node:` and `glob`
  requires because Next loads it synchronously. App lint rules remain unchanged;
  the adapter and its tests are now linted as well.
- Both Dockerfiles copy the local package before `npm ci`; it uses relative paths.
  npm's old nested fast-glob lock record survived overrides in an isolated fixture.
  Removed only that obsolete seed record and regenerated with npm. No existing
  remaining package versions changed versus the reviewed Tailwind snapshot;
  npm additionally resolved optional WASM package placement.
- Both local `make audit-frontend` and hosted CI now run the complete development
  audit alongside the existing production audit, keeping the high threshold.
- Removal condition: when a compatible Next plugin no longer installs vulnerable
  braces, remove the adapter, direct file dependency and override together; retain
  root/rule compatibility evidence and rerun both audits and frontend gates.
  Upgrading Next requires checking its actual fast-glob calls against this contract.

Primary source checked 2026-10-04:
[glob API and symlink behavior](https://github.com/isaacs/node-glob), installed
Next ESLint 16.3.8 source, npm registry glob13.0.6 metadata, and
[npm overrides](https://docs.npmjs.com/cli/configuring-npm/package-json/).

### Evidence on the new state

Red: original fast-glob did not enforce the intended nesting/length boundary
(`/tmp/pri66-adapter-baseline.log`). Compatibility fixtures caught trailing-slash
expectation and symlink differences during implementation. No retroactive TDD
claim for the earlier completed Tailwind migration.

Passed:

- Canonical `npm ci`, coherent `npm ls --all`, no braces package in lock;
  installed lock equals the npm-generated isolated lock. Install log:
  `/tmp/pri66-final-ci-install.log`.
- `npm run test:lint-tooling`: 22 checks covering literal/relative/absolute,
  wildcard/recursive/brace/extglob, files/hidden/missing paths, root arrays,
  normalized Windows separators, symlinks, input limits and unsupported calls.
  Actual Next `no-html-link-for-pages` reports an internal link and accepts an
  external link, proving root discovery still feeds the rule.
- `make verify-frontend-ci`: contracts, adapter tests, lint, types, production
  build, 256 unit tests, 10 MVP browser tests, both audits zero. Bundled Node
  24.19.0, synthetic services, offline SQLite contract export.
  `/tmp/pri66-adapter-frontend-ci.log`.
- Fresh production/full JSON audits: zero findings at all severities.
  `/tmp/pri66-adapter-{prod,full}-audit.json`.
- Production browser: 2 CSS/focus/theme and nonce-CSP/hydration checks passed.
  `/tmp/pri66-adapter-production-browser.log`.

Passed: eight public-preview browser tests on the new state
(`/tmp/pri66-adapter-preview.log`). `git diff --check` also passes.

Fresh independent review for this tooling increment passed on the owner's renewed
verification request; see the renewed review below. The earlier three migration
reviews are separate historical evidence. User is investigating Docker; hosted Linux/Node22 images,
PostgreSQL, secret scan, human review, merge and deployed verification remain
unproven. No commit, push, merge or deployment performed.

Rollback the lint adapter/manifests/lock and Docker copy wiring together if root
checking fails; restoring the old lint graph also restores the development
advisory. The compiler rollback described above is separate and restores the
production advisory. No data migration required.

The accidental parent-folder npm install is outside this Git diff. Recovery needs
a pre-change parent lockfile; no adjacent backup or local Time Machine snapshot
was found. A backup was requested; no speculative overwrite was made.


## Renewed final verification — 2026-10-04

Owner renewed the verification request after the additional-round approval request,
authorizing one fresh review beyond the three earlier migration rounds. Reviewed
uncommitted state against freshly verified remote main/merge base/HEAD
`dbebb1c830b0384f39d5d820fe7bdccb1c96e342`. No staged or branch commits; PRI-28
and the parent-folder installation remain excluded. Risk: **Significant**.

Fresh-context Codex reviewer `/root/pri66_adapter_final_review` reported
**no material findings**. Exact model is unavailable; no cross-model claim.
Isolated source, no source mutations, no recursive review. All 779 reviewed hashes
match before/after; manifest SHA256
`780ac54d8032e3c899a711849254f81207a2003c0a56be590f62fdf32cb563c0`.
Only this evidence-document status update follows the reviewed snapshot.

Independent checks passed: offline clean installs with npm11 and npm10.9.9 on
Node24.19.0/macOS; lock unchanged; `npm ls --all` for both; all 22 adapter/actual
Next Pages Router rule tests on both installations; focused ESLint; eight extra
root patterns compared with exact Next16.3.8/fast-glob3.3.1 baseline (terminal
slash, ./ wildcard, numeric braces, character class, nested paths, broken symlink,
brace-contained globstars, top-level alternatives).

An exploratory App Router lint assertion failed: `/profile` was not reported by
Next's rule. Exact original dependency baseline reproduced it; unchanged Next URL
code generates `/^\/profile$/` while normalizing the href to `/profile/`.
This is an evidenced pre-existing upstream limitation, not an introduced regression.
No valid repository check was weakened, and broader lint behavior was not changed.
Report and retained failure/baseline evidence:
`/tmp/pri66-renewed-review/review.md`, `independent.log`,
`independent-baseline.log`, `independent-final.log`, `npm10-ci.log`.

The entire current source matched the prior native-gate snapshot exactly.
Retained valid evidence: contracts/lint/types/build, 256 unit tests, 22 tooling
checks, 10 MVP + 8 preview + 2 production CSS/CSP browser tests. These were not
unnecessarily rerun. A new registry audit (`npm audit --include=dev --json`)
again returned zero at every severity (`/tmp/pri66-renewed-audit.json`). Package
and lock declarations agree, no braces package remains, and `git diff --check`
passes. Prior PRI66-R1 remains resolved.

Acceptance mapping: advisory removal, reproducible dependency graph, local
behavior/native gates and independent review pass. Docker/Linux Node22,
hosted CI including PostgreSQL/migrations/secret scan, owner delivery approval,
merge and rollout remain pending. No production, database, auth, concurrency,
idempotency or data-integrity behavior changed; those suites were not rerun.
No performance/cost/memory benefit is claimed. Accessibility evidence is
representative browser checks, not exhaustive certification. Rollout/browser
support and rollback requirements above remain applicable.

Verdict: **verified locally, not released**. Keep PRI-66 In Progress. No commit,
push, merge or deployment occurred. Parent-folder recovery still needs its
pre-change lockfile and is not resolved by this repository review.
