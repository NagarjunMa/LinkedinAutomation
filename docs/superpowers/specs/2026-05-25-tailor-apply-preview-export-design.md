# Tailor Apply → Preview → Export — Design Spec

**Date:** 2026-05-25
**Status:** Approved
**Author:** brainstorming session
**Scope:** Make the **Apply** button on `/dashboard/resume/tailor` actually do something. After Apply, show a side-panel preview of the tailored resume, let the user download a PDF (Phase 2 templates) with a JD-aware filename, and persist per-JD version history so future analytics work has data to query.

---

## 1. Problem Statement

The JD tailor flow produces an excellent diff plan and renders proposed changes in the UI. **Clicking Apply does nothing visible**: no version is saved, no logs are emitted, no PDF appears. Users see proposed changes but cannot act on them.

Beyond fixing the bug, we need to deliver real value at the Apply step: a tangible PDF the user can submit today, line-by-line copyable bullets for users who maintain their own resume tool, and a persistence layer that captures which JDs the user tailored for (so future analytics work has data to query).

## 2. Goals

- Apply button creates a versioned, JD-linked `ResumeVersion` row.
- After Apply, show a side-panel preview pane (rendered HTML, no Playwright needed for preview) of the tailored resume.
- One-click PDF download using existing Phase 2 templates, with country + role auto-picked from the JD analysis (user can override).
- PDF filename auto-formed from user's name + JD company name (auto-extracted from JD), editable before download.
- Persist `jd_evaluation_id` on `resume_versions` to enable per-JD analytics queries.
- Always tailor from the original uploaded resume (star pattern) — new JDs do not inherit edits from previous JDs.

## 3. Non-Goals

- Granular per-bullet accept-rate tracking (a future event-sourced phase).
- Multi-user collaboration or share-links to previews.
- Undo / version-rollback UI.
- New PDF templates beyond the six already shipped in Phase 2 (US / IN × SWE / DS / PM).
- "Tailor from latest version" branching semantics (rejected in Q6 — star pattern only).

## 4. Target User

Primary: experienced engineers (3–15 yr) tailoring a resume to a specific JD they intend to apply to today. Secondary: power users who copy bullets into their own LaTeX/Word source of truth — they can read the preview HTML and copy text directly, or use the diff view above the preview pane.

## 5. Decisions Locked

| Topic | Choice |
|---|---|
| Output | Line-by-line diff (existing UI) + PDF download + persistence for analytics |
| Company name in PDF filename | Auto-extracted from JD by LLM (editable before download) |
| PDF template source | Reuse Phase 2 templates (six); auto-pick from JD country + role; user can override |
| UX flow after Apply | Inline side-panel preview + Download PDF button |
| Persistence model | JD-linked versions (FK from `ResumeVersion` → `JDEvaluation`) |
| Re-tailor semantics | Always tailor from the original `ResumeDocument` (star pattern) |
| Architecture approach | Approach 1 — extend existing models, no new aggregate tables |

## 6. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ Next.js — /dashboard/resume/tailor                           │
│                                                              │
│  LEFT  RIGHT                                                 │
│  ──    ─────                                                 │
│  JD    Diff view (existing) ── Apply ──┐                     │
│  +     ▼                               │                     │
│  resume                                ▼                     │
│  picker  Preview pane (NEW)                                  │
│        ┌─────────────────────┐                               │
│        │ rendered resume HTML│ ← Download PDF (template     │
│        │ (matches Phase 2     │   picker dropdown)           │
│        │  template aesthetic) │                              │
│        └─────────────────────┘                               │
└──────────────────────────────────────────────────────────────┘
                │ HTTPS REST
