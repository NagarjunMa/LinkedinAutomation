# PrismPro repository guidance

This is a tracked entrypoint for contributors and coding agents. The old
LinkedIn/email-automation description is historical, not current architecture.

## Read before working

1. Read applicable `AGENTS.md` instructions when present.
2. Read [architecture routing](docs/architecture.md) and its approved Linear
   specifications; distinguish target designs from current code.
3. Read the current PrismPro Linear issue, acceptance criteria and decisions.
   Use only `linear_prismpro`; verify PrismPro workspace/project before writes.
4. Inspect branch/history/worktree and preserve unrelated edits.
5. Use the [documentation index](docs/README.md), [README](README.md) and
   [deployment runbook](docs/production-mvp-runbook.md), not legacy setup recipes.

## Development and verification

Use `engineering-loop` when available and follow the repository's standing
workflow. Establish scope, invariants, risk tier and acceptance tests first.
Use red-green-refactor for behavior changes; document structural-validation
exceptions for docs/configuration. Keep one coherent behavior per review.

Before completion, re-read acceptance criteria, inspect the entire merge-base
diff including uncommitted changes, review applicable correctness/security/
privacy/reliability/compatibility risks, and run relevant repository-native gates.
Fix material in-scope findings and rerun affected checks. Record exact results,
skipped/blocked checks, remaining risks and rollout/rollback in the verified issue.
Critical boundaries require an additional explicit review. Never mark a skipped
required gate as passed or initial implementation as complete.

The [Makefile](Makefile) and [CI workflow](.github/workflows/ci.yml) own commands;
do not bypass hooks, weaken thresholds or suppress errors to obtain a pass.
Production mutations and real-provider calls need appropriate authorization.

## Branches and delivery

Use `<type>/pri-<number>-<short-kebab-case-description>`: `feature`, `fix`,
`chore`, `security`, `refactor`, `test`, `docs` or `perf`. Verify the issue
number and branch-name collisions. For authorized work without an issue, omit
the issue segment rather than invent one.

Development is sequential: prior PR merged and CI green, local main updated,
merged local branch retired, then the next owner-approved task. Obtain owner
approval before commit/push. Never treat a plan as permission to merge or deploy.

## Non-negotiable boundaries

- No secrets, private resumes, transcripts or production records in Git or Linear.
- Backend-only privileged credentials; verify ownership even when database access bypasses RLS.
- Reviewed Alembic migrations only; no schema-bootstrap or revision-stamping workaround.
- Keep public preview and billing restrictions intact.
- Model output and uploaded documents are untrusted; tests do not certify factual grounding.
- No adjacent Career Evidence features or new integrations in a documentation task.
