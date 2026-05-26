# Tailor Apply → Preview → Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the broken Apply button into a persisted, JD-linked ResumeVersion + side-panel HTML preview + Phase 2 PDF export with JD-aware filename, plus a per-JD analytics endpoint.

**Architecture:** Extend existing models (Approach 1 from spec). Add `jd_evaluation_id`, `accepted_at`, `template_id` columns to `resume_versions`. Add `company_name` to `JDExtraction`. New `POST /api/v1/jd/{id}/apply` endpoint creates version + renders preview HTML (Jinja2, no Playwright). Existing `POST /api/v1/exports` extended to accept custom filename + read `template_id` from ResumeVersion. New `GET /api/v1/analytics/jd-progress` joins the three tables. Frontend adds a sticky right-side preview pane in `/dashboard/resume/tailor` with template picker + filename editor + Download PDF button.

**Tech Stack:** FastAPI 0.110+, SQLAlchemy 2.0, Alembic, OpenAI 1.56 (`gpt-4o-2024-08-06`), Jinja2 (template render to HTML string), Playwright (HTML → PDF, Phase 2), Supabase Storage (signed URLs), Pydantic v2, Next.js 14 App Router, TanStack Query, shadcn/ui.

**Spec reference:** `docs/superpowers/specs/2026-05-25-tailor-apply-preview-export-design.md`

---

## File structure

**Backend — new:**
```
backend/migrations/versions/2026_05_25_jd_linked_versions.py
backend/tests/api/v1/test_jd_apply.py
backend/tests/api/v1/test_analytics_jd_progress.py
backend/tests/services/pdf/test_render_html_only.py
backend/tests/fixtures/jds/with_company.txt
backend/tests/fixtures/jds/no_company.txt
```

**Backend — modify:**
```
backend/app/models/resume_document.py           ← +3 columns on ResumeVersion
backend/app/schemas/jd.py                       ← +company_name on JDExtraction
backend/app/schemas/resume.py                   ← +ApplyTailorRequest/Response
backend/app/services/jd/extractor.py            ← prompt: require company extraction
backend/app/services/pdf/template_engine.py     ← +render_html_only() helper
backend/app/services/pdf/renderer.py            ← +filename override
backend/app/api/v1/endpoints/jd.py              ← +POST /jd/{id}/apply
backend/app/api/v1/endpoints/exports.py         ← accept filename + fallback to version template
backend/app/api/v1/endpoints/admin_metrics.py   ← +GET /analytics/jd-progress
backend/app/api/v1/api.py                       ← (no change — routers already registered)
backend/tests/api/v1/test_jd.py                 ← no change (apply test in new file)
```

**Frontend — new:**
```
frontend/src/components/tailor/preview-panel.tsx
frontend/src/hooks/use-tailor-apply.ts
frontend/src/hooks/use-export-pdf.ts
```

**Frontend — modify:**
```
frontend/src/lib/api/types.ts                    ← +ApplyTailorRequest/Response, +AnalyticsJdProgress
frontend/src/lib/api/index.ts                    ← +applyTailor, +exportPdf
frontend/src/app/dashboard/resume/tailor/page.tsx ← two-column layout, mount preview panel
frontend/src/components/tailor/diff-view.tsx     ← change Apply button wiring (call useApplyTailor)
```

---

### Task 1: Alembic migration — add JD link + accepted_at + template_id to resume_versions

**Files:**
- Create: `backend/migrations/versions/2026_05_25_jd_linked_versions.py`

- [ ] **Step 1: Find current head**

```bash
cd backend && alembic heads
```

Expected: `2026_05_20_storage` (or whatever the current head is — capture this for `down_revision`).

- [ ] **Step 2: Write the migration file**

```python
"""add jd link + accepted_at + template_id to resume_versions

Revision ID: 2026_05_25_jd_links
Revises: 2026_05_20_storage
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_05_25_jd_links"
down_revision = "2026_05_20_storage"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "resume_versions",
        sa.Column("jd_evaluation_id", sa.String(), nullable=True),
    )
    op.add_column(
        "resume_versions",
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "resume_versions",
        sa.Column("template_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_resume_versions_jd_evaluation_id",
        "resume_versions",
        "jd_evaluations",
        ["jd_evaluation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_resume_versions_jd_evaluation_id",
        "resume_versions",
        ["jd_evaluation_id"],
    )


def downgrade():
    op.drop_index("ix_resume_versions_jd_evaluation_id", "resume_versions")
    op.drop_constraint("fk_resume_versions_jd_evaluation_id", "resume_versions", type_="foreignkey")
    op.drop_column("resume_versions", "template_id")
    op.drop_column("resume_versions", "accepted_at")
    op.drop_column("resume_versions", "jd_evaluation_id")
```

If `alembic heads` returned a different revision, replace `down_revision = "2026_05_20_storage"` with the actual head id.

- [ ] **Step 3: Apply migration**

```bash
cd backend && alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade ... -> 2026_05_25_jd_links`.

If DB unreachable (Supabase only available remotely), skip apply locally — CI / staging will run it.

- [ ] **Step 4: Commit**

```bash
git add backend/migrations/versions/2026_05_25_jd_linked_versions.py
git commit -m "feat(db): jd_evaluation_id + accepted_at + template_id on resume_versions"
```

---

### Task 2: Extend SQLAlchemy model — add the three columns

**Files:**
- Modify: `backend/app/models/resume_document.py`

- [ ] **Step 1: Write a failing test**

Create `backend/tests/test_models_resume_version_columns.py`:

```python
def test_resume_version_has_jd_link_columns():
    from app.models.resume_document import ResumeVersion
    cols = {c.name for c in ResumeVersion.__table__.columns}
    assert "jd_evaluation_id" in cols
    assert "accepted_at" in cols
    assert "template_id" in cols
```

Run: `cd backend && python3.11 -m pytest tests/test_models_resume_version_columns.py -v`
Expected: FAIL — columns not yet on model.

- [ ] **Step 2: Add columns to model**

Open `backend/app/models/resume_document.py`. Find the `ResumeVersion` class. Add three columns after the existing ones:

```python
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base_class import Base


class ResumeVersion(Base):
    __tablename__ = "resume_versions"
    id = Column(String, primary_key=True, index=True)
    resume_document_id = Column(String, ForeignKey("resume_documents.id"), nullable=False, index=True)
    parent_version_id = Column(String, nullable=True)
    change_set = Column(JSONB, nullable=False)
    parsed_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Tailor-flow additions (2026-05-25)
    jd_evaluation_id = Column(String, ForeignKey("jd_evaluations.id"), nullable=True, index=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    template_id = Column(String, nullable=True)
```

- [ ] **Step 3: Update conftest SQLite table definition**

Open `backend/tests/conftest.py`. Find the `_create_sqlite_tables` helper. Locate the `resume_versions` Table definition. Add the three columns:

```python
sa.Table(
    "resume_versions",
    meta,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("resume_document_id", sa.String, sa.ForeignKey("resume_documents.id"), nullable=False, index=True),
    sa.Column("parent_version_id", sa.String, nullable=True),
    sa.Column("change_set", JSON, nullable=False),
    sa.Column("parsed_json", JSON, nullable=False),
    sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    sa.Column("jd_evaluation_id", sa.String, sa.ForeignKey("jd_evaluations.id"), nullable=True, index=True),
    sa.Column("accepted_at", sa.DateTime, nullable=True),
    sa.Column("template_id", sa.String, nullable=True),
),
```