┌───────────────▼──────────────────────────────────────────────┐
│ FastAPI                                                       │
│                                                               │
│ POST /api/v1/jd/{jd_eval_id}/apply  (NEW — 0 credits)        │
│   ├─ Validate ownership                                       │
│   ├─ Apply accepted change_set to original ResumeDocument    │
│   ├─ Insert ResumeVersion with jd_evaluation_id FK           │
│   ├─ Render preview HTML (Jinja2 → string, no PDF yet)       │
│   └─ Return { version_id, preview_html, suggested_template } │
│                                                               │
│ POST /api/v1/exports  (EXISTING Phase 2 — 1 credit)          │
│   ├─ Now accepts custom filename + reads template from       │
│   │   ResumeVersion when request omits it                    │
│   └─ Renders PDF via Playwright                              │
│                                                               │
│ GET /api/v1/analytics/jd-progress  (NEW — 0 credits)         │
│   └─ Joins jd_evaluations + resume_versions + resume_exports │
└───────────────┬──────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────┐
│ Postgres                                                      │
│  resume_versions                                              │
│    + jd_evaluation_id  (NEW FK, nullable, indexed)           │
│    + accepted_at        (NEW timestamp, nullable)            │
│    + template_id        (NEW string, nullable)               │
│  jd_evaluations                                               │
│    + diff_plan.company_name added to JD extraction JSON      │
└──────────────────────────────────────────────────────────────┘
```

## 7. Components

### 7.1 Migration

`backend/migrations/versions/2026_05_25_jd_linked_versions.py`:
- `ALTER TABLE resume_versions ADD COLUMN jd_evaluation_id VARCHAR NULL REFERENCES jd_evaluations(id)`
- `ALTER TABLE resume_versions ADD COLUMN accepted_at TIMESTAMPTZ NULL`
- `ALTER TABLE resume_versions ADD COLUMN template_id VARCHAR NULL`
- `CREATE INDEX ix_resume_versions_jd_evaluation_id ON resume_versions(jd_evaluation_id)`

All columns nullable — backward compatible with pre-existing rows.

### 7.2 Schema additions

`app/schemas/jd.py` — extend `JDExtraction`:
```python
company_name: Optional[str] = None
```

Update extractor prompt to require best-effort company extraction. Falls back to `null` for blind / recruiter posts.

`app/schemas/resume.py` — extend `ApplyTailorRequest` / `ApplyTailorResponse`:
```python
class ApplyTailorRequest(BaseModel):
    accepted_changes: List[ChangeItem]
    template_id: Optional[str] = None

class ApplyTailorResponse(BaseModel):
    version_id: str
    preview_html: str
    company_name: Optional[str]
    suggested_template: str
    filename_hint: str
    warning: Optional[str] = None
```

### 7.3 New endpoint: `POST /api/v1/jd/{jd_evaluation_id}/apply`

Credit cost: **0** (tailor analysis at 2 credits already paid).

Logic:
1. Load JDEvaluation; verify `user_id == current_user_id`.
2. Resolve base `ResumeDocument` via `JDEvaluation.resume_document_id` — **always original, not latest version**.
3. Apply `accepted_changes` via existing `apply_changes(base, changes)` helper.
4. Resolve template:
   - If `request.template_id` provided, use it.
   - Else: `f"{country_hint.lower()}-{primary_role_category.lower()}"` from JD extraction (e.g. `us-swe`, `in-pm`).
5. INSERT `resume_versions` row:
   - `id` = new uuid
   - `resume_document_id` = base doc id
   - `parent_version_id` = NULL (star pattern; not linear history)
   - `change_set` = serialized accepted_changes
   - `parsed_json` = merged result
   - `jd_evaluation_id` = path param
   - `accepted_at` = now()
   - `template_id` = resolved
6. Render preview HTML:
   - `preview_html = template_engine.render_html_only(parsed_json, template_id)`
   - On exception: log + return empty string + `warning="Preview unavailable"`.
7. Compute filename:
   - `first = slugify(parsed_json.contact.name.split()[0] or "user")`
   - `last = slugify(parsed_json.contact.name.split()[-1] or "")`
   - `company = slugify(jd.diff_plan.company_name or "resume")`
   - `filename_hint = f"{first}-{last}-{company}.pdf"` (collapse double dashes)
8. Return `ApplyTailorResponse`.

### 7.4 Extended endpoint: `POST /api/v1/exports`

Phase 2 endpoint, minor additions:
- Accept optional `filename` in request body; sanitize via `slugify` + reject path-traversal segments (`..`, `/`, `\`, control chars). If absent, use `<doc-id>.pdf`.
- Read `template_id` from `ResumeVersion` row when request omits it.
- Storage path: `<user_id>/exports/<version_id>_<filename>` (existing pattern).

Credit cost stays at **1**.

### 7.5 New analytics endpoint: `GET /api/v1/analytics/jd-progress`

Single SQL query joining `jd_evaluations`, `resume_versions`, `resume_exports`. Returns:
```json
{
  "user_id": "...",
  "jds": [
    {
      "jd_evaluation_id": "...",
      "jd_company": "Stripe",
      "tailored_at": "2026-05-23T...",
      "applies_count": 3,
      "exports_count": 1,
      "last_match_score": 82,
      "last_exported_at": "2026-05-25T..."
    }
  ],
  "totals": {
    "jds_tailored": 7,
    "versions_created": 12,
    "pdfs_exported": 5
  }
}
```

Credit cost: 0. Scoped to `current_user_id`; never accepts user_id from query.

### 7.6 PDF template engine

`app/services/pdf/template_engine.py` adds:
```python
def render_html_only(parsed_json: dict, template_id: str) -> str:
    """Render Jinja2 template to HTML string. No Playwright. Inline all CSS."""
