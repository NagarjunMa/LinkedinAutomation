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