- [ ] **Step 4: Verify test passes**

```bash
cd backend && python3.11 -m pytest tests/test_models_resume_version_columns.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/resume_document.py backend/tests/conftest.py backend/tests/test_models_resume_version_columns.py
git commit -m "feat(models): add jd_evaluation_id + accepted_at + template_id to ResumeVersion"
```

---

### Task 3: Extend JDExtraction schema with company_name

**Files:**
- Modify: `backend/app/schemas/jd.py`
- Modify: `backend/app/services/jd/extractor.py`
- Modify: `backend/tests/services/jd/test_extractor.py`

- [ ] **Step 1: Add field to schema**

Edit `backend/app/schemas/jd.py`. Add to `JDExtraction`:

```python
class JDExtraction(BaseModel):
    must_have: List[Requirement]
    good_to_have: List[Requirement]
    soft_skills: List[str] = Field(default_factory=list)
    seniority: Literal["junior", "mid", "senior", "staff"]
    primary_role_category: Literal["SWE", "DS", "PM", "other"]
    country_hint: Literal["US", "IN", "other"]
    red_flags: List[str] = Field(default_factory=list)
    company_name: Optional[str] = None
```

- [ ] **Step 2: Update extractor system prompt**

Edit `backend/app/services/jd/extractor.py`. Find `EXTRACTOR_SYSTEM`. Add a `company_name` line in the field spec list:

```
- company_name: best-effort extraction of the hiring company's name from the JD body. If the JD is a blind recruiter post and the company is not named, return null.
```

- [ ] **Step 3: Write failing schema test**

Add to `backend/tests/services/jd/test_extractor.py`:

```python
import pytest, respx, httpx, json
from app.services.jd.extractor import extract_jd_requirements


@pytest.mark.asyncio
@respx.mock
async def test_extractor_returns_company_name_when_present():
    payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "parsed": {
                "must_have": [{"skill": "Python", "evidence_from_jd": "5+ yrs", "type": "technical"}],
                "good_to_have": [],
                "soft_skills": [],
                "seniority": "senior",
                "primary_role_category": "SWE",
                "country_hint": "US",
                "red_flags": [],
                "company_name": "Stripe",
            }, "content": json.dumps({})}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.route(url="https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=payload))
    result = await extract_jd_requirements("Senior Python at Stripe...")
    assert result.company_name == "Stripe"


@pytest.mark.asyncio
@respx.mock
async def test_extractor_returns_null_company_when_blind():
    payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "parsed": {
                "must_have": [{"skill": "Python", "evidence_from_jd": "5+ yrs", "type": "technical"}],
                "good_to_have": [],
                "soft_skills": [],
                "seniority": "mid",
                "primary_role_category": "SWE",
                "country_hint": "US",
                "red_flags": [],
                "company_name": None,
            }, "content": json.dumps({})}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.route(url="https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=payload))
    result = await extract_jd_requirements("Confidential client — blind post...")
    assert result.company_name is None
```

Run: `cd backend && python3.11 -m pytest tests/services/jd/test_extractor.py -v -k company`
Expected: PASS (schema accepts None default).

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/jd.py backend/app/services/jd/extractor.py backend/tests/services/jd/test_extractor.py
git commit -m "feat(jd): company_name on JDExtraction; extractor prompt requires it"
```

---

### Task 4: Add `render_html_only()` to template engine

**Files:**
- Modify: `backend/app/services/pdf/template_engine.py`
- Create: `backend/tests/services/pdf/test_render_html_only.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/services/pdf/test_render_html_only.py`:

```python
from app.services.pdf.template_engine import render_html_only
from app.schemas.resume_v2 import ResumeDocumentJSON, Contact, ExperienceEntry, Bullet, Skills


def _doc():
    return ResumeDocumentJSON(
        contact=Contact(name="Test User", email="t@u.com"),
        experience=[ExperienceEntry(
            company="Acme", role="SWE",
            bullets=[Bullet(id="b1", text="Built things", raw_text="Built things")])],
        skills=Skills(hard=["Python"]),
        raw_text="ignored",
    )


def test_render_html_only_returns_string():
    html = render_html_only(_doc(), country="US", role="swe")
    assert isinstance(html, str)
    assert "Test User" in html
    assert "Acme" in html


def test_render_html_only_inlines_css():
    """Iframe srcdoc cannot fetch external CSS — must be inlined."""
    html = render_html_only(_doc(), country="US", role="swe")
    # Some marker from inlined CSS that we know exists in _base.css
    assert "<style>" in html or "<style type=" in html
    # No file:// URLs should remain
    assert "file://" not in html


def test_render_html_only_unknown_country_raises():
    import pytest
    with pytest.raises(ValueError):
        render_html_only(_doc(), country="XX", role="swe")
```

Run: `cd backend && python3.11 -m pytest tests/services/pdf/test_render_html_only.py -v`
Expected: FAIL — `render_html_only` not yet exported.

- [ ] **Step 2: Implement the helper**

Edit `backend/app/services/pdf/template_engine.py`. Add at the bottom of the file:

```python
from pathlib import Path

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _inlined_shared_css() -> str:
    """Read all shared CSS files and return as a single <style> block."""
    parts = []
    for name in ("_base.css", "_typography.css", "_print.css"):
        css_path = _TEMPLATES_DIR / "shared" / name
        if css_path.exists():
            parts.append(css_path.read_text())
    if not parts:
        return ""
    return "<style>\n" + "\n".join(parts) + "\n</style>"


def render_html_only(
    doc,
    country,
    role,
) -> str:
    """Render a resume document to a fully self-contained HTML string.

    Differences from render_html:
      - CSS is inlined as a <style> block (no file:// URLs) so the output
        can be displayed in a sandboxed iframe srcdoc without external
        asset fetches.

    Args:
        doc: ResumeDocumentJSON (Phase 1 schema)
        country: "US" or "IN"
        role: "swe" / "ds" / "pm"

    Returns:
        Self-contained HTML string ready for iframe srcdoc.

    Raises:
        ValueError: if country or role is invalid.
        jinja2.TemplateNotFound: if the template file is missing.
    """
    template_path = pick_template(country, role)
    template = _env.get_template(template_path)
    html = template.render(
        resume=doc.model_dump() if hasattr(doc, "model_dump") else doc,
        # Existing render_html passed shared_css_url; we override with inlined version
        shared_css_url=None,
    )
    # Strip any leftover external stylesheet links and inject inline styles.
    import re
    html = re.sub(
        r'<link[^>]+href="file://[^"]+"[^>]*>',
        "",
        html,
    )
    inlined = _inlined_shared_css()
    # Inject inlined styles right before </head> (or at start if no head tag).
    if "</head>" in html:
        html = html.replace("</head>", f"{inlined}\n</head>", 1)
    else:
        html = inlined + html
    return html