```

CSS is inlined server-side (read `_base.css` + `_typography.css` content) so the `<iframe srcdoc>` renders identically to the final PDF without fetching external assets.

### 7.7 Frontend types

`frontend/src/lib/api/types.ts`:
```ts
export interface ApplyTailorRequest {
  accepted_changes: ChangeItem[];
  template_id?: string;
}
export interface ApplyTailorResponse {
  version_id: string;
  preview_html: string;
  company_name: string | null;
  suggested_template: string;
  filename_hint: string;
  warning?: string;
}
```

### 7.8 Frontend hooks

`frontend/src/hooks/use-tailor.ts`:
- `useApplyTailor(jdEvalId)` — POST `/api/v1/jd/{id}/apply`. On success: invalidate `['versions']`, `['credits-balance']`, `['jd-progress']`.
- `useExportPdf(versionId)` — POST `/api/v1/exports`. On success: trigger browser download via signed URL.

### 7.9 Frontend page changes

`frontend/src/app/dashboard/resume/tailor/page.tsx`:
- Two-column layout: existing diff view LEFT, new preview panel RIGHT (sticky, scroll-aware).
- After Apply: hydrate preview panel.

New component `frontend/src/components/tailor/preview-panel.tsx`:
- Sticky right column, full available height, scrollable.
- `<iframe srcdoc={previewHtml} sandbox="allow-same-origin">`
- Template dropdown (six options), pre-selected from `suggested_template`.
- Editable filename input, pre-filled with `filename_hint`.
- **Download PDF** button.

## 8. Data Flow

### 8.1 Apply → preview

1. User checks/unchecks proposed changes in DiffView.
2. User clicks Apply.
3. Frontend collects accepted `ChangeItem[]`.
4. `POST /api/v1/jd/{jd_evaluation_id}/apply` body `{ accepted_changes, template_id: null }`.
5. Backend per §7.3.
6. Frontend hydrates preview panel; invalidates relevant TanStack queries; toast "Applied N changes."

### 8.2 Download PDF

1. User clicks **Download PDF**.
2. `POST /api/v1/exports` body `{ resume_version_id, template_id, filename }`.
3. Backend per §7.4: debit credit → render PDF → upload to Storage → signed URL.
4. Frontend triggers download via `<a download href={signed_url}>`. Toast "Downloaded …".

### 8.3 Analytics

`GET /api/v1/analytics/jd-progress` runs the single SQL join per §7.5. Used by a future `/dashboard/analytics` page (out of scope here, but data is ready).

### 8.4 Re-tailor invariants

- Tailoring the **same JD again**: new ResumeVersion row created with same `jd_evaluation_id`. History preserved.
- Tailoring a **new JD on the same resume**: backend tailor service always uses `ResumeDocument.parsed_json` as base, **never** the latest version. Verified by an integration test.

## 9. Error Handling

### Apply endpoint

| Failure | Detection | Response |
|---|---|---|
| JDEvaluation not found / wrong user | Ownership check | 404 |
| ResumeDocument deleted between tailor and apply | FK lookup fails | 410 Gone |
| Invalid `bullet_id` in accepted_changes | Pre-apply validation | 422 + bad IDs |
| `apply_changes()` schema error | Pydantic ValidationError | 422 + detail |
| Template render fails | try/except around `render_html_only` | Version row STILL inserted; `preview_html=""`, `warning` set |
| DB write fails | SQLAlchemy IntegrityError | 500; rollback; no orphan |

No credit debit on Apply → no refund logic needed.

### Export endpoint (Phase 2, extended)

| Failure | Response |
|---|---|
| Wrong user / not found | 404 |
| Insufficient credits | 402 (frontend opens credit purchase modal) |
| Playwright crash | 503; refund credit; retry-once internal |
| Storage upload fail | 503; refund credit |
| Bad filename (path traversal) | Server-sanitized via slugify; never errors |
| Unknown `template_id` | 422 |

### Analytics endpoint

| Failure | Response |
|---|---|
| DB connection drop | 503 + empty payload; frontend shows "Analytics temporarily unavailable" |

### Frontend resilience

- Apply 4xx → toast with backend `detail`; checkboxes stay unchanged; user can retry.
- Apply 5xx → toast "Save failed — try again."
- Empty preview_html → fallback "Preview unavailable. You can still download PDF."
- Export 402 → modal directing user to `/dashboard/credits`.
- Export 503 → toast "Render failed. Credit refunded."
- Browser blocks download → render signed URL as clickable fallback link.

### Security

- iframe sandboxed to `allow-same-origin` only — no script execution.
- All user-controlled fields (filename, company name) slugified before constructing storage path.
- Defense-in-depth: explicit ownership check on every endpoint, even though RLS enforces at DB layer.
- Analytics endpoint scoped exclusively to `current_user_id`; ignores query params.

### Observability

- Apply log line: `{event: "tailor_applied", user_id, jd_evaluation_id, version_id, changes_count, template_id, preview_render_ms}`.
- Export logs: existing Phase 2 latency / file_size / template structured logs.
- Analytics endpoint: query p95 latency alert if >500 ms (warns about missing index on `resume_versions.jd_evaluation_id`).

## 10. Testing

### Backend

**Migration**
- `test_2026_05_25_migration_idempotent` — apply + rollback + apply again; columns + index present.

**Schemas**
- `JDExtraction.company_name` optional + nullable.
- `ApplyTailorRequest` rejects unknown fields.
- `ApplyTailorResponse.filename_hint` slugifies unicode, spaces, special chars.

**Apply endpoint**
- `test_apply_creates_version_with_jd_fk`
- `test_apply_uses_base_resume_not_latest_version` (Q6.A invariant)
- `test_apply_404_on_unknown_jd_eval`
- `test_apply_404_on_other_users_jd` (don't leak existence)
- `test_apply_422_on_invalid_bullet_id`
- `test_apply_preview_html_renders`
- `test_apply_preview_render_failure_returns_warning`
- `test_apply_filename_hint_format`
- `test_apply_filename_hint_fallback_when_no_company`
- `test_apply_suggested_template_uses_country_and_role`
- `test_apply_zero_credit_cost`

**Exports endpoint (extended)**
- `test_export_with_custom_filename`
- `test_export_sanitizes_filename` (path-traversal blocked)
- `test_export_uses_version_template_id_when_request_omits`

**Analytics endpoint**
- `test_jd_progress_empty_for_new_user`
- `test_jd_progress_counts_applies_and_exports`
- `test_jd_progress_scopes_to_current_user`
- `test_jd_progress_query_under_100ms` (with 50 JDs / 200 versions seeded)

**Integration**
- `test_full_tailor_flow_e2e` (upload → evaluate → jd/analyze → apply → exports → signed URL works)
- `test_re_tailor_new_jd_starts_from_base`

### Frontend

**Component (Vitest + RTL)**
- `PreviewPanel renders iframe with provided HTML`
- `PreviewPanel template dropdown change updates state`
- `PreviewPanel filename input syncs to state`
- `PreviewPanel Download button disabled while exportPending`
- `PreviewPanel Download button posts correct payload`
- `Tailor page right column shows placeholder before Apply`
- `Tailor page right column hydrates after Apply success`

**E2E (Playwright)**
- `tailor-apply-export-flow.spec.ts` (mock backend → accept 2 changes → Apply → preview visible → Download triggers file save event)
- `tailor-credit-error.spec.ts` (mock 402 → credit modal appears)
- `tailor-preview-render-failure.spec.ts` (empty preview_html → fallback visible, Download still works)

### Test data

- New fixtures:
  - `backend/tests/fixtures/jds/with_company.txt` (company clearly named)
  - `backend/tests/fixtures/jds/no_company.txt` (blind / recruiter post)
- Existing 10 PDFs + 10 DOCX + 20 JDs cover SWE/DS/PM × US/IN for template resolution.

### CI gates

- Apply + Export + Analytics endpoint tests **block merge**.
- Frontend component tests **block merge**.
- Playwright E2E for tailor flow **blocks merge**.
- Analytics performance test runs nightly (not blocking) — alerts on regression.

## 11. Migration / Cleanup

- New columns nullable. No backfill needed.
- Pre-existing `ResumeVersion` rows from Phase 1–4 have `jd_evaluation_id = NULL` (legacy non-JD versions). Analytics endpoint filters those out via `WHERE jd_evaluation_id IS NOT NULL`.
- No data migration required when this lands.

## 12. Open Questions

- Should the preview panel auto-update if the user changes a checkbox AFTER Apply? Current design: no — they must click Apply again. Re-applying is cheap (0 credits). Revisit if users complain.
- Should we cap the number of ResumeVersion rows per JD? Current design: no — unbounded history is cheap until storage costs matter.
- Should the analytics endpoint paginate? Current design: no — single user's lifetime JD count is small (tens to low hundreds). Add cursor if abuse appears.

## 13. Next Steps

1. Write the implementation plan via `writing-plans` skill.
2. Implement: migration → schema additions → Apply endpoint → exports extension → analytics endpoint → frontend preview panel → wire-up + tests.
3. Manual smoke: full tailor → apply → download cycle on staging Supabase.
4. Merge to main, deploy.
5. Watch `tailor_applied` log volume + analytics query latency for one week.
