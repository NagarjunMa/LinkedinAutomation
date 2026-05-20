# Production Blockers

These issues were flagged in the Phase-1 code review and **must be resolved before any production deployment**. They are out of scope for the current fix pass but are documented here so they are not forgotten.

---

## CRITICAL

### Issue 3 — Local-disk resume upload (ephemeral Railway FS)

**File:** `backend/app/api/v1/endpoints/resumes_v2.py` — `UPLOAD_DIR`

**Problem:** Uploaded resume files are written to a local directory on the server filesystem (`uploads/resumes/`). Railway uses an ephemeral filesystem that is wiped on every redeploy. Any `FileNotFoundError` on the ATS simulation path (`doc_row.file_path`) will cause the evaluate endpoint to crash after a redeploy.

**Required fix:** Migrate file storage to Supabase Storage (or equivalent persistent object store). Store the Supabase Storage path in `ResumeDocument.file_path` and fetch the file via the Supabase client at evaluation time. Spec §6 explicitly calls this out as required.

---

## IMPORTANT

### Issue 7 — Credit ledger `with_for_update` locks wrong row

**File:** `backend/app/middleware/credits.py` (or equivalent ledger module)

**Problem:** The `with_for_update()` call acquires a row-level lock on an arbitrary row rather than specifically locking the target user's row. Under concurrent requests for the same user, this can lead to a race condition where two requests both see sufficient balance and both debit, resulting in a negative balance.

**Required fix:** Replace the current query with `select(User).where(User.user_id == user_id).with_for_update()` once production Postgres integration testing is available. Validate under concurrent load before deploy.

---

### Issue 6 — Retry inconsistency (partially addressed)

**Status:** The current fix pass (Issue 9) added correct transient-error retry to `evaluator.py`, `extractor.py`, and `tailor.py`. The `rewriter.py` service was not in scope for this pass and still uses the old retry configuration (or none).

**Required fix:** Apply the same `retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError))` pattern to `backend/app/services/resume/rewriter.py` before launch.

---

### Issue 8 — Dead code files to remove

The following files are unused and should be deleted in a follow-up clean-up pass to reduce maintenance burden and avoid confusion:

- `backend/app/schemas/activity.py`
- `backend/app/schemas/analytics.py`
- `backend/app/schemas/export.py`
- `backend/app/utils/email_helpers.py`
- `backend/app/core/config_old.py`
- `backend/migrations/add_apollo_contact_models.py`
- `backend/migrations/cleanup_unused_tables.py`
- `backend/app/services/orchestrator_manager.py`

---

### Issue 10 — `schemas/resume.py` is too large

**File:** `backend/app/schemas/resume.py`

**Problem:** This single file mixes legacy resume schemas (used by the old endpoints) and the new Phase-1 schemas (`ResumeDocumentJSON`, `EvaluationReport`, etc.), making it hard to maintain and increasing the risk of accidental coupling.

**Required fix:** Split into `schemas/resume_legacy.py` (legacy models) and `schemas/resume_v2.py` (Phase-1 models) in a dedicated refactor branch. Update all import sites accordingly.

---

### Issue 11 — Tailor bullet_lookup misses project bullets

**File:** `backend/app/services/jd/tailor.py`

**Problem:** The `bullet_lookup` dict in `tailor_resume_to_jd` only iterates over `doc.experience` bullets. If the LLM proposes a rewrite for a bullet that lives in `doc.projects`, the lookup will fall back to `diff.old`, bypassing the hallucination guard against the actual original text.

**Required fix:** Include project bullets in the lookup:
```python
bullet_lookup = {
    b.id: b.text
    for exp in doc.experience
    for b in exp.bullets
}
bullet_lookup.update({
    b.id: b.text
    for proj in (doc.projects or [])
    for b in (proj.bullets or [])
})
```

---

## MINOR (Issues 13–22)

See the original code review for the full list. These are low-priority polish items (naming, docstrings, logging improvements, etc.) and do not block a safe production launch on their own. Address them in a follow-up pass before the feature is generally available.

---

## Phase 2 — Issues raised by final review (2026-05-20)

### Issue P2-1 — JWT signature verification disabled (pre-existing, elevated by Phase 2)

**File:** `backend/app/core/auth.py:31`

`jwt.decode(..., options={"verify_signature": False})` accepts forged tokens. Pre-existing, but Phase 2 added `POST /api/v1/exports` which debits credits and writes to Supabase Storage keyed by `user_id`. An attacker crafting a JWT with any `sub` claim can impersonate any user.

**Required fix:** Switch to verified decode using `settings.SUPABASE_JWT_SECRET` (HS256). Tests need to mint properly signed JWTs.

### Issue P2-2 — Per-thread Chromium accumulates without cleanup

**File:** `backend/app/services/pdf/renderer.py:38-49`

`threading.local()` stores a `Browser` + `Playwright` per thread. FastAPI's default executor has up to 12 worker threads on common hardware; under sustained concurrent exports, every thread leaks a ~150 MB headless Chromium with no `atexit` cleanup.

**Required fix:** (1) Register an `atexit` hook iterating all known browsers and calling `browser.close()` + `pw.stop()`. (2) Install a bounded `ThreadPoolExecutor` (e.g. 2–4 workers) for PDF renders, or wrap the renderer call in an `asyncio.Semaphore`.

### Issue P2-3 — `timed_out` audit row persistence is implicit

**File:** `backend/app/api/v1/endpoints/exports.py:66-78`, `backend/app/middleware/credits.py:56-64`

The `ResumeExport(status="timed_out")` row is staged before `raise HTTPException(500)`, and the `credit_transaction` exit path's `db.commit()` incidentally flushes it. If the refund itself errors and the middleware calls `db.rollback()`, the audit row vanishes silently along with the credit refund.

**Required fix:** Commit the audit row in a separate transaction before raising, or document the contract explicitly. Add a test asserting the `timed_out` row exists after a render timeout.

### Issue P2-4 — `ResumeExport.render_ms` column never populated

**File:** `backend/app/models/resume_export.py:17`

Column exists in model + migration + SQLite test schema. Endpoint never writes it. Source of truth for render latency is the structured `pdf_render` log only.

**Required fix:** Change `render_pdf_from_doc` to return `(pdf_bytes, render_ms)` (or a small dataclass) and persist `render_ms` on the `ResumeExport` row. Alternative: drop the column.

### Issue P2-5 — No per-endpoint concurrency cap

**File:** `backend/app/api/v1/endpoints/exports.py`

Credit gate limits spend, not concurrency. A single user with credits can fan out N parallel exports; combined with Issue P2-2, this saturates threads + memory before any render returns.

**Required fix:** Module-level `asyncio.Semaphore(N)` around the `run_in_executor` call (N tuned to host memory headroom). Return `HTTP 429` on acquisition timeout.

### Issue P2-6 — CSS loaded via `file://` URIs is path-sensitive in container builds

**File:** `backend/app/services/pdf/template_engine.py:31-32`

`_shared_css_url()` resolves paths at module import time from `__file__`. Container builds that `COPY` source files to a different layout can produce unstyled PDFs (Chromium silently skips unreachable stylesheets). Smoke test asserts `>2000 bytes` which passes even for fully unstyled output.

**Required fix:** Inline the CSS into each template via `{% include 'shared/_base.css' %}` (raw block), or have the renderer set `page.set_content(html, base_url=...)` to a working file:// root. Add a test that confirms a known CSS rule is present in the rendered output.