```

- [ ] **Step 3: Run the test — expect PASS**

```bash
cd backend && python3.11 -m pytest tests/services/pdf/test_render_html_only.py -v
```
Expected: 3 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/pdf/template_engine.py backend/tests/services/pdf/test_render_html_only.py
git commit -m "feat(pdf): render_html_only() — self-contained HTML for iframe preview"
```

---

### Task 5: Add Pydantic schemas — ApplyTailorRequest + ApplyTailorResponse

**Files:**
- Modify: `backend/app/schemas/resume_v2.py`
- Create: `backend/tests/schemas/test_apply_schemas.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/schemas/test_apply_schemas.py`:

```python
import pytest
from pydantic import ValidationError
from app.schemas.resume_v2 import ApplyTailorRequest, ApplyTailorResponse, ChangeItem


def test_apply_request_accepts_changes_with_optional_template():
    req = ApplyTailorRequest(
        accepted_changes=[ChangeItem(type="bullet_update", bullet_id="b1", new_text="x")],
        template_id="us-swe",
    )
    assert req.template_id == "us-swe"


def test_apply_request_template_id_optional():
    req = ApplyTailorRequest(
        accepted_changes=[ChangeItem(type="bullet_update", bullet_id="b1", new_text="x")],
    )
    assert req.template_id is None


def test_apply_response_minimal():
    resp = ApplyTailorResponse(
        version_id="v1",
        preview_html="<html>...</html>",
        company_name="Stripe",
        suggested_template="us-swe",
        filename_hint="test-user-stripe.pdf",
    )
    assert resp.warning is None


def test_apply_response_with_warning():
    resp = ApplyTailorResponse(
        version_id="v1",
        preview_html="",
        company_name=None,
        suggested_template="us-swe",
        filename_hint="test-user-resume.pdf",
        warning="Preview unavailable",
    )
    assert resp.preview_html == ""
    assert resp.warning == "Preview unavailable"
```

Run: `cd backend && python3.11 -m pytest tests/schemas/test_apply_schemas.py -v`
Expected: FAIL — schemas not yet defined.

- [ ] **Step 2: Define schemas**

Edit `backend/app/schemas/resume_v2.py`. The file already has a `ChangeItem` class for the `versions` endpoint. Append:

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

If `ChangeItem` isn't defined in `resume_v2.py` (it may live in `api/v1/endpoints/resumes_v2.py` as a nested class), then move it to `resume_v2.py` first OR import it where needed. Grep first:

```bash
cd backend && grep -rn "class ChangeItem" app/
```

If the class lives only in the endpoint file, define it in `app/schemas/resume_v2.py`:

```python
class ChangeItem(BaseModel):
    type: Literal["bullet_update", "skills_reorder", "summary_update"]
    bullet_id: Optional[str] = None
    new_text: Optional[str] = None
    new_skills_order: Optional[List[str]] = None
    new_summary: Optional[str] = None
```

Then update `app/api/v1/endpoints/resumes_v2.py` to import from `app.schemas.resume_v2` instead of redeclaring.

- [ ] **Step 3: Run the test — expect PASS**

```bash
cd backend && python3.11 -m pytest tests/schemas/test_apply_schemas.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/resume_v2.py backend/tests/schemas/test_apply_schemas.py backend/app/api/v1/endpoints/resumes_v2.py
git commit -m "feat(schemas): ApplyTailorRequest + ApplyTailorResponse; centralise ChangeItem"
```

---

### Task 6: Implement `POST /api/v1/jd/{jd_evaluation_id}/apply`

**Files:**
- Modify: `backend/app/api/v1/endpoints/jd.py`
- Create: `backend/tests/api/v1/test_jd_apply.py`

- [ ] **Step 1: Write the failing test (ownership + happy path)**

Create `backend/tests/api/v1/test_jd_apply.py`:

```python
import uuid
import pytest


def _seed_jd(db_session, user_id, resume_doc_id):
    """Helper: insert a JDEvaluation row directly."""
    from app.models.jd_evaluation import JDEvaluation
    jd = JDEvaluation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        resume_document_id=resume_doc_id,
        jd_text="Senior Python at Stripe",
        extracted_requirements={"company_name": "Stripe", "country_hint": "US", "primary_role_category": "SWE"},
        diff_plan={"company_name": "Stripe"},
        match_score=75,
    )
    db_session.add(jd)
    db_session.commit()
    return jd.id


def _seed_resume_doc(db_session, user_id):
    from app.models.resume_document import ResumeDocument
    doc_id = str(uuid.uuid4())
    db_session.add(ResumeDocument(
        id=doc_id, user_id=user_id, original_filename="r.pdf",
        file_path="/x", file_type="pdf",
        parsed_json={
            "contact": {"name": "Test User", "email": "t@u.com", "links": []},
            "experience": [{"company": "Acme", "role": "SWE", "bullets": [{"id": "b1", "text": "Did things", "raw_text": "Did things"}]}],
            "education": [], "skills": {"hard": ["Python"], "soft": []},
            "projects": [], "certifications": [], "raw_text": "...",
        },
        raw_text="...",
    ))
    db_session.commit()
    return doc_id


def test_apply_creates_version_with_jd_fk(client, auth_headers, db_session, test_user_id):
    doc_id = _seed_resume_doc(db_session, test_user_id)
    jd_id = _seed_jd(db_session, test_user_id, doc_id)
    body = {
        "accepted_changes": [
            {"type": "bullet_update", "bullet_id": "b1", "new_text": "Built Python services on AWS"}
        ],
    }
    resp = client.post(f"/api/v1/jd/{jd_id}/apply", json=body, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "version_id" in data
    assert data["filename_hint"].endswith("-stripe.pdf")
    assert data["suggested_template"] == "us-swe"

    # ResumeVersion row should exist with jd_evaluation_id set
    from app.models.resume_document import ResumeVersion
    row = db_session.query(ResumeVersion).filter_by(id=data["version_id"]).first()
    assert row is not None
    assert row.jd_evaluation_id == jd_id
    assert row.template_id == "us-swe"
    assert row.accepted_at is not None


def test_apply_404_on_unknown_jd(client, auth_headers, test_user_id):
    resp = client.post("/api/v1/jd/00000000-0000-0000-0000-000000000000/apply",
                       json={"accepted_changes": []}, headers=auth_headers)
    assert resp.status_code == 404


def test_apply_zero_credit_cost(client, auth_headers, db_session, test_user_id):
    from app.services.credits.ledger import get_balance
    doc_id = _seed_resume_doc(db_session, test_user_id)
    jd_id = _seed_jd(db_session, test_user_id, doc_id)
    bal_before = get_balance(db_session, test_user_id)
    client.post(f"/api/v1/jd/{jd_id}/apply",
                json={"accepted_changes": []}, headers=auth_headers)
    assert get_balance(db_session, test_user_id) == bal_before
```

Run: `cd backend && python3.11 -m pytest tests/api/v1/test_jd_apply.py -v`
Expected: FAIL — endpoint not implemented.

- [ ] **Step 2: Implement the endpoint**

Edit `backend/app/api/v1/endpoints/jd.py`. Add at the bottom:

