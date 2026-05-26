# Comprehensive Test Coverage — Design Spec

**Date:** 2026-05-26
**Author:** brainstorming session (Claude + nagarjun)
**Status:** approved, ready for implementation plan

---

## Goal

Prevent regressions in Prism Pro core code while shedding dead modules. Achieve via tiered coverage gates enforced in CI + a pre-push hook, delivered in three sequential phases.

## Non-goals

- 100% coverage on demoted job-tracking endpoints (`jobs.py`, `profiles.py`, etc.)
- Mutation testing (`mutmut`) — out of scope until coverage gaps close
- Behavior-only testing without numeric thresholds
- e2e Playwright expansion (existing 25-test suite kept as-is)

## Success criteria

- Backend critical paths ≥95% line coverage
- Backend schemas/models/utilities ≥90%
- Frontend hooks + Prism Pro components ≥80%
- CI fails on coverage drop below tier thresholds
- Pre-push hook runs `pytest -x` + `vitest run src/` (no coverage check locally — speed)
- ~1100 LOC of truly dead code deleted

---

## Tiered coverage thresholds

### Critical paths — ≥95%

```
backend/app/api/v1/endpoints/{exports,jd,resumes_v2,credits,analytics,webhooks,admin_metrics}.py
backend/app/services/credits/
backend/app/services/resume/         (parser, evaluator, rewriter, ats_simulator, hallucination_guard)
backend/app/services/jd/             (extractor, tailor)
backend/app/services/pdf/            (renderer, template_engine)
backend/app/services/storage/        (supabase_storage, exceptions)
backend/app/services/payments/       (stripe_webhook_handler)
backend/app/core/auth.py             (_ensure_user_row, get_current_user_id, get_current_user_email, JWKS)
backend/app/middleware/credits.py
```

### Standard paths — ≥90%

```
backend/app/schemas/{jd,resume_v2,resume_export}.py
backend/app/models/{credit_ledger,jd_evaluation,resume_document,resume_evaluation_v2,resume_export,user}.py
backend/app/core/{llm_logging,config,celery_app}.py
backend/app/utils/
```

### Frontend — ≥80%

```
frontend/src/hooks/                  (use-tailor-apply, use-export-pdf, use-resume, use-jd, use-credits)
frontend/src/app/lib/api/            (resumes, jd, exports, credits, types-v2)
frontend/src/components/tailor/      (preview-panel, diff-view)
frontend/src/components/resume/      (severity-coded bullet, rewrite modal, upload dropzone, analysis panel)
```

### Excluded from coverage gate (legacy/demoted live routes)

```
backend/app/api/v1/endpoints/{jobs,job_extraction,profiles,user_profiles,logs}.py
backend/app/services/{job_matcher,smart_job_scorer,url_job_extractor,supabase_cache_service,supabase_task_queue,resume_parser,profile_service,job_cleanup_service,job_scorer,ai_service}.py
backend/app/core/{rate_limiter,enhanced_logging,logging}.py
backend/app/middleware/security.py
backend/app/tasks/                   (Celery tasks — integration tested elsewhere)
backend/app/models/{job,profile,resume}.py     (legacy models)
backend/app/schemas/{job,profile}.py
```

---

## Dead code deletion

### Confirmed orphaned (no imports) — delete unconditionally

```
backend/app/services/consolidated_resume_evaluator.py     (115 LOC, multi-agent — rejected in Phase 0)
backend/app/schemas/resume_legacy.py                       (121 LOC, superseded by resume_v2)
backend/app/schemas/resume.py                              (2 LOC stub)
```

### Verify-then-delete (grep before remove)

```
backend/app/services/resume_parser.py                      (old parser — services/resume/parser.py is canonical)
backend/app/services/job_matcher.py                        (147 LOC, 0%)
backend/app/services/supabase_cache_service.py             (201 LOC, 0%)
backend/app/services/supabase_task_queue.py                (214 LOC, 0%)
```

### Process

1. `grep -r "from app.services.<module>" backend/` — zero hits → delete.
2. Run full pytest after each delete. Failure = something imported it indirectly → restore.
3. Total target: ~1100 LOC removed.

---

## Phase breakdown

### Phase 1 — Backend gap-fill (1-2 weeks)

