# Tech Debt

Permanent fixes deferred for later. Track items here; add date + brief note when adding. Move to BLOCKERS.md only if a deploy is gated on it.

---

## Backend

### Migrate `os.getenv` → `settings.X` for module-load env reads

**Added:** 2026-05-21
**Why:** Some files (e.g. `evaluator.py`, `rewriter.py`, `extractor.py`, `tailor.py`, `storage/supabase_storage.py`) read env via `os.getenv` at module-import time. Without `--env-file` or an explicit `load_dotenv()` call before app import, these return `None` and crash (e.g. OpenAI client refuses to init).
**Current workaround:** `load_dotenv()` is called at the top of `app/main.py`, populating `os.environ` from `.env` before any module imports. Works locally + on Railway (no-op when no `.env` file is present and platform env is injected).
**Permanent fix:** replace `os.getenv("X")` with `settings.X` everywhere, route all env access through `app.core.config.Settings`. Pydantic-settings is the single source of truth, gives type validation, fail-fast on missing required vars.
**Files to migrate:**
- `app/services/resume/evaluator.py:42` — `OPENAI_API_KEY`
- `app/services/resume/rewriter.py:~46` — `OPENAI_API_KEY`
- `app/services/jd/extractor.py:9` — `OPENAI_API_KEY`
- `app/services/jd/tailor.py:13` — `OPENAI_API_KEY`
- `app/services/storage/supabase_storage.py:14-17` — `SUPABASE_STORAGE_BUCKET`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `app/core/auth.py:23` — `SUPABASE_URL` (JWKS URL construction)

### Squash Alembic migration chain into single baseline

**Added:** 2026-05-21
**Why:** Migration history has tangled merge graph from accumulated branches across phases. On fresh DB, `alembic upgrade head` fails because `add_resume_status_locking` tries to `ALTER TABLE resumes` before `resumes` table is created. We bootstrapped this fresh Supabase project via `Base.metadata.create_all()` + `alembic stamp head`.
**Permanent fix:**
1. Delete all files in `backend/migrations/versions/*.py` (preserve `env.py` + `script.py.mako`)
2. Run `alembic revision --autogenerate -m "initial_schema_baseline"` against a fresh DB matching current models
3. Inspect generated baseline; confirm all 15 production tables created
4. Apply to each environment via `alembic stamp head` (so existing DBs adopt the new baseline)
5. Commit

### Remove `test_user_123` auth fallback

**Added:** 2026-05-21
**File:** `app/core/auth.py:get_authenticated_user_id`
**Why:** Returns hardcoded `"test_user_123"` when no credentials present. Security hole — anyone hitting a protected endpoint without auth gets treated as a real user.
**Fix:** Return 401 in all environments. Tests already bypass via FastAPI `dependency_overrides`, so the fallback is unnecessary.

### Drop `SUPABASE_JWT_SECRET` from `conftest.py` and `.env.example`

**Added:** 2026-05-21
**Why:** Backend migrated from HS256 (shared secret) to ES256 (JWKS-based) for Supabase JWT verification. `SUPABASE_JWT_SECRET` is no longer read by code. Conftest still does `os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret")` — dead config.
**Fix:** delete the setdefault line + remove from `.env.example` if present.

### Add `SQLALCHEMY_DATABASE_URI` to `.env.example`

**Added:** 2026-05-21
**Why:** New devs (and future you on fresh checkouts) need a template. Currently the var is required but undocumented.
**Fix:** add a commented sample to `backend/.env.example`:
```
# Direct Postgres connection (NOT pooled — needed for Alembic DDL)
# URL-encode special chars in password: @ → %40, # → %23, etc.
SQLALCHEMY_DATABASE_URI=postgresql://postgres:<PASSWORD>@db.<project-ref>.supabase.co:5432/postgres
```

### Standardize storage bucket name

**Added:** 2026-05-21
**Why:** Code defaults to `resumes` in some places (`services/storage/supabase_storage.py:14`), `resume-exports` in others (`config.py:132` default). We're using `resume` (singular) via env override. Inconsistent.
**Fix:** pick one canonical name (`resumes` likely), update every default, deprecate `SUPABASE_STORAGE_BUCKET` env override.

### Fix 10 PDF renderer test failures

**Added:** Phase 2 (pre-2026-05-21)
**Files:** `tests/services/pdf/test_renderer_perf.py`, `tests/services/pdf/test_templates_smoke.py`
**Why:** Phase 2 introduced async/sync Playwright threading and per-thread browser cache. Tests pass on Phase 2 dev machine, fail elsewhere (CI + local on different Mac). Documented in BLOCKERS.md §P2.
**Fix:** investigate Playwright threading model, fix conftest browser lifecycle, or rewrite using async Playwright API throughout.

---

## Frontend

### Fix 12 pre-existing TypeScript errors

**Added:** Phase 3 (pre-2026-05-21)
**Why:** `next.config.mjs` has `typescript.ignoreBuildErrors: true` masking errors that `tsc --noEmit` reports. CI workflow marks `tsc` step `continue-on-error: true` to unblock.
**Fix:** Resolve framer-motion variant type incompat, react-window v2 API change, motion.div type, dashboard-context state-type mismatch.

### Fix 9 `react-hooks/exhaustive-deps` warnings

**Added:** Phase 0 lint cleanup (pre-2026-05-21)
**Files:** `gmail-connection.tsx`, `job-cleanup-manager.tsx`, `profile-completion-banner.tsx`, `resume-analysis-panel.tsx`, `resume-evaluator.tsx`, `resume-upload.tsx`
**Fix:** add missing deps OR refactor hooks; case-by-case judgment.

### Gitignore `playwright-report/` and `test-results/`

**Added:** 2026-05-21
**Why:** These dirs are regenerated every test run and produce diff churn / accidental commits.
**Fix:** add to `frontend/.gitignore`:
```
playwright-report/
test-results/
```

### Re-enable gitleaks (or equivalent secret scanning) in CI

**Added:** 2026-05-21
**Why:** `gitleaks/gitleaks-action@v2` was removed from CI workflow because it required `GITLEAKS_LICENSE` for orgs and was blocking init.
**Fix:** either configure GITLEAKS_LICENSE, switch to gitleaks-action@v1 (license-free), or rely on GitHub native secret scanning (free for public repos via Settings → Security → Secret scanning).

---

## CI / DevOps

### Migration squash blocks fresh-DB CI integration tests

**Added:** 2026-05-21
**Why:** `alembic upgrade head` fails on a fresh DB due to broken migration chain (see backend item above). CI currently runs against SQLite which sidesteps this.
**Fix:** dependent on backend "Squash Alembic migration chain" item.

### Postgres concurrent-debit test is skipped in CI

**Added:** Phase 4
**Why:** Test requires real Postgres `SELECT FOR UPDATE` — skipped on SQLite. CI has a Postgres service but the test isn't wired to actually run there.
**Fix:** ensure the Postgres-only credit ledger test runs in the `Run tests (Postgres — concurrency-sensitive paths)` step. Currently the `-k "concurrent"` selector may not match.