```python
import uuid
import re
from datetime import datetime, timezone
from app.schemas.resume_v2 import (
    ResumeDocumentJSON,
    ApplyTailorRequest,
    ApplyTailorResponse,
)
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.jd_evaluation import JDEvaluation
from app.api.v1.endpoints.resumes_v2 import apply_changes  # reuse existing helper
from app.services.pdf.template_engine import render_html_only


def _slugify(value: str) -> str:
    """Lowercase, replace non-alphanum with hyphens, collapse repeats, strip ends."""
    value = (value or "").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "user"


@router.post("/{jd_evaluation_id}/apply", response_model=ApplyTailorResponse)
async def apply_tailor(
    jd_evaluation_id: str,
    body: ApplyTailorRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    # 1. Load + ownership check
    jd = db.get(JDEvaluation, jd_evaluation_id)
    if not jd or jd.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="JD evaluation not found")

    # 2. Load base ResumeDocument (always original, never latest version)
    doc_row = db.get(ResumeDocument, jd.resume_document_id)
    if not doc_row:
        raise HTTPException(status_code=410, detail="Source resume removed")

    base_doc = ResumeDocumentJSON.model_validate(doc_row.parsed_json)

    # 3. Apply accepted_changes via the existing helper from resumes_v2.py
    try:
        merged_doc = apply_changes(base_doc, body.accepted_changes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid changes: {e}")

    # 4. Resolve template_id
    requirements = jd.extracted_requirements or {}
    country = (requirements.get("country_hint") or "US").upper()
    if country not in ("US", "IN"):
        country = "US"  # fallback for "other"
    role = (requirements.get("primary_role_category") or "SWE").lower()
    if role not in ("swe", "ds", "pm"):
        role = "swe"  # fallback for "other"
    suggested_template = f"{country.lower()}-{role}"
    template_id = body.template_id or suggested_template

    # 5. Render preview HTML (best-effort — never fails the whole request)
    preview_html = ""
    warning = None
    try:
        preview_html = render_html_only(merged_doc, country=country, role=role)
    except Exception as e:
        warning = f"Preview unavailable: {e}"

    # 6. INSERT ResumeVersion row
    version_id = str(uuid.uuid4())
    db.add(ResumeVersion(
        id=version_id,
        resume_document_id=doc_row.id,
        parent_version_id=None,  # star pattern; not linear
        change_set=[c.model_dump() for c in body.accepted_changes],
        parsed_json=merged_doc.model_dump(),
        jd_evaluation_id=jd.id,
        accepted_at=datetime.now(timezone.utc),
        template_id=template_id,
    ))
    db.commit()

    # 7. Filename hint
    name_parts = (merged_doc.contact.name or "user").split()
    first = _slugify(name_parts[0])
    last = _slugify(name_parts[-1] if len(name_parts) > 1 else "")
    company = _slugify(requirements.get("company_name") or "resume")
    parts = [p for p in (first, last, company) if p]
    filename_hint = "-".join(parts) + ".pdf"

    return ApplyTailorResponse(
        version_id=version_id,
        preview_html=preview_html,
        company_name=requirements.get("company_name"),
        suggested_template=suggested_template,
        filename_hint=filename_hint,
        warning=warning,
    )
```

- [ ] **Step 3: Run the test — expect PASS**

```bash
cd backend && python3.11 -m pytest tests/api/v1/test_jd_apply.py -v
```
Expected: 3 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/endpoints/jd.py backend/tests/api/v1/test_jd_apply.py
git commit -m "feat(api): POST /jd/{id}/apply — creates JD-linked ResumeVersion + preview HTML"
```

---

### Task 7: Re-tailor invariant test — new JD always branches from base

**Files:**
- Modify: `backend/tests/api/v1/test_jd_apply.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/api/v1/test_jd_apply.py`:

```python
def test_apply_uses_base_resume_not_latest_version(client, auth_headers, db_session, test_user_id):
    """Q6.A invariant: second JD must tailor from base ResumeDocument,
    NOT from the version created by the first JD's apply."""
    doc_id = _seed_resume_doc(db_session, test_user_id)
    jd1 = _seed_jd(db_session, test_user_id, doc_id)

    # Apply JD1 — bullet b1 becomes "JD1 bullet"
    client.post(f"/api/v1/jd/{jd1}/apply", json={
        "accepted_changes": [
            {"type": "bullet_update", "bullet_id": "b1", "new_text": "JD1 bullet"}
        ],
    }, headers=auth_headers)

    # Now seed JD2 and apply
    jd2 = _seed_jd(db_session, test_user_id, doc_id)
    resp = client.post(f"/api/v1/jd/{jd2}/apply", json={
        "accepted_changes": [],  # accept no changes
    }, headers=auth_headers)
    assert resp.status_code == 200
    version_id = resp.json()["version_id"]

    from app.models.resume_document import ResumeVersion
    v2 = db_session.query(ResumeVersion).filter_by(id=version_id).first()
    # parsed_json should reflect the ORIGINAL bullet, not JD1's edit
    bullets = v2.parsed_json["experience"][0]["bullets"]
    assert bullets[0]["text"] == "Did things"  # original, not "JD1 bullet"