1. Delete dead code per "Dead code deletion" section.
2. Backfill `core/auth.py` 35% → 95%:
   - `_ensure_user_row` happy path + IntegrityError race
   - `get_current_user_id` valid / expired / wrong audience / missing token
   - `get_current_user_email`
   - JWKS client cache, key rotation, fetch failure
3. Backfill `services/payments/stripe_webhook_handler.py` 79% → 95%:
   - All event types (`checkout.session.completed`, `payment_intent.succeeded`, refund, dispute)
   - Bad signature → 400
   - Idempotency via `external_ref` (replay = no double-grant)
4. Backfill `services/credits/ledger.py` 93% → 95%:
   - Concurrent debit on Postgres `SELECT FOR UPDATE`
   - Refund after debit
   - Insufficient balance → 402
5. `tasks/credit_tasks.py` 60% → 95%:
   - Monthly grant skips users with active paid subscription
   - Idempotency on re-run within same month
6. `.coveragerc` with exclude list + `pytest --cov-fail-under` per tier.
7. CI gate: backend coverage step fails build below threshold.

**Acceptance:** `core/auth.py` + `stripe_webhook_handler.py` + dead-code delete merged. `credit_tasks.py` Celery test deferable to Phase 3 if Phase 1 runs long.

### Phase 2 — Frontend foundation (1-2 weeks)

1. Install `@vitest/coverage-v8` + verify Linux CI runner compatibility.
2. Add scripts to `package.json`:
   - `"test": "vitest run src/"`
   - `"test:coverage": "vitest run src/ --coverage"`
3. Test hooks (each: success, error, loading, cache invalidation):
   - `use-tailor-apply`, `use-export-pdf`, `use-resume`, `use-jd-analyze`, `use-credits-balance`
4. Test API client modules (each: request shape, response parse, 4xx/5xx, network error) via `msw`:
   - `lib/api/resumes`, `lib/api/jd`, `lib/api/exports`, `lib/api/credits`
5. Test Prism Pro components:
   - `DiffView` — per-change accept, summary update, skills reorder
   - `SeverityBulletRenderer` — Strong/Weak/Vague color coding
   - `RewriteModal` — placeholder rendering, accept flow
   - `ResumeUploadDropzone` — file validation, progress
   - `ResumeAnalysisPanel` — section rendering
6. CI gate: frontend coverage step added.

### Phase 3 — Pre-push hook + threshold ratchet (3-5 days)

1. Install `lefthook` (preferred over `husky` — Go-based, zero npm overhead).
2. `lefthook.yml` pre-push hook:
   - `cd backend && pytest -x -q`
   - `cd frontend && npm run test`
3. Ratchet CI thresholds:
   - Week 1: gate at current floor
   - Week 2: raise to tier minimums (95/90/80)
   - Week 3: declare baseline; future PRs cannot drop coverage on touched files
4. Add coverage badge to README (Codecov or shields.io static).

---

## Tooling stack

### Backend

- `pytest` (already)
- `pytest-cov` (installed)
- `pytest-asyncio` (already)
- `respx` for HTTP mocks (already — OpenAI/Supabase)
- `freezegun` for time-based tests (monthly grant) — to add
- `factory_boy` for fixture factories (User, ResumeDocument, JDEvaluation) — to add

### Frontend

- `vitest` (already configured at `frontend/vitest.config.ts`)
- `@vitest/coverage-v8` — to install
- `@testing-library/react` + `@testing-library/jest-dom` (already)
- `@testing-library/user-event` (already)
- `msw` (Mock Service Worker) — to install. Realistic HTTP-level mocks, replaces hand-rolled fetch mocks.
- `happy-dom` (already, vitest env)

### Coverage config

- `backend/.coveragerc` — `[run] omit` list per "Excluded" section; `[report] fail_under` per-tier via `pytest --cov-fail-under` (tiered = run pytest twice, once per tier scope).
- `frontend/vitest.config.ts` — add `coverage.thresholds` block.

### Pre-push hook

- `lefthook` over `husky` — single binary, faster, no npm overhead.
- `lefthook.yml` at repo root.

### CI

- Extend `.github/workflows/ci.yml`:
  - Backend job: `pytest --cov=app --cov-report=xml --cov-fail-under=<tier>`
  - Frontend job: `npm run test:coverage`
  - Both upload `coverage.xml` artifact for visibility.
- Keep existing ruff/tsc `continue-on-error` (TECH_DEBT items).

---

## Testing conventions

### Backend layout

```
tests/
  api/v1/           # endpoint integration (FastAPI TestClient + SQLite override)
  services/         # pure unit tests (mock external IO)
    resume/
    jd/
    pdf/
    credits/
    payments/
    storage/
  schemas/          # Pydantic validation tests
  integration/      # multi-component E2E (real DB transactions)
  conftest.py       # shared fixtures: db_session, test_user_id, mock_openai, mock_supabase
```

### Backend patterns

- One file per source module: `app/services/jd/tailor.py` → `tests/services/jd/test_tailor.py`
- Per function: happy + 2-3 error/edge cases. Focus on branch coverage, not exhaustive cases.
- LLM calls: `respx` mocks OpenAI HTTP layer. Never call real API in tests.
- Supabase Storage: in-process stub via `monkeypatch`, no real bucket.
- Postgres-only tests: `@pytest.mark.postgres` marker, run in CI Postgres concurrency-sensitive paths step.
- Hallucination guard: optional property-based via `hypothesis` — generate random number-bearing strings, assert unprompted digits rejected. Defer if Phase 1 scope creeps.

### Frontend patterns

- One test file per component/hook/api module, colocated in `__tests__/` subdir (matches existing PreviewPanel layout).
- Hook tests: `renderHook` + `QueryClientProvider` wrapper. Assert query state transitions + cache invalidation.
- Component tests: render + `userEvent` interaction + assertion on DOM/aria roles.
- Snapshot tests forbidden — too brittle.
- API client tests: `msw` intercepts, return canned JSON, assert request shape + response parse.

### Naming

- Backend: `test_<function>_<scenario>` (e.g. `test_ensure_user_row_idempotent_on_integrity_error`)
- Frontend: `describe('useTailorApply')` + `it('invalidates resume-versions on success')`

---

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Coverage chasing instead of bug-catching | Code review rejects tests that call function + assert no error. Require explicit behavior assertions. |
| Pre-push hook bypassed with `--no-verify` | CI gate catches it. Hook is convenience, not trust boundary. |
| Frontend tests become snapshot soup | Snapshots forbidden in conventions. Use `getByRole`/`getByLabelText`. |
| Flaky LLM mocks drift from real API | Weekly nightly golden snapshots (`RUN_GOLDEN=1`) already in place. Catches drift. |
| Phase 1 takes 3 weeks not 1-2 | Phase 1 acceptance = `auth.py` + `stripe_webhook_handler.py` + dead-code delete. Defer `credit_tasks.py` if running long. |
| Postgres-only tests stay skipped in CI | TECH_DEBT tracks this. Phase 1 task: wire `-k postgres` to actually run. |
| `@vitest/coverage-v8` install breaks Linux CI | Install in Phase 2; verify on Linux runner before adding gate. |

---

## Critical files to modify

- `backend/.coveragerc` (new)
- `backend/pytest.ini` (extend `addopts` with coverage)
- `frontend/vitest.config.ts` (add coverage block)
- `frontend/package.json` (add test scripts + deps)
- `.github/workflows/ci.yml` (extend backend + frontend coverage steps)
- `lefthook.yml` (new, repo root)
- `TECH_DEBT.md` (mark resolved items)
- `progress.txt` (new phase block)

## Files to delete

- `backend/app/services/consolidated_resume_evaluator.py`
- `backend/app/schemas/resume_legacy.py`
- `backend/app/schemas/resume.py`
- `backend/app/services/resume_parser.py` (verify first)
- `backend/app/services/job_matcher.py` (verify first)
- `backend/app/services/supabase_cache_service.py` (verify first)
- `backend/app/services/supabase_task_queue.py` (verify first)

---

## Verification

After each phase:

1. **Phase 1:** `cd backend && pytest --cov=app --cov-report=term` — confirm critical-path files at ≥95%. CI build passes.
2. **Phase 2:** `cd frontend && npm run test:coverage` — confirm hooks/components at ≥80%. CI builds passes on Linux runner.
3. **Phase 3:** Pre-push hook fires on `git push` of a synthetic test failure — blocks push. `--no-verify` allows override. CI threshold ratchets confirmed in workflow logs.

End-to-end smoke after all phases:
- Touch a file under `services/resume/`, remove a test, push → CI fails.
- Restore test, push → CI passes.
- Verify coverage badge in README renders current value.