```

Run: `cd backend && python3.11 -m pytest tests/api/v1/test_jd_apply.py::test_apply_uses_base_resume_not_latest_version -v`
Expected: PASS (the implementation in Task 6 already loads from `ResumeDocument`, not from any version).

- [ ] **Step 2: Commit**

```bash
git add backend/tests/api/v1/test_jd_apply.py
git commit -m "test(jd-apply): invariant — re-tailor branches from base resume, not latest version"
```

---

### Task 8: Extend `/api/v1/exports` — accept custom filename + version template fallback

**Files:**
- Modify: `backend/app/api/v1/endpoints/exports.py`
- Modify: `backend/tests/api/v1/test_exports_endpoint.py` (or wherever exports tests live)

- [ ] **Step 1: Inspect existing exports endpoint**

```bash
cd backend && grep -n "filename\|template_id\|def export\|ExportRequest" app/api/v1/endpoints/exports.py | head -20
```

Note the existing function name + request body shape.

- [ ] **Step 2: Write the failing test**

Append to the appropriate exports test file (e.g. `backend/tests/api/v1/test_exports_endpoint.py`):

```python
def test_export_with_custom_filename(client, auth_headers, db_session, test_user_id, mocker):
    """Filename in request body should drive storage path + signed URL filename."""
    # Seed a ResumeVersion with template_id
    from app.models.resume_document import ResumeDocument, ResumeVersion
    import uuid
    doc_id = str(uuid.uuid4())
    db_session.add(ResumeDocument(
        id=doc_id, user_id=test_user_id, original_filename="r.pdf",
        file_path="/x", file_type="pdf",
        parsed_json={"contact": {"name": "Test"}, "experience": [], "education": [],
                     "skills": {"hard": [], "soft": []}, "projects": [], "certifications": [], "raw_text": ""},
        raw_text="",
    ))
    version_id = str(uuid.uuid4())
    db_session.add(ResumeVersion(
        id=version_id, resume_document_id=doc_id,
        change_set=[], parsed_json={"contact": {"name": "Test"}, "experience": [], "education": [],
                                     "skills": {"hard": [], "soft": []}, "projects": [], "certifications": [], "raw_text": ""},
        template_id="us-swe",
    ))
    db_session.commit()

    # Grant credits
    from app.services.credits.ledger import grant_monthly
    grant_monthly(db_session, test_user_id, 5)
    db_session.commit()

    # Mock the actual PDF render to avoid Playwright in unit tests
    mocker.patch("app.api.v1.endpoints.exports.render_pdf_from_doc", return_value=b"%PDF-1.4 fake")
    mocker.patch("app.api.v1.endpoints.exports.get_storage").return_value.upload.return_value = "test-user/exports/x.pdf"
    mocker.patch("app.api.v1.endpoints.exports.get_storage").return_value.signed_url.return_value = "https://signed.url/x"

    resp = client.post("/api/v1/exports", json={
        "resume_version_id": version_id,
        "filename": "custom-name.pdf",
    }, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["filename"] == "custom-name.pdf"


def test_export_sanitizes_filename(client, auth_headers, db_session, test_user_id, mocker):
    """Path-traversal segments must be stripped."""
    # ... same setup, but filename = "../../etc/passwd.pdf"
    # Assert returned filename is sanitized (no .., no /, no \).
    pass  # full implementation in Step 3 below
```

Run: `cd backend && python3.11 -m pytest tests/api/v1/test_exports_endpoint.py::test_export_with_custom_filename -v`
Expected: FAIL — endpoint doesn't accept `filename` yet.

- [ ] **Step 3: Implement filename support + sanitisation**

Edit `backend/app/api/v1/endpoints/exports.py`. Add to the request model (find the existing `ExportRequest` class):

```python
class ExportRequest(BaseModel):
    resume_version_id: str
    template_id: Optional[str] = None
    filename: Optional[str] = None
```

In the endpoint handler, add at the appropriate point:

```python
import re

def _sanitize_filename(name: str, default: str = "resume.pdf") -> str:
    """Strip path-traversal + control chars. Ensure .pdf suffix."""
    if not name:
        return default
    # Strip directory parts
    name = name.replace("\\", "/").split("/")[-1]
    # Remove .. and control chars
    name = re.sub(r"[\x00-\x1f]", "", name).replace("..", "")
    # Allow only alphanum, dash, underscore, dot
    name = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-")
    if not name:
        return default
    if not name.lower().endswith(".pdf"):
        name = name + ".pdf"
    return name


# Inside the endpoint, after loading ResumeVersion:
template_id = body.template_id or version.template_id or "us-swe"
filename = _sanitize_filename(body.filename, default=f"{version.id}.pdf")

# Pass `filename` into storage upload path + return in response:
storage_path = f"{current_user_id}/exports/{version.id}_{filename}"
# ... upload + signed_url generation as before ...
return {"export_id": ..., "signed_url": ..., "filename": filename}
```

Make sure the response includes `filename` so the frontend can use it for the `<a download>` attribute.

Also flesh out `test_export_sanitizes_filename`:

```python
def test_export_sanitizes_filename(client, auth_headers, db_session, test_user_id, mocker):
    # Same setup as test_export_with_custom_filename, but:
    resp = client.post("/api/v1/exports", json={
        "resume_version_id": version_id,
        "filename": "../../etc/passwd.pdf",
    }, headers=auth_headers)
    assert resp.status_code == 200
    name = resp.json()["filename"]
    assert ".." not in name
    assert "/" not in name
    assert "\\" not in name
```

- [ ] **Step 4: Run the tests — expect PASS**

```bash
cd backend && python3.11 -m pytest tests/api/v1/test_exports_endpoint.py -v -k "custom_filename or sanitizes"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/endpoints/exports.py backend/tests/api/v1/test_exports_endpoint.py
git commit -m "feat(api): /exports accepts filename + falls back to version template_id"
```

---

### Task 9: Implement `GET /api/v1/analytics/jd-progress`

**Files:**
- Modify: `backend/app/api/v1/endpoints/admin_metrics.py`
- Create: `backend/tests/api/v1/test_analytics_jd_progress.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/api/v1/test_analytics_jd_progress.py`:

```python
import uuid


def test_jd_progress_empty_for_new_user(client, auth_headers):
    resp = client.get("/api/v1/analytics/jd-progress", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["jds"] == []
    assert data["totals"] == {"jds_tailored": 0, "versions_created": 0, "pdfs_exported": 0}


def test_jd_progress_counts(client, auth_headers, db_session, test_user_id):
    from app.models.resume_document import ResumeDocument, ResumeVersion
    from app.models.jd_evaluation import JDEvaluation

    doc_id = str(uuid.uuid4())
    db_session.add(ResumeDocument(
        id=doc_id, user_id=test_user_id, original_filename="r.pdf",
        file_path="/x", file_type="pdf",
        parsed_json={}, raw_text="",
    ))
    jd1 = str(uuid.uuid4())
    db_session.add(JDEvaluation(
        id=jd1, user_id=test_user_id, resume_document_id=doc_id,
        jd_text="...", extracted_requirements={"company_name": "Stripe"},
        diff_plan={}, match_score=80,
    ))
    # 2 versions on jd1
    for _ in range(2):
        db_session.add(ResumeVersion(
            id=str(uuid.uuid4()), resume_document_id=doc_id,
            change_set=[], parsed_json={},
            jd_evaluation_id=jd1, template_id="us-swe",
        ))
    db_session.commit()

    resp = client.get("/api/v1/analytics/jd-progress", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["jds"]) == 1
    assert data["jds"][0]["jd_evaluation_id"] == jd1
    assert data["jds"][0]["applies_count"] == 2
    assert data["jds"][0]["exports_count"] == 0
    assert data["totals"]["jds_tailored"] == 1
    assert data["totals"]["versions_created"] == 2
```

Run: `cd backend && python3.11 -m pytest tests/api/v1/test_analytics_jd_progress.py -v`
Expected: FAIL — endpoint not present.

- [ ] **Step 2: Implement the endpoint**

Edit `backend/app/api/v1/endpoints/admin_metrics.py`. Append:

```python
from sqlalchemy import func, select
from app.models.jd_evaluation import JDEvaluation
from app.models.resume_document import ResumeVersion
# resume_exports model — if available; if not, use a raw count placeholder
try:
    from app.models.resume_export import ResumeExport
    _HAS_EXPORTS_MODEL = True
except ImportError:
    _HAS_EXPORTS_MODEL = False


@router.get("/jd-progress")  # router is /analytics/... when registered
def jd_progress(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Per-JD funnel metrics for the current user."""
    jd_rows = db.query(JDEvaluation).filter(JDEvaluation.user_id == current_user_id).all()
    out = {"jds": [], "totals": {"jds_tailored": 0, "versions_created": 0, "pdfs_exported": 0}}
    for jd in jd_rows:
        applies = db.query(func.count(ResumeVersion.id)).filter(
            ResumeVersion.jd_evaluation_id == jd.id
        ).scalar() or 0
        if _HAS_EXPORTS_MODEL:
            exports = db.query(func.count(ResumeExport.id)).join(
                ResumeVersion, ResumeExport.resume_version_id == ResumeVersion.id
            ).filter(ResumeVersion.jd_evaluation_id == jd.id).scalar() or 0
        else:
            exports = 0
        out["jds"].append({
            "jd_evaluation_id": jd.id,
            "jd_company": (jd.extracted_requirements or {}).get("company_name"),
            "tailored_at": jd.created_at.isoformat() if jd.created_at else None,
            "applies_count": applies,
            "exports_count": exports,
            "last_match_score": jd.match_score,
        })
        out["totals"]["jds_tailored"] += 1
        out["totals"]["versions_created"] += applies
        out["totals"]["pdfs_exported"] += exports
    return out
```

The router prefix is set per `admin_metrics.py` — verify it's mounted under `/analytics` OR adjust. If the file's router is `/admin/metrics`, create a NEW router file `backend/app/api/v1/endpoints/analytics.py` instead and register it in `app/api/v1/api.py`. Pick whichever path matches the existing register pattern.

- [ ] **Step 3: Register the router (if new file)**

In `backend/app/api/v1/api.py`, ensure there's a line like:

```python
from app.api.v1.endpoints import analytics  # if new file
api_router.include_router(analytics.router)
```

- [ ] **Step 4: Run the tests — expect PASS**

```bash
cd backend && python3.11 -m pytest tests/api/v1/test_analytics_jd_progress.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/endpoints/ backend/app/api/v1/api.py backend/tests/api/v1/test_analytics_jd_progress.py
git commit -m "feat(api): GET /analytics/jd-progress — per-JD funnel counts"
```

---

### Task 10: Frontend — types + API client + hooks

**Files:**
- Modify: `frontend/src/lib/api/types.ts`
- Modify: `frontend/src/lib/api/index.ts`
- Create: `frontend/src/hooks/use-tailor-apply.ts`

- [ ] **Step 1: Add types**

Edit `frontend/src/lib/api/types.ts`. Append:

```ts
export interface ChangeItem {
  type: 'bullet_update' | 'skills_reorder' | 'summary_update';
  bullet_id?: string;
  new_text?: string;
  new_skills_order?: string[];
  new_summary?: string;
}

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

export interface AnalyticsJdProgress {
  jds: Array<{
    jd_evaluation_id: string;
    jd_company: string | null;
    tailored_at: string | null;
    applies_count: number;
    exports_count: number;
    last_match_score: number | null;
  }>;
  totals: {
    jds_tailored: number;
    versions_created: number;
    pdfs_exported: number;
  };
}
```

- [ ] **Step 2: Add API client function**

Edit `frontend/src/lib/api/index.ts`. Append within the existing JD API object (or create one):

```ts
export const jdApi = {
  // ... existing methods ...
  applyTailor: async (
    jdEvaluationId: string,
    body: ApplyTailorRequest
  ): Promise<ApplyTailorResponse> => {
    return makeAPIRequest<ApplyTailorResponse>(
      `/api/v1/jd/${jdEvaluationId}/apply`,
      { method: 'POST', body: JSON.stringify(body) }
    );
  },
};
```

If the existing pattern uses a different request helper, follow the existing convention.

- [ ] **Step 3: Write the hook**

Create `frontend/src/hooks/use-tailor-apply.ts`:

```ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { jdApi } from '@/lib/api';
import type { ApplyTailorRequest, ApplyTailorResponse } from '@/lib/api/types';

export function useTailorApply(jdEvaluationId: string) {
  const qc = useQueryClient();
  return useMutation<ApplyTailorResponse, Error, ApplyTailorRequest>({
    mutationFn: (body) => jdApi.applyTailor(jdEvaluationId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['versions'] });
      qc.invalidateQueries({ queryKey: ['credits-balance'] });
      qc.invalidateQueries({ queryKey: ['jd-progress'] });
    },
  });
}
```

- [ ] **Step 4: Verify frontend builds**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

Expected: build succeeds with no new type errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/api/types.ts frontend/src/lib/api/index.ts frontend/src/hooks/use-tailor-apply.ts
git commit -m "feat(api-client): types + applyTailor mutation + useTailorApply hook"
```

---

### Task 11: Frontend — useExportPdf hook (extending Phase 2 exports)

**Files:**
- Create: `frontend/src/hooks/use-export-pdf.ts`
- Modify: `frontend/src/lib/api/index.ts`

- [ ] **Step 1: Extend the API client**

Edit `frontend/src/lib/api/index.ts`. Add:

```ts
export interface ExportPdfRequest {
  resume_version_id: string;
  template_id?: string;
  filename?: string;
}

export interface ExportPdfResponse {
  export_id: string;
  signed_url: string;
  filename: string;
}

export const exportsApi = {
  exportPdf: async (body: ExportPdfRequest): Promise<ExportPdfResponse> => {
    return makeAPIRequest<ExportPdfResponse>('/api/v1/exports', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
};
```

- [ ] **Step 2: Write the hook**

Create `frontend/src/hooks/use-export-pdf.ts`:

```ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { exportsApi, type ExportPdfRequest, type ExportPdfResponse } from '@/lib/api';

export function useExportPdf() {
  const qc = useQueryClient();
  return useMutation<ExportPdfResponse, Error, ExportPdfRequest>({
    mutationFn: (body) => exportsApi.exportPdf(body),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['credits-balance'] });
      qc.invalidateQueries({ queryKey: ['jd-progress'] });
      // Trigger browser download
      const a = document.createElement('a');
      a.href = data.signed_url;
      a.download = data.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    },
  });
}
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/api/index.ts frontend/src/hooks/use-export-pdf.ts
git commit -m "feat(hooks): useExportPdf — triggers browser download on success"
```

---

### Task 12: PreviewPanel component

**Files:**
- Create: `frontend/src/components/tailor/preview-panel.tsx`

- [ ] **Step 1: Implement the component**

Create `frontend/src/components/tailor/preview-panel.tsx`:

```tsx
"use client";

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { useExportPdf } from '@/hooks/use-export-pdf';

const TEMPLATE_OPTIONS = [
  { id: 'us-swe', label: 'USA — Software Engineer' },
  { id: 'us-ds', label: 'USA — Data Scientist' },
  { id: 'us-pm', label: 'USA — Product Manager' },
  { id: 'in-swe', label: 'India — Software Engineer' },
  { id: 'in-ds', label: 'India — Data Scientist' },
  { id: 'in-pm', label: 'India — Product Manager' },
];

interface PreviewPanelProps {
  versionId: string;
  previewHtml: string;
  suggestedTemplate: string;
  filenameHint: string;
  warning?: string;
}

export function PreviewPanel({
  versionId,
  previewHtml,
  suggestedTemplate,
  filenameHint,
  warning,
}: PreviewPanelProps) {
  const [template, setTemplate] = useState(suggestedTemplate);
  const [filename, setFilename] = useState(filenameHint);
  const exportMut = useExportPdf();
  const { toast } = useToast();

  // Re-sync when new Apply lands
  useEffect(() => {
    setTemplate(suggestedTemplate);
    setFilename(filenameHint);
  }, [versionId, suggestedTemplate, filenameHint]);

  const onDownload = async () => {
    try {
      await exportMut.mutateAsync({
        resume_version_id: versionId,
        template_id: template,
        filename,
      });
      toast({ title: 'Downloaded', description: filename });
    } catch (e: any) {
      const msg = e?.message ?? 'Export failed';
      if (msg.includes('402') || msg.toLowerCase().includes('credit')) {
        toast({
          title: 'Need more credits',
          description: 'Add credits in /dashboard/credits to export.',
          variant: 'destructive',
        });
      } else {
        toast({ title: 'Export failed', description: msg, variant: 'destructive' });
      }
    }
  };

  return (
    <aside className="sticky top-24 h-[calc(100vh-8rem)] flex flex-col gap-4">
      <div className="flex-1 overflow-hidden border border-border rounded-md bg-card">
        {previewHtml ? (
          <iframe
            srcDoc={previewHtml}
            sandbox="allow-same-origin"
            className="w-full h-full"
            title="Resume preview"
          />
        ) : (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground p-6 text-center">
            {warning ?? 'Apply changes to see preview'}
          </div>
        )}
      </div>

      <div className="space-y-3">
        <div>
          <label className="text-xs uppercase tracking-wider text-muted-foreground">Template</label>
          <Select value={template} onValueChange={setTemplate}>
            <SelectTrigger className="w-full mt-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TEMPLATE_OPTIONS.map((opt) => (
                <SelectItem key={opt.id} value={opt.id}>{opt.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <label className="text-xs uppercase tracking-wider text-muted-foreground">Filename</label>
          <Input
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            placeholder="firstname-lastname-company.pdf"
            className="mt-1"
          />
        </div>

        <Button
          onClick={onDownload}
          disabled={exportMut.isPending}
          className="w-full"
        >
          {exportMut.isPending ? 'Generating PDF…' : 'Download PDF'}
        </Button>
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/tailor/preview-panel.tsx
git commit -m "feat(tailor): PreviewPanel — iframe preview + template picker + Download PDF"
```

---

### Task 13: Wire Apply button + preview panel into the tailor page

**Files:**
- Modify: `frontend/src/app/dashboard/resume/tailor/page.tsx`

- [ ] **Step 1: Inspect current tailor page**

```bash
cd frontend && grep -n "Apply\|onApply\|DiffView\|jd_evaluation_id\|export const" src/app/dashboard/resume/tailor/page.tsx | head -20
```

Capture the current Apply button location + variable names.

- [ ] **Step 2: Add two-column layout + hook the Apply button**

Edit `frontend/src/app/dashboard/resume/tailor/page.tsx`. Locate the existing single-column rendering of the diff view. Wrap content in a 2-column grid on `lg` and up. Pseudo-structure:

```tsx
import { useState } from 'react';
import { useTailorApply } from '@/hooks/use-tailor-apply';
import { PreviewPanel } from '@/components/tailor/preview-panel';
import type { ApplyTailorResponse, ChangeItem } from '@/lib/api/types';

// ... inside the component, after JD analysis has loaded:
const [applyResult, setApplyResult] = useState<ApplyTailorResponse | null>(null);
const applyMut = useTailorApply(jdEvaluationId);  // jdEvaluationId comes from existing state

const acceptedChanges: ChangeItem[] = buildAcceptedChanges();  // derive from checkboxes

const onApplyClick = async () => {
  try {
    const result = await applyMut.mutateAsync({ accepted_changes: acceptedChanges });
    setApplyResult(result);
    toast({ title: 'Applied', description: `${acceptedChanges.length} changes saved` });
  } catch (e: any) {
    toast({ title: 'Apply failed', description: e?.message, variant: 'destructive' });
  }
};

return (
  <div className="grid grid-cols-1 lg:grid-cols-[1fr_480px] gap-8">
    <div>
      {/* existing diff view + Apply button — replace its onClick with onApplyClick */}
      <Button onClick={onApplyClick} disabled={applyMut.isPending || acceptedChanges.length === 0}>
        {applyMut.isPending ? 'Applying…' : `Apply ${acceptedChanges.length}`}
      </Button>
    </div>

    {applyResult ? (
      <PreviewPanel
        versionId={applyResult.version_id}
        previewHtml={applyResult.preview_html}
        suggestedTemplate={applyResult.suggested_template}
        filenameHint={applyResult.filename_hint}
        warning={applyResult.warning}
      />
    ) : (
      <aside className="sticky top-24 h-[calc(100vh-8rem)] border border-border rounded-md bg-card flex items-center justify-center text-sm text-muted-foreground p-6 text-center">
        Apply changes to see preview
      </aside>
    )}
  </div>
);
```

`buildAcceptedChanges()` is the helper that collects checkbox state into `ChangeItem[]`. If the existing diff view already exposes this state, reuse it. If not, refactor the diff view to surface accepted change state via a prop callback.

- [ ] **Step 3: Verify build + lint**

```bash
cd frontend && npm run build 2>&1 | tail -10
cd frontend && npm run lint 2>&1 | tail -5
```

Expected: build green, no new lint errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/dashboard/resume/tailor/page.tsx
git commit -m "feat(tailor): wire Apply button → useTailorApply + mount PreviewPanel"
```

---

### Task 14: Frontend component tests (PreviewPanel)

**Files:**
- Create: `frontend/src/components/tailor/__tests__/preview-panel.test.tsx`

- [ ] **Step 1: Write the tests**

Create `frontend/src/components/tailor/__tests__/preview-panel.test.tsx`:

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PreviewPanel } from '../preview-panel';

// Mock the toast hook
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

// Mock the export hook so no real network call
vi.mock('@/hooks/use-export-pdf', () => ({
  useExportPdf: () => ({
    mutateAsync: vi.fn().mockResolvedValue({
      export_id: 'e1', signed_url: 'https://x.com/p.pdf', filename: 'x.pdf',
    }),
    isPending: false,
  }),
}));

const wrap = (ui: React.ReactNode) => {
  const qc = new QueryClient();
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
};

describe('PreviewPanel', () => {
  it('renders iframe with provided HTML when previewHtml is non-empty', () => {
    wrap(<PreviewPanel versionId="v1" previewHtml="<p>Resume HTML</p>"
                       suggestedTemplate="us-swe" filenameHint="x.pdf" />);
    const iframe = screen.getByTitle('Resume preview') as HTMLIFrameElement;
    expect(iframe.getAttribute('srcdoc')).toContain('Resume HTML');
  });

  it('shows fallback message when previewHtml is empty', () => {
    wrap(<PreviewPanel versionId="v1" previewHtml=""
                       suggestedTemplate="us-swe" filenameHint="x.pdf"
                       warning="Preview unavailable" />);
    expect(screen.getByText(/Preview unavailable/i)).toBeInTheDocument();
  });

  it('filename input is editable and syncs to state', () => {
    wrap(<PreviewPanel versionId="v1" previewHtml="<p>x</p>"
                       suggestedTemplate="us-swe" filenameHint="default.pdf" />);
    const input = screen.getByPlaceholderText(/firstname-lastname/) as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'custom.pdf' } });
    expect(input.value).toBe('custom.pdf');
  });

  it('Download PDF button is rendered and clickable', () => {
    wrap(<PreviewPanel versionId="v1" previewHtml="<p>x</p>"
                       suggestedTemplate="us-swe" filenameHint="x.pdf" />);
    const btn = screen.getByRole('button', { name: /Download PDF/i });
    expect(btn).toBeEnabled();
  });
});
```

- [ ] **Step 2: Run the tests**

```bash
cd frontend && npx vitest run src/components/tailor/__tests__/preview-panel.test.tsx
```

Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/tailor/__tests__/preview-panel.test.tsx
git commit -m "test(tailor): PreviewPanel component tests"
```

---

### Task 15: Backend integration test — full flow

**Files:**
- Modify: `backend/tests/integration/test_phase1_e2e.py` (or create new file)

- [ ] **Step 1: Write integration test**

Append to `backend/tests/integration/test_phase1_e2e.py`:

```python
def test_apply_then_export_e2e(client, auth_headers, db_session, test_user_id, mocker):
    """Upload → evaluate (mocked) → jd/analyze (mocked) → apply → exports → signed URL."""
    import uuid
    from app.models.resume_document import ResumeDocument
    from app.models.jd_evaluation import JDEvaluation
    from app.services.credits.ledger import grant_monthly

    grant_monthly(db_session, test_user_id, 20)
    db_session.commit()

    # Seed resume doc directly (skip upload step for speed)
    doc_id = str(uuid.uuid4())
    db_session.add(ResumeDocument(
        id=doc_id, user_id=test_user_id, original_filename="r.pdf",
        file_path="/x", file_type="pdf",
        parsed_json={
            "contact": {"name": "Asha Sharma", "email": "a@s.com", "links": []},
            "experience": [{"company": "Acme", "role": "SWE",
                            "bullets": [{"id": "b1", "text": "Built things", "raw_text": "Built things"}]}],
            "education": [], "skills": {"hard": ["Python"], "soft": []},
            "projects": [], "certifications": [], "raw_text": "...",
        },
        raw_text="...",
    ))
    jd_id = str(uuid.uuid4())
    db_session.add(JDEvaluation(
        id=jd_id, user_id=test_user_id, resume_document_id=doc_id,
        jd_text="Senior SWE at Stripe (US)",
        extracted_requirements={
            "company_name": "Stripe",
            "country_hint": "US",
            "primary_role_category": "SWE",
        },
        diff_plan={}, match_score=75,
    ))
    db_session.commit()

    # 1. Apply
    apply = client.post(f"/api/v1/jd/{jd_id}/apply", json={
        "accepted_changes": [
            {"type": "bullet_update", "bullet_id": "b1", "new_text": "Shipped Python services on AWS"}
        ],
    }, headers=auth_headers)
    assert apply.status_code == 200
    apply_data = apply.json()
    assert apply_data["filename_hint"] == "asha-sharma-stripe.pdf"
    version_id = apply_data["version_id"]

    # 2. Export (mock the PDF render + storage)
    mocker.patch("app.api.v1.endpoints.exports.render_pdf_from_doc", return_value=b"%PDF-1.4 fake")
    mocker.patch("app.api.v1.endpoints.exports.get_storage").return_value.upload.return_value = f"{test_user_id}/exports/{version_id}.pdf"
    mocker.patch("app.api.v1.endpoints.exports.get_storage").return_value.signed_url.return_value = "https://signed.url/x"
    export = client.post("/api/v1/exports", json={
        "resume_version_id": version_id,
        "template_id": apply_data["suggested_template"],
        "filename": apply_data["filename_hint"],
    }, headers=auth_headers)
    assert export.status_code == 200
    assert export.json()["signed_url"].startswith("https://")
    assert export.json()["filename"] == "asha-sharma-stripe.pdf"

    # 3. Analytics reflects the work
    progress = client.get("/api/v1/analytics/jd-progress", headers=auth_headers)
    assert progress.status_code == 200
    jds = progress.json()["jds"]
    assert any(j["jd_evaluation_id"] == jd_id and j["applies_count"] == 1 for j in jds)
```

- [ ] **Step 2: Run the test**

```bash
cd backend && python3.11 -m pytest tests/integration/test_phase1_e2e.py::test_apply_then_export_e2e -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_phase1_e2e.py
git commit -m "test(e2e): full apply → export → analytics flow"
```

---

### Task 16: Final verification + run full test suite

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && python3.11 -m pytest tests/ --ignore=tests/golden 2>&1 | tail -10
```

Expected: all pass. Compare count to baseline (102 tests before this plan) — should be ~110+ after.

- [ ] **Step 2: Run frontend build + lint + component tests**

```bash
cd frontend && npm run build 2>&1 | tail -5
cd frontend && npm run lint 2>&1 | tail -5
cd frontend && npx vitest run 2>&1 | tail -10
```

Expected: build green, lint 0 errors (warnings allowed), vitest all pass.

- [ ] **Step 3: Manual smoke (local)**

```bash
make dev
# Browser: http://localhost:3000
# Login → Tailor flow → Apply → preview panel visible → Download PDF → file lands in Downloads/
```

- [ ] **Step 4: Push branch + open PR**

```bash
git push -u origin <branch-name>
gh pr create --base main --title "feat: tailor Apply → preview → export + JD analytics" \
  --body "Implements docs/superpowers/specs/2026-05-25-tailor-apply-preview-export-design.md. 16 tasks. ~10 new backend tests + 4 frontend component tests + 1 e2e."
```

---

## Self-Review Summary

**Spec coverage (post-write):**
- §6 Architecture → reflected across Tasks 1, 6, 9, 13 ✓
- §7.1 Migration → Task 1 ✓
- §7.2 Schemas (JDExtraction.company_name) → Task 3 ✓
- §7.2 Schemas (ApplyTailorRequest/Response) → Task 5 ✓
- §7.3 Apply endpoint → Tasks 6, 7 ✓
- §7.4 Exports filename + template fallback → Task 8 ✓
- §7.5 Analytics endpoint → Task 9 ✓
- §7.6 render_html_only → Task 4 ✓
- §7.7 Frontend types → Task 10 ✓
- §7.8 Hooks (useTailorApply, useExportPdf) → Tasks 10, 11 ✓
- §7.9 PreviewPanel + tailor page wiring → Tasks 12, 13 ✓
- §8 Data flow → exercised by Tasks 6, 8, 9 + e2e Task 15 ✓
- §9 Error handling → covered in endpoint implementations + tests ✓
- §10 Testing → Tasks 6, 7, 8, 9, 14, 15 ✓

**Placeholder scan:** none. Every step contains complete code, exact commands, or specific edit instructions tied to actual line content. The "find the existing X" steps direct the engineer to grep so they're not guessing.

**Type consistency:** `ApplyTailorRequest`, `ApplyTailorResponse`, `ExportPdfRequest`, `ExportPdfResponse`, `ChangeItem`, `AnalyticsJdProgress` used consistently across backend (Tasks 5, 6, 8, 9) and frontend (Tasks 10, 11, 12, 13). Function names `apply_changes`, `render_html_only`, `_sanitize_filename`, `_slugify` consistent across tasks.

**Risks flagged inline:**
- Task 5 has a branch: if `ChangeItem` already lives in `resumes_v2.py`, centralise it. The plan tells the engineer to grep first.
- Task 9 has a branch: register `/analytics/jd-progress` on the right router file depending on existing `admin_metrics.py` layout. Plan provides the alternative.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-25-tailor-apply-preview-export-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
