# Prism Pro — Phase 2: PDF Render Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the PDF export pipeline — turn a `ResumeDocument` (or accepted `ResumeVersion`) into a recruiter-grade PDF via 6 country/role HTML+CSS templates rendered by headless Chromium, uploaded to Supabase Storage, returned as a signed URL, with credit debit and refund-on-failure.

**Architecture:** A FastAPI endpoint debits 1 credit, picks one of 6 Jinja2 templates (`us|in / swe|ds|pm`), renders to PDF via Playwright (headless Chromium, single shared browser instance), uploads to Supabase Storage, persists a `resume_exports` row, and returns a signed download URL. Templates share base/typography/print CSS partials; country differences (US 1-page action-first vs IN 2-page scope-aware) are baked into structure, not runtime config. The renderer has a 15s timeout with one retry and falls back to `us/swe` on template render failure. Spec §7.7.

**Tech Stack:** Python 3.11, FastAPI, Playwright (Python, already in `backend/requirements.txt`), Jinja2, supabase-py 2.3.0, Alembic, SQLAlchemy 2, Pydantic 2, pytest, syrupy for snapshot.

**Spec source of truth:** `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md` §6, §7.7, §8.1 step 12, §9 (Puppeteer-row), §10 PDF renderer.

**Note on Playwright vs Puppeteer:** The spec text says "Puppeteer." We use **Playwright** (Python) because (a) it's already in `requirements.txt`, (b) it drives the same Chromium engine, (c) it has first-class Python bindings — Puppeteer would require Node sidecar. Functional output is identical.

---

## File Structure

**New files:**
- `backend/migrations/versions/2026_05_20_add_resume_exports.py` — Alembic migration for the `resume_exports` table.
- `backend/app/models/resume_export.py` — `ResumeExport` SQLAlchemy model.
- `backend/app/schemas/resume_export.py` — `ExportRequest`, `ExportResponse`, `Country`, `RoleTemplate` enums. (New file rather than appending to `schemas/resume.py` — see BLOCKERS.md Issue 10.)
- `backend/app/core/supabase_storage.py` — supabase-py client singleton + `upload_pdf()` / `signed_url()` helpers.
- `backend/app/services/pdf/__init__.py` — package marker.
- `backend/app/services/pdf/template_engine.py` — Jinja2 environment loader + `pick_template(country, role)` helper + `render_html(doc, country, role)`.
- `backend/app/services/pdf/renderer.py` — Playwright wrapper: shared browser singleton, `render_pdf(html, timeout_s=15) -> bytes` with one retry on timeout.
- `backend/app/services/pdf/templates/shared/_base.css` — page reset, sizing.
- `backend/app/services/pdf/templates/shared/_typography.css` — font stacks (Inter for US, Inter + IBM Plex for IN headings), sizes, weights.
- `backend/app/services/pdf/templates/shared/_print.css` — `@page` rules, margins, page-break behavior.
- `backend/app/services/pdf/templates/us/swe.html` — US SWE template (action-first, 1-page target).
- `backend/app/services/pdf/templates/us/ds.html` — US DS template.
- `backend/app/services/pdf/templates/us/pm.html` — US PM template.
- `backend/app/services/pdf/templates/in/swe.html` — IN SWE template (scope-aware, 2-page tolerated).
- `backend/app/services/pdf/templates/in/ds.html` — IN DS template.
- `backend/app/services/pdf/templates/in/pm.html` — IN PM template.
- `backend/app/api/v1/endpoints/exports.py` — `POST /api/v1/exports`, `GET /api/v1/exports/{id}`.
- `backend/tests/services/pdf/__init__.py` — pytest package marker.
- `backend/tests/services/pdf/test_template_engine.py`
- `backend/tests/services/pdf/test_renderer.py`
- `backend/tests/services/pdf/test_templates_smoke.py`
- `backend/tests/services/pdf/test_renderer_perf.py`
- `backend/tests/api/test_exports_endpoint.py`
- `backend/tests/integration/test_export_e2e.py`
- `backend/tests/fixtures/resume_doc_json.py` — shared fixture builder for `ResumeDocumentJSON` instances used across template/render tests.

**Modified files:**
- `backend/app/api/v1/api.py` — register `exports.router`.
- `backend/app/api/v1/endpoints/__init__.py` — export new module (only if file currently lists endpoints explicitly).
- `backend/app/models/__init__.py` — register `ResumeExport`.
- `backend/app/core/config.py` — add `SUPABASE_STORAGE_BUCKET` setting (default `"resume-exports"`) and `PDF_RENDER_TIMEOUT_S` (default `15`).
- `backend/requirements.txt` — no changes (playwright + jinja2 + supabase already pinned).
- `README.md` — append Phase 2 endpoints under the existing Phase 1 endpoint list.

---

## Phase 2 — PDF Render

### Task 0: Verify dependencies + install Playwright Chromium

**Files:**
- None (environment setup).

- [ ] **Step 1: Confirm playwright + supabase + jinja2 pinned**

Run:
```bash
grep -E "^(playwright|supabase|jinja2)" backend/requirements.txt
```
Expected (any version is fine, presence is what matters):
```
playwright==1.40.0
supabase==2.3.0
jinja2==3.1.2
```

- [ ] **Step 2: Install browsers**

Run from repo root:
```bash
cd backend && python -m playwright install chromium
```
Expected: download completes, no errors. (CI must run this step too — add to CI workflow in Task 22.)

- [ ] **Step 3: Smoke-test Playwright import + browser launch**

Run:
```bash
cd backend && python -c "from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    print('ok', b.version)
    b.close()"
```
Expected: `ok <version>` and exit 0.

- [ ] **Step 4: Commit**

```bash
git status
git commit --allow-empty -m "chore(phase-2): verify playwright + chromium ready"
```

---

### Task 1: Alembic migration — `resume_exports` table

**Files:**
- Create: `backend/migrations/versions/2026_05_20_add_resume_exports.py`

- [ ] **Step 1: Write the migration**

```python
"""add resume_exports table for phase 2 pdf render

Revision ID: 2026_05_20_phase2
Revises: 2026_05_19_phase1
Create Date: 2026-05-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "2026_05_20_phase2"
down_revision = "2026_05_19_phase1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resume_exports",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("resume_document_id", sa.String(), sa.ForeignKey("resume_documents.id"), nullable=False, index=True),
        sa.Column("resume_version_id", sa.String(), sa.ForeignKey("resume_versions.id"), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=False),     # 'US' | 'IN'
        sa.Column("role_template", sa.String(length=8), nullable=False),  # 'swe' | 'ds' | 'pm'
        sa.Column("storage_path", sa.String(), nullable=False),        # bucket-relative path
        sa.Column("status", sa.String(length=16), nullable=False, server_default="succeeded"),
        sa.Column("render_ms", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("resume_exports")
```

- [ ] **Step 2: Run migration against the test SQLite DB**

```bash
cd backend && alembic upgrade head
```
Expected: `Running upgrade 2026_05_19_phase1 -> 2026_05_20_phase2, add resume_exports table for phase 2 pdf render`.

- [ ] **Step 3: Confirm downgrade is reversible**

```bash
cd backend && alembic downgrade -1 && alembic upgrade head
```
Expected: both commands exit 0.

- [ ] **Step 4: Commit**

```bash
git add backend/migrations/versions/2026_05_20_add_resume_exports.py
git commit -m "feat(db): resume_exports table for phase 2 pdf renders"
```

---

### Task 2: SQLAlchemy model — `ResumeExport`

**Files:**
- Create: `backend/app/models/resume_export.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write a failing import test**

Create `backend/tests/models/test_resume_export_model.py`:
```python
def test_resume_export_columns():
    from app.models.resume_export import ResumeExport
    cols = {c.name for c in ResumeExport.__table__.columns}
    assert cols >= {
        "id", "user_id", "resume_document_id", "resume_version_id",
        "country", "role_template", "storage_path", "status",
        "render_ms", "file_size_bytes", "error_message", "created_at",
    }
```

- [ ] **Step 2: Run test — FAIL**

```bash
cd backend && pytest tests/models/test_resume_export_model.py -v
```
Expected: `ModuleNotFoundError: No module named 'app.models.resume_export'`.

- [ ] **Step 3: Write the model**

```python
# backend/app/models/resume_export.py
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.base_class import Base


class ResumeExport(Base):
    __tablename__ = "resume_exports"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    resume_document_id = Column(String, ForeignKey("resume_documents.id"), nullable=False, index=True)
    resume_version_id = Column(String, ForeignKey("resume_versions.id"), nullable=True)
    country = Column(String(2), nullable=False)
    role_template = Column(String(8), nullable=False)
    storage_path = Column(String, nullable=False)
    status = Column(String(16), nullable=False, default="succeeded")
    render_ms = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 4: Register in models package**

Open `backend/app/models/__init__.py`. If existing models are re-exported there, add `from app.models.resume_export import ResumeExport  # noqa: F401`. If the file is empty (only used for package-discovery), leave as is — SQLAlchemy will pick up the model when the module is imported by routes.

- [ ] **Step 5: Re-run test — PASS**

```bash
cd backend && pytest tests/models/test_resume_export_model.py -v
```
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/resume_export.py backend/app/models/__init__.py backend/tests/models/test_resume_export_model.py
git commit -m "feat(model): ResumeExport SQLAlchemy model"
```

---

### Task 3: Pydantic schemas — `ExportRequest`, `ExportResponse`, enums

**Files:**
- Create: `backend/app/schemas/resume_export.py`
- Create: `backend/tests/schemas/test_resume_export_schema.py`

- [ ] **Step 1: Write failing schema tests**

```python
# backend/tests/schemas/test_resume_export_schema.py
import pytest
from pydantic import ValidationError


def test_export_request_accepts_known_country_and_role():
    from app.schemas.resume_export import ExportRequest
    r = ExportRequest(
        resume_document_id="doc-1",
        country="US",
        role_template="swe",
    )
    assert r.country == "US"
    assert r.role_template == "swe"
    assert r.resume_version_id is None


def test_export_request_rejects_unknown_country():
    from app.schemas.resume_export import ExportRequest
    with pytest.raises(ValidationError):
        ExportRequest(resume_document_id="doc-1", country="UK", role_template="swe")


def test_export_request_rejects_unknown_role():
    from app.schemas.resume_export import ExportRequest
    with pytest.raises(ValidationError):
        ExportRequest(resume_document_id="doc-1", country="US", role_template="designer")


def test_export_response_shape():
    from app.schemas.resume_export import ExportResponse
    r = ExportResponse(
        export_id="exp-1",
        download_url="https://x/y.pdf",
        expires_at="2026-05-27T00:00:00Z",
        country="IN",
        role_template="ds",
    )
    assert r.export_id == "exp-1"
```

- [ ] **Step 2: Run — FAIL**

```bash
cd backend && pytest tests/schemas/test_resume_export_schema.py -v
```
Expected: 4 errors / fails (module not found).

- [ ] **Step 3: Write the schema**

```python
# backend/app/schemas/resume_export.py
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Country(str, Enum):
    US = "US"
    IN = "IN"


class RoleTemplate(str, Enum):
    SWE = "swe"
    DS = "ds"
    PM = "pm"


class ExportRequest(BaseModel):
    resume_document_id: str = Field(..., min_length=1)
    resume_version_id: Optional[str] = None
    country: Country
    role_template: RoleTemplate


class ExportResponse(BaseModel):
    export_id: str
    download_url: str
    expires_at: datetime
    country: Country
    role_template: RoleTemplate
```

- [ ] **Step 4: Re-run — PASS**

```bash
cd backend && pytest tests/schemas/test_resume_export_schema.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/resume_export.py backend/tests/schemas/test_resume_export_schema.py
git commit -m "feat(schema): ExportRequest/Response + Country/RoleTemplate enums"
```

---

### Task 4: Supabase Storage client + helpers

**Files:**
- Modify: `backend/app/core/config.py`
- Create: `backend/app/core/supabase_storage.py`
- Create: `backend/tests/core/test_supabase_storage.py`

- [ ] **Step 1: Add config knobs**

Open `backend/app/core/config.py`. Inside the `Settings` class (next to the other Supabase-related settings), add:

```python
    SUPABASE_STORAGE_BUCKET: str = "resume-exports"
    SUPABASE_SIGNED_URL_TTL_SECONDS: int = 60 * 60 * 24 * 7  # 7 days
    PDF_RENDER_TIMEOUT_S: int = 15
```

- [ ] **Step 2: Write failing client tests**

```python
# backend/tests/core/test_supabase_storage.py
from unittest.mock import MagicMock, patch


def test_upload_pdf_calls_supabase_storage(monkeypatch):
    from app.core import supabase_storage as ss
    fake_client = MagicMock()
    fake_bucket = MagicMock()
    fake_client.storage.from_.return_value = fake_bucket
    monkeypatch.setattr(ss, "_get_client", lambda: fake_client)

    path = ss.upload_pdf(b"%PDF-fake", "user-1/exp-1.pdf")
    fake_client.storage.from_.assert_called_once_with(ss.settings.SUPABASE_STORAGE_BUCKET)
    fake_bucket.upload.assert_called_once()
    args, kwargs = fake_bucket.upload.call_args
    # path is first positional; file is second; options carry content-type
    assert "user-1/exp-1.pdf" in args
    assert path == "user-1/exp-1.pdf"


def test_signed_url_returns_url(monkeypatch):
    from app.core import supabase_storage as ss
    fake_client = MagicMock()
    fake_bucket = MagicMock()
    fake_bucket.create_signed_url.return_value = {"signedURL": "https://x/file.pdf?token=abc"}
    fake_client.storage.from_.return_value = fake_bucket
    monkeypatch.setattr(ss, "_get_client", lambda: fake_client)

    url = ss.signed_url("user-1/exp-1.pdf", ttl_seconds=3600)
    assert url == "https://x/file.pdf?token=abc"
    fake_bucket.create_signed_url.assert_called_once_with("user-1/exp-1.pdf", 3600)
```

- [ ] **Step 3: Run — FAIL**

```bash
cd backend && pytest tests/core/test_supabase_storage.py -v
```
Expected: `ModuleNotFoundError: No module named 'app.core.supabase_storage'`.

- [ ] **Step 4: Write the module**

```python
# backend/app/core/supabase_storage.py
"""Supabase Storage client + PDF helpers for Phase 2 exports.

We deliberately keep this small: a lazy singleton client, an upload helper,
and a signed-URL helper. The client is constructed from SUPABASE_URL +
SUPABASE_SERVICE_ROLE_KEY (already in app config).
"""
from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from app.core.config import settings


@lru_cache(maxsize=1)
def _get_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def upload_pdf(pdf_bytes: bytes, storage_path: str) -> str:
    """Upload PDF bytes to the configured bucket. Returns the storage path."""
    bucket = _get_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET)
    bucket.upload(
        storage_path,
        pdf_bytes,
        {"content-type": "application/pdf", "upsert": "true"},
    )
    return storage_path


def signed_url(storage_path: str, ttl_seconds: Optional[int] = None) -> str:
    """Return a signed download URL for the stored PDF."""
    ttl = ttl_seconds if ttl_seconds is not None else settings.SUPABASE_SIGNED_URL_TTL_SECONDS
    bucket = _get_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET)
    resp = bucket.create_signed_url(storage_path, ttl)
    # supabase-py returns the URL under either "signedURL" or "signed_url" depending on version.
    return resp.get("signedURL") or resp["signed_url"]
```

> **Why:** `supabase-py` 2.3 returns the field as `signedURL`, but newer minor versions started returning `signed_url`. Handle both so a routine bump doesn't break exports.

- [ ] **Step 5: Re-run — PASS**

```bash
cd backend && pytest tests/core/test_supabase_storage.py -v
```
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/config.py backend/app/core/supabase_storage.py backend/tests/core/test_supabase_storage.py
git commit -m "feat(storage): supabase storage client + signed-url helper"
```

---

### Task 5: Template engine — Jinja2 env + `pick_template` + `render_html`

**Files:**
- Create: `backend/app/services/pdf/__init__.py` (empty marker)
- Create: `backend/app/services/pdf/template_engine.py`
- Create: `backend/tests/fixtures/resume_doc_json.py`
- Create: `backend/tests/services/pdf/__init__.py` (empty marker)
- Create: `backend/tests/services/pdf/test_template_engine.py`

- [ ] **Step 1: Write the shared resume fixture builder**

```python
# backend/tests/fixtures/resume_doc_json.py
from app.schemas.resume import (
    Bullet, Contact, EducationEntry, ExperienceEntry,
    ProjectEntry, ResumeDocumentJSON, Skills,
)


def make_resume(name: str = "Jane Doe") -> ResumeDocumentJSON:
    return ResumeDocumentJSON(
        contact=Contact(
            name=name,
            email="jane@example.com",
            phone="+1 555-0100",
            links=["https://github.com/janedoe"],
        ),
        summary="SWE with 5 years building distributed systems.",
        experience=[
            ExperienceEntry(
                company="Acme",
                role="Senior SWE",
                dates="2022-2026",
                location="SF, CA",
                bullets=[
                    Bullet(id="b1", text="Cut p99 latency 38% by rewriting the auth path.", raw_text="..."),
                    Bullet(id="b2", text="Mentored 4 engineers; 3 promoted within 12 months.", raw_text="..."),
                ],
            ),
        ],
        education=[EducationEntry(school="State U", degree="BS CS", dates="2017-2021", gpa="3.8")],
        skills=Skills(hard=["Python", "Postgres", "AWS"], soft=["Mentoring"]),
        projects=[ProjectEntry(name="OSS lib", bullets=[Bullet(id="p1", text="500+ GitHub stars.", raw_text="...")])],
        raw_text="…",
    )
```

> **Why share the fixture:** every template test and the renderer smoke test needs the same `ResumeDocumentJSON`. Drift between copies will produce false-positive snapshot diffs.

- [ ] **Step 2: Write failing template-engine tests**

```python
# backend/tests/services/pdf/test_template_engine.py
import pytest
from tests.fixtures.resume_doc_json import make_resume


def test_pick_template_returns_path_for_known_combo():
    from app.services.pdf.template_engine import pick_template
    assert pick_template("US", "swe").endswith("us/swe.html")
    assert pick_template("IN", "pm").endswith("in/pm.html")


def test_pick_template_raises_on_unknown():
    from app.services.pdf.template_engine import pick_template
    with pytest.raises(ValueError):
        pick_template("UK", "swe")
    with pytest.raises(ValueError):
        pick_template("US", "designer")


def test_render_html_contains_contact_name_and_bullets():
    from app.services.pdf.template_engine import render_html
    doc = make_resume(name="Jane Doe")
    html = render_html(doc, country="US", role="swe")
    assert "Jane Doe" in html
    assert "Cut p99 latency 38%" in html
    assert "<html" in html.lower()


def test_render_html_escapes_html_in_user_content():
    from app.services.pdf.template_engine import render_html
    doc = make_resume(name="<script>alert(1)</script>")
    html = render_html(doc, country="US", role="swe")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
```

> **Why the XSS test:** templates render user-supplied content. Jinja2 autoescape MUST be on (default off for `Environment()`); the test pins the requirement so a future refactor can't silently turn it off.

- [ ] **Step 3: Run — FAIL**

```bash
cd backend && pytest tests/services/pdf/test_template_engine.py -v
```
Expected: 4 fails / errors (module missing).

- [ ] **Step 4: Implement the engine**

```python
# backend/app/services/pdf/__init__.py
```
(Empty — package marker.)

```python
# backend/app/services/pdf/template_engine.py
"""Jinja2 environment + template selection for Phase 2 PDF render.

Templates live alongside this module under templates/{country}/{role}.html.
Shared CSS is served via Jinja's static_url filter using file:// URLs so
Chromium loads them deterministically without a webserver.
"""
from pathlib import Path
from typing import Literal

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.schemas.resume import ResumeDocumentJSON

TEMPLATES_DIR = Path(__file__).parent / "templates"

_VALID_COUNTRIES = {"US", "IN"}
_VALID_ROLES = {"swe", "ds", "pm"}

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def pick_template(country: str, role: str) -> str:
    """Return the template path relative to TEMPLATES_DIR, e.g. 'us/swe.html'."""
    if country not in _VALID_COUNTRIES:
        raise ValueError(f"Unknown country: {country}")
    if role not in _VALID_ROLES:
        raise ValueError(f"Unknown role: {role}")
    return f"{country.lower()}/{role}.html"


def _shared_css_url(filename: str) -> str:
    return (TEMPLATES_DIR / "shared" / filename).as_uri()


def render_html(
    doc: ResumeDocumentJSON,
    country: Literal["US", "IN"],
    role: Literal["swe", "ds", "pm"],
) -> str:
    template_path = pick_template(country, role)
    template = _env.get_template(template_path)
    return template.render(
        doc=doc,
        country=country,
        role=role,
        base_css=_shared_css_url("_base.css"),
        type_css=_shared_css_url("_typography.css"),
        print_css=_shared_css_url("_print.css"),
    )
```

- [ ] **Step 5: Re-run — three should pass, one (render_html) still fails until templates exist**

```bash
cd backend && pytest tests/services/pdf/test_template_engine.py -v
```
Expected: `test_pick_template_*` pass; `test_render_html_*` fail with `TemplateNotFound: us/swe.html`.

- [ ] **Step 6: Commit the engine — templates land in Tasks 6–12**

```bash
git add backend/app/services/pdf/__init__.py backend/app/services/pdf/template_engine.py backend/tests/fixtures/resume_doc_json.py backend/tests/services/pdf/__init__.py backend/tests/services/pdf/test_template_engine.py
git commit -m "feat(pdf): Jinja2 template engine + pick_template helper"
```

---

### Task 6: Shared CSS partials

**Files:**
- Create: `backend/app/services/pdf/templates/shared/_base.css`
- Create: `backend/app/services/pdf/templates/shared/_typography.css`
- Create: `backend/app/services/pdf/templates/shared/_print.css`

> **Why one task for all three:** the partials are tiny, deeply interdependent, and templates downstream import all three together. Splitting would force template tasks to commit broken HTML.

- [ ] **Step 1: Write `_base.css`**

```css
/* backend/app/services/pdf/templates/shared/_base.css */
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: white; color: #1a1a1a; }
a { color: inherit; text-decoration: none; }
ul { margin: 0; padding-left: 1.1em; }
li { margin: 0 0 0.15em 0; }
.section { margin-top: 0.9em; }
.section h2 {
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 1px solid #333;
  padding-bottom: 0.1em;
}
.row { display: flex; justify-content: space-between; gap: 1em; }
.muted { color: #555; }
```

- [ ] **Step 2: Write `_typography.css`**

```css
/* backend/app/services/pdf/templates/shared/_typography.css */
:root {
  --font-sans: "Inter", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --font-serif-headings-in: "IBM Plex Serif", "Times New Roman", Times, serif;
  --fs-name: 22pt;
  --fs-h2: 11pt;
  --fs-body: 10pt;
  --fs-small: 9pt;
  --line: 1.35;
}
body { font-family: var(--font-sans); font-size: var(--fs-body); line-height: var(--line); }
h1 { font-size: var(--fs-name); margin: 0; font-weight: 700; }
h2 { font-size: var(--fs-h2); margin: 0.6em 0 0.3em; font-weight: 700; }
.summary, .meta { font-size: var(--fs-small); }
.country-IN h2 { font-family: var(--font-serif-headings-in); letter-spacing: 0.02em; }
```

- [ ] **Step 3: Write `_print.css`**

```css
/* backend/app/services/pdf/templates/shared/_print.css */
@page {
  size: Letter;     /* US default; IN templates override via @page in their own <style> */
  margin: 0.5in 0.55in;
}
@media print {
  body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
}
.no-break { break-inside: avoid; page-break-inside: avoid; }
.experience-item { break-inside: avoid; page-break-inside: avoid; margin-bottom: 0.5em; }
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/pdf/templates/shared/
git commit -m "feat(pdf): shared base/typography/print CSS partials"
```

---

### Task 7: US-SWE template

**Files:**
- Create: `backend/app/services/pdf/templates/us/swe.html`
- Modify: `backend/tests/services/pdf/test_template_engine.py` (already covers render)

- [ ] **Step 1: Write the template**

```html
{# backend/app/services/pdf/templates/us/swe.html — US SWE: action-first, 1-page target #}
<!doctype html>
<html lang="en" class="country-US role-swe">
<head>
  <meta charset="utf-8">
  <title>{{ doc.contact.name }} — Resume</title>
  <link rel="stylesheet" href="{{ base_css }}">
  <link rel="stylesheet" href="{{ type_css }}">
  <link rel="stylesheet" href="{{ print_css }}">
</head>
<body>
  <header>
    <h1>{{ doc.contact.name }}</h1>
    <div class="meta">
      {% if doc.contact.email %}{{ doc.contact.email }}{% endif %}
      {% if doc.contact.phone %} · {{ doc.contact.phone }}{% endif %}
      {% for link in doc.contact.links %} · {{ link }}{% endfor %}
    </div>
  </header>

  {% if doc.summary %}
  <section class="section">
    <h2>Summary</h2>
    <p class="summary">{{ doc.summary }}</p>
  </section>
  {% endif %}

  <section class="section">
    <h2>Experience</h2>
    {% for exp in doc.experience %}
      <div class="experience-item">
        <div class="row">
          <strong>{{ exp.role }} · {{ exp.company }}</strong>
          <span class="muted">{{ exp.dates }}{% if exp.location %} · {{ exp.location }}{% endif %}</span>
        </div>
        <ul>
          {% for b in exp.bullets %}<li>{{ b.text }}</li>{% endfor %}
        </ul>
      </div>
    {% endfor %}
  </section>

  {% if doc.projects %}
  <section class="section">
    <h2>Projects</h2>
    {% for proj in doc.projects %}
      <div class="experience-item">
        <strong>{{ proj.name }}</strong>
        <ul>{% for b in proj.bullets %}<li>{{ b.text }}</li>{% endfor %}</ul>
      </div>
    {% endfor %}
  </section>
  {% endif %}

  <section class="section">
    <h2>Skills</h2>
    <p>{{ doc.skills.hard | join(", ") }}</p>
  </section>

  <section class="section">
    <h2>Education</h2>
    {% for ed in doc.education %}
      <div class="row">
        <strong>{{ ed.degree }} · {{ ed.school }}</strong>
        <span class="muted">{{ ed.dates }}{% if ed.gpa %} · GPA {{ ed.gpa }}{% endif %}</span>
      </div>
    {% endfor %}
  </section>
</body>
</html>
```

- [ ] **Step 2: Run the template-engine render test — PASS for US-SWE**

```bash
cd backend && pytest tests/services/pdf/test_template_engine.py::test_render_html_contains_contact_name_and_bullets tests/services/pdf/test_template_engine.py::test_render_html_escapes_html_in_user_content -v
```
Expected: both pass.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/pdf/templates/us/swe.html
git commit -m "feat(pdf): US-SWE template (action-first, 1-page)"
```

---

### Task 8: US-DS template

**Files:**
- Create: `backend/app/services/pdf/templates/us/ds.html`

- [ ] **Step 1: Write the template (Data Science focus — surface methods + scale)**

```html
{# backend/app/services/pdf/templates/us/ds.html — US DS: methods + scale up top #}
<!doctype html>
<html lang="en" class="country-US role-ds">
<head>
  <meta charset="utf-8">
  <title>{{ doc.contact.name }} — Resume</title>
  <link rel="stylesheet" href="{{ base_css }}">
  <link rel="stylesheet" href="{{ type_css }}">
  <link rel="stylesheet" href="{{ print_css }}">
</head>
<body>
  <header>
    <h1>{{ doc.contact.name }}</h1>
    <div class="meta">
      {% if doc.contact.email %}{{ doc.contact.email }}{% endif %}
      {% if doc.contact.phone %} · {{ doc.contact.phone }}{% endif %}
      {% for link in doc.contact.links %} · {{ link }}{% endfor %}
    </div>
  </header>

  {% if doc.summary %}
  <section class="section">
    <h2>Profile</h2>
    <p class="summary">{{ doc.summary }}</p>
  </section>
  {% endif %}

  <section class="section">
    <h2>Skills</h2>
    <p>{{ doc.skills.hard | join(" · ") }}</p>
  </section>

  <section class="section">
    <h2>Experience</h2>
    {% for exp in doc.experience %}
      <div class="experience-item">
        <div class="row">
          <strong>{{ exp.role }} — {{ exp.company }}</strong>
          <span class="muted">{{ exp.dates }}{% if exp.location %} · {{ exp.location }}{% endif %}</span>
        </div>
        <ul>{% for b in exp.bullets %}<li>{{ b.text }}</li>{% endfor %}</ul>
      </div>
    {% endfor %}
  </section>

  {% if doc.projects %}
  <section class="section">
    <h2>Selected Projects</h2>
    {% for proj in doc.projects %}
      <div class="experience-item">
        <strong>{{ proj.name }}</strong>
        <ul>{% for b in proj.bullets %}<li>{{ b.text }}</li>{% endfor %}</ul>
      </div>
    {% endfor %}
  </section>
  {% endif %}

  <section class="section">
    <h2>Education</h2>
    {% for ed in doc.education %}
      <div class="row">
        <strong>{{ ed.degree }} · {{ ed.school }}</strong>
        <span class="muted">{{ ed.dates }}{% if ed.gpa %} · GPA {{ ed.gpa }}{% endif %}</span>
      </div>
    {% endfor %}
  </section>
</body>
</html>
```

- [ ] **Step 2: Smoke-render via Python**

```bash
cd backend && python -c "
from tests.fixtures.resume_doc_json import make_resume
from app.services.pdf.template_engine import render_html
html = render_html(make_resume(), 'US', 'ds')
assert '<title>' in html and 'Skills' in html
print('ok')
"
```
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/pdf/templates/us/ds.html
git commit -m "feat(pdf): US-DS template"
```

---

### Task 9: US-PM template

**Files:**
- Create: `backend/app/services/pdf/templates/us/pm.html`

- [ ] **Step 1: Write the template (PM focus — outcomes + scope at the top of each role)**

```html
{# backend/app/services/pdf/templates/us/pm.html — US PM: outcome-first #}
<!doctype html>
<html lang="en" class="country-US role-pm">
<head>
  <meta charset="utf-8">
  <title>{{ doc.contact.name }} — Resume</title>
  <link rel="stylesheet" href="{{ base_css }}">
  <link rel="stylesheet" href="{{ type_css }}">
  <link rel="stylesheet" href="{{ print_css }}">
</head>
<body>
  <header>
    <h1>{{ doc.contact.name }}</h1>
    <div class="meta">
      {% if doc.contact.email %}{{ doc.contact.email }}{% endif %}
      {% if doc.contact.phone %} · {{ doc.contact.phone }}{% endif %}
      {% for link in doc.contact.links %} · {{ link }}{% endfor %}
    </div>
  </header>

  {% if doc.summary %}
  <section class="section">
    <h2>Profile</h2>
    <p class="summary">{{ doc.summary }}</p>
  </section>
  {% endif %}

  <section class="section">
    <h2>Experience</h2>
    {% for exp in doc.experience %}
      <div class="experience-item">
        <div class="row">
          <strong>{{ exp.role }} · {{ exp.company }}</strong>
          <span class="muted">{{ exp.dates }}{% if exp.location %} · {{ exp.location }}{% endif %}</span>
        </div>
        <ul>{% for b in exp.bullets %}<li>{{ b.text }}</li>{% endfor %}</ul>
      </div>
    {% endfor %}
  </section>

  <section class="section">
    <h2>Skills</h2>
    <p>{{ doc.skills.hard | join(" · ") }}</p>
  </section>

  <section class="section">
    <h2>Education</h2>
    {% for ed in doc.education %}
      <div class="row">
        <strong>{{ ed.degree }} · {{ ed.school }}</strong>
        <span class="muted">{{ ed.dates }}</span>
      </div>
    {% endfor %}
  </section>
</body>
</html>
```

- [ ] **Step 2: Smoke-render**

```bash
cd backend && python -c "
from tests.fixtures.resume_doc_json import make_resume
from app.services.pdf.template_engine import render_html
html = render_html(make_resume(), 'US', 'pm')
assert 'Profile' in html
print('ok')
"
```
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/pdf/templates/us/pm.html
git commit -m "feat(pdf): US-PM template"
```

---

### Task 10: IN-SWE template

**Files:**
- Create: `backend/app/services/pdf/templates/in/swe.html`

- [ ] **Step 1: Write the template (IN: scope-aware, 2-page tolerated, A4 paper)**

```html
{# backend/app/services/pdf/templates/in/swe.html — IN SWE: scope-aware, A4 #}
<!doctype html>
<html lang="en" class="country-IN role-swe">
<head>
  <meta charset="utf-8">
  <title>{{ doc.contact.name }} — Resume</title>
  <link rel="stylesheet" href="{{ base_css }}">
  <link rel="stylesheet" href="{{ type_css }}">
  <link rel="stylesheet" href="{{ print_css }}">
  <style>
    @page { size: A4; margin: 0.55in 0.55in; }
  </style>
</head>
<body>
  <header>
    <h1>{{ doc.contact.name }}</h1>
    <div class="meta">
      {% if doc.contact.email %}{{ doc.contact.email }}{% endif %}
      {% if doc.contact.phone %} · {{ doc.contact.phone }}{% endif %}
      {% for link in doc.contact.links %} · {{ link }}{% endfor %}
    </div>
  </header>

  {% if doc.summary %}
  <section class="section">
    <h2>Professional Summary</h2>
    <p class="summary">{{ doc.summary }}</p>
  </section>
  {% endif %}

  <section class="section">
    <h2>Professional Experience</h2>
    {% for exp in doc.experience %}
      <div class="experience-item">
        <div class="row">
          <strong>{{ exp.role }} · {{ exp.company }}</strong>
          <span class="muted">{{ exp.dates }}{% if exp.location %} · {{ exp.location }}{% endif %}</span>
        </div>
        <ul>{% for b in exp.bullets %}<li>{{ b.text }}</li>{% endfor %}</ul>
      </div>
    {% endfor %}
  </section>

  {% if doc.projects %}
  <section class="section">
    <h2>Key Projects</h2>
    {% for proj in doc.projects %}
      <div class="experience-item">
        <strong>{{ proj.name }}</strong>
        <ul>{% for b in proj.bullets %}<li>{{ b.text }}</li>{% endfor %}</ul>
      </div>
    {% endfor %}
  </section>
  {% endif %}

  <section class="section">
    <h2>Technical Skills</h2>
    <p>{{ doc.skills.hard | join(", ") }}</p>
  </section>

  <section class="section">
    <h2>Education</h2>
    {% for ed in doc.education %}
      <div class="row">
        <strong>{{ ed.degree }} · {{ ed.school }}</strong>
        <span class="muted">{{ ed.dates }}{% if ed.gpa %} · GPA {{ ed.gpa }}{% endif %}</span>
      </div>
    {% endfor %}
  </section>
</body>
</html>
```

- [ ] **Step 2: Smoke-render**

```bash
cd backend && python -c "
from tests.fixtures.resume_doc_json import make_resume
from app.services.pdf.template_engine import render_html
html = render_html(make_resume(), 'IN', 'swe')
assert 'Professional Experience' in html and 'A4' in html
print('ok')
"
```
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/pdf/templates/in/swe.html
git commit -m "feat(pdf): IN-SWE template (A4, scope-aware)"
```

---

### Task 11: IN-DS template

**Files:**
- Create: `backend/app/services/pdf/templates/in/ds.html`

- [ ] **Step 1: Write the template**

```html
{# backend/app/services/pdf/templates/in/ds.html — IN DS: methods + scope #}
<!doctype html>
<html lang="en" class="country-IN role-ds">
<head>
  <meta charset="utf-8">
  <title>{{ doc.contact.name }} — Resume</title>
  <link rel="stylesheet" href="{{ base_css }}">
  <link rel="stylesheet" href="{{ type_css }}">
  <link rel="stylesheet" href="{{ print_css }}">
  <style>@page { size: A4; margin: 0.55in 0.55in; }</style>
</head>
<body>
  <header>
    <h1>{{ doc.contact.name }}</h1>
    <div class="meta">
      {% if doc.contact.email %}{{ doc.contact.email }}{% endif %}
      {% if doc.contact.phone %} · {{ doc.contact.phone }}{% endif %}
      {% for link in doc.contact.links %} · {{ link }}{% endfor %}
    </div>
  </header>

  {% if doc.summary %}
  <section class="section">
    <h2>Profile</h2>
    <p class="summary">{{ doc.summary }}</p>
  </section>
  {% endif %}

  <section class="section">
    <h2>Technical Skills</h2>
    <p>{{ doc.skills.hard | join(" · ") }}</p>
  </section>

  <section class="section">
    <h2>Professional Experience</h2>
    {% for exp in doc.experience %}
      <div class="experience-item">
        <div class="row">
          <strong>{{ exp.role }} — {{ exp.company }}</strong>
          <span class="muted">{{ exp.dates }}{% if exp.location %} · {{ exp.location }}{% endif %}</span>
        </div>
        <ul>{% for b in exp.bullets %}<li>{{ b.text }}</li>{% endfor %}</ul>
      </div>
    {% endfor %}
  </section>

  {% if doc.projects %}
  <section class="section">
    <h2>Key Projects</h2>
    {% for proj in doc.projects %}
      <div class="experience-item">
        <strong>{{ proj.name }}</strong>
        <ul>{% for b in proj.bullets %}<li>{{ b.text }}</li>{% endfor %}</ul>
      </div>
    {% endfor %}
  </section>
  {% endif %}

  <section class="section">
    <h2>Education</h2>
    {% for ed in doc.education %}
      <div class="row">
        <strong>{{ ed.degree }} · {{ ed.school }}</strong>
        <span class="muted">{{ ed.dates }}{% if ed.gpa %} · GPA {{ ed.gpa }}{% endif %}</span>
      </div>
    {% endfor %}
  </section>
</body>
</html>
```

- [ ] **Step 2: Smoke-render**

```bash
cd backend && python -c "
from tests.fixtures.resume_doc_json import make_resume
from app.services.pdf.template_engine import render_html
html = render_html(make_resume(), 'IN', 'ds')
assert 'Technical Skills' in html
print('ok')
"
```
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/pdf/templates/in/ds.html
git commit -m "feat(pdf): IN-DS template"
```

---

### Task 12: IN-PM template

**Files:**
- Create: `backend/app/services/pdf/templates/in/pm.html`

- [ ] **Step 1: Write the template**

```html
{# backend/app/services/pdf/templates/in/pm.html — IN PM: outcomes + scope #}
<!doctype html>
<html lang="en" class="country-IN role-pm">
<head>
  <meta charset="utf-8">
  <title>{{ doc.contact.name }} — Resume</title>
  <link rel="stylesheet" href="{{ base_css }}">
  <link rel="stylesheet" href="{{ type_css }}">
  <link rel="stylesheet" href="{{ print_css }}">
  <style>@page { size: A4; margin: 0.55in 0.55in; }</style>
</head>
<body>
  <header>
    <h1>{{ doc.contact.name }}</h1>
    <div class="meta">
      {% if doc.contact.email %}{{ doc.contact.email }}{% endif %}
      {% if doc.contact.phone %} · {{ doc.contact.phone }}{% endif %}
      {% for link in doc.contact.links %} · {{ link }}{% endfor %}
    </div>
  </header>

  {% if doc.summary %}
  <section class="section">
    <h2>Profile</h2>
    <p class="summary">{{ doc.summary }}</p>
  </section>
  {% endif %}

  <section class="section">
    <h2>Professional Experience</h2>
    {% for exp in doc.experience %}
      <div class="experience-item">
        <div class="row">
          <strong>{{ exp.role }} · {{ exp.company }}</strong>
          <span class="muted">{{ exp.dates }}{% if exp.location %} · {{ exp.location }}{% endif %}</span>
        </div>
        <ul>{% for b in exp.bullets %}<li>{{ b.text }}</li>{% endfor %}</ul>
      </div>
    {% endfor %}
  </section>

  <section class="section">
    <h2>Skills</h2>
    <p>{{ doc.skills.hard | join(" · ") }}</p>
  </section>

  <section class="section">
    <h2>Education</h2>
    {% for ed in doc.education %}
      <div class="row">
        <strong>{{ ed.degree }} · {{ ed.school }}</strong>
        <span class="muted">{{ ed.dates }}</span>
      </div>
    {% endfor %}
  </section>
</body>
</html>
```

- [ ] **Step 2: Smoke-render**

```bash
cd backend && python -c "
from tests.fixtures.resume_doc_json import make_resume
from app.services.pdf.template_engine import render_html
html = render_html(make_resume(), 'IN', 'pm')
assert 'Profile' in html
print('ok')
"
```
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/pdf/templates/in/pm.html
git commit -m "feat(pdf): IN-PM template"
```

---

### Task 13: PDF renderer — Playwright wrapper with timeout + retry + fallback

**Files:**
- Create: `backend/app/services/pdf/renderer.py`
- Create: `backend/tests/services/pdf/test_renderer.py`

- [ ] **Step 1: Write failing renderer tests**

```python
# backend/tests/services/pdf/test_renderer.py
import pytest
from unittest.mock import MagicMock, patch
from tests.fixtures.resume_doc_json import make_resume


def test_render_pdf_returns_bytes_starting_with_pdf_magic(tmp_path):
    from app.services.pdf.renderer import render_pdf_from_doc
    pdf = render_pdf_from_doc(make_resume(), country="US", role="swe")
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000   # not an empty stub


def test_render_pdf_retries_once_on_timeout(monkeypatch):
    """First call raises TimeoutError, second call succeeds, render returns bytes."""
    from app.services.pdf import renderer
    calls = {"n": 0}

    def fake_render_bytes(html, timeout_s):
        calls["n"] += 1
        if calls["n"] == 1:
            from playwright.sync_api import TimeoutError as PWTimeout
            raise PWTimeout("simulated")
        return b"%PDF-retry-success"

    monkeypatch.setattr(renderer, "_render_html_to_pdf_bytes", fake_render_bytes)
    pdf = renderer.render_pdf_from_doc(make_resume(), country="US", role="swe")
    assert pdf.startswith(b"%PDF-")
    assert calls["n"] == 2


def test_render_pdf_falls_back_to_us_swe_on_template_error(monkeypatch):
    """If the requested template raises, we fall back to us/swe and still return a PDF."""
    from app.services.pdf import renderer
    from app.services.pdf import template_engine

    calls = {"templates": []}
    original_render_html = template_engine.render_html

    def flaky_render_html(doc, country, role):
        calls["templates"].append((country, role))
        if (country, role) == ("IN", "ds"):
            raise RuntimeError("simulated template fail")
        return original_render_html(doc, country, role)

    monkeypatch.setattr(template_engine, "render_html", flaky_render_html)
    monkeypatch.setattr(renderer, "render_html", flaky_render_html)
    pdf = renderer.render_pdf_from_doc(make_resume(), country="IN", role="ds")
    assert pdf.startswith(b"%PDF-")
    assert ("IN", "ds") in calls["templates"]
    assert ("US", "swe") in calls["templates"]


def test_render_pdf_raises_after_second_timeout(monkeypatch):
    from app.services.pdf import renderer
    from playwright.sync_api import TimeoutError as PWTimeout

    def always_timeout(html, timeout_s):
        raise PWTimeout("simulated")

    monkeypatch.setattr(renderer, "_render_html_to_pdf_bytes", always_timeout)
    with pytest.raises(renderer.PdfRenderTimeout):
        renderer.render_pdf_from_doc(make_resume(), country="US", role="swe")
```

- [ ] **Step 2: Run — FAIL**

```bash
cd backend && pytest tests/services/pdf/test_renderer.py -v
```
Expected: 4 fails (module missing).

- [ ] **Step 3: Implement the renderer**

```python
# backend/app/services/pdf/renderer.py
"""Playwright-backed HTML→PDF renderer.

Public API: render_pdf_from_doc(doc, country, role) -> bytes

Behavior:
- Single shared Playwright + browser instance (lazy, process-global).
- 15s timeout per render (configurable via settings.PDF_RENDER_TIMEOUT_S).
- One retry on Playwright TimeoutError.
- If the template engine raises, fall back to us/swe and try again.
- After fallback, a second timeout raises PdfRenderTimeout; callers refund the credit.
"""
from __future__ import annotations

import threading
from typing import Optional

from playwright.sync_api import (
    Browser,
    Playwright,
    TimeoutError as PWTimeout,
    sync_playwright,
)

from app.core.config import settings
from app.schemas.resume import ResumeDocumentJSON
from app.services.pdf.template_engine import render_html


class PdfRenderTimeout(Exception):
    pass


_lock = threading.Lock()
_pw: Optional[Playwright] = None
_browser: Optional[Browser] = None


def _get_browser() -> Browser:
    global _pw, _browser
    with _lock:
        if _browser is None or not _browser.is_connected():
            _pw = sync_playwright().start()
            _browser = _pw.chromium.launch(args=["--no-sandbox"])
        return _browser


def _render_html_to_pdf_bytes(html: str, timeout_s: int) -> bytes:
    """Render HTML to PDF bytes via a fresh page. Raises Playwright TimeoutError on miss."""
    browser = _get_browser()
    context = browser.new_context()
    try:
        page = context.new_page()
        page.set_default_timeout(timeout_s * 1000)
        page.set_content(html, wait_until="networkidle")
        return page.pdf(
            print_background=True,
            prefer_css_page_size=True,
        )
    finally:
        context.close()


def render_pdf_from_doc(
    doc: ResumeDocumentJSON,
    country: str,
    role: str,
    timeout_s: Optional[int] = None,
) -> bytes:
    """Render a resume doc to PDF bytes. One retry on timeout. Template fallback on render error."""
    t = timeout_s or settings.PDF_RENDER_TIMEOUT_S

    # Stage 1: template
    try:
        html = render_html(doc, country, role)
    except Exception:
        # Template-engine failure → fall back to a known-good template.
        html = render_html(doc, "US", "swe")

    # Stage 2: PDF render with one retry on timeout.
    try:
        return _render_html_to_pdf_bytes(html, timeout_s=t)
    except PWTimeout:
        try:
            return _render_html_to_pdf_bytes(html, timeout_s=t)
        except PWTimeout as exc:
            raise PdfRenderTimeout(f"PDF render timed out after retry (>{t}s)") from exc
```

> **Why a process-global browser:** launching Chromium takes ~500ms. Keeping it alive between requests turns each export into a fast `new_context()`. A new context per request is cheap and isolates cookies/storage.

- [ ] **Step 4: Re-run — PASS**

```bash
cd backend && pytest tests/services/pdf/test_renderer.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pdf/renderer.py backend/tests/services/pdf/test_renderer.py
git commit -m "feat(pdf): Playwright renderer with 15s timeout, retry, template fallback"
```

---

### Task 14: Renderer telemetry — structured latency + size logging

**Files:**
- Modify: `backend/app/services/pdf/renderer.py`
- Create: `backend/tests/services/pdf/test_renderer_telemetry.py`

> **Why this is its own task:** Phase 1 added LLM cost/latency telemetry in `app/core/llm_logging.py`. We mirror the pattern so the existing log aggregation / cost dashboard query keeps working. Doing it inline in Task 13 would bloat that task; doing it later risks forgetting.

- [ ] **Step 1: Write failing telemetry test**

```python
# backend/tests/services/pdf/test_renderer_telemetry.py
import logging
import json
from tests.fixtures.resume_doc_json import make_resume


def test_render_pdf_emits_structured_log(caplog):
    from app.services.pdf import renderer
    caplog.set_level(logging.INFO, logger="pdf_render")
    renderer.render_pdf_from_doc(make_resume(), country="US", role="swe")
    records = [r for r in caplog.records if r.name == "pdf_render"]
    assert records, "expected at least one pdf_render log record"
    # We attach structured fields via record.__dict__; verify shape.
    last = records[-1]
    payload = getattr(last, "structured", None)
    assert payload, "expected 'structured' field on log record"
    assert payload["event"] == "pdf_render"
    assert payload["country"] == "US"
    assert payload["role"] == "swe"
    assert isinstance(payload["render_ms"], int)
    assert payload["render_ms"] >= 0
    assert isinstance(payload["file_size_bytes"], int)
    assert payload["file_size_bytes"] > 0
    assert payload["status"] == "succeeded"
```

- [ ] **Step 2: Run — FAIL**

```bash
cd backend && pytest tests/services/pdf/test_renderer_telemetry.py -v
```
Expected: fail (no `pdf_render` logger / no `structured` field).

- [ ] **Step 3: Add telemetry to renderer**

In `backend/app/services/pdf/renderer.py`, at module top add:

```python
import logging
import time

_log = logging.getLogger("pdf_render")
```

Replace the body of `render_pdf_from_doc` with:

```python
def render_pdf_from_doc(
    doc: ResumeDocumentJSON,
    country: str,
    role: str,
    timeout_s: Optional[int] = None,
) -> bytes:
    t = timeout_s or settings.PDF_RENDER_TIMEOUT_S
    started = time.monotonic()
    status = "succeeded"
    fallback_used = False
    try:
        try:
            html = render_html(doc, country, role)
        except Exception:
            fallback_used = True
            html = render_html(doc, "US", "swe")
        try:
            pdf = _render_html_to_pdf_bytes(html, timeout_s=t)
        except PWTimeout:
            try:
                pdf = _render_html_to_pdf_bytes(html, timeout_s=t)
            except PWTimeout as exc:
                status = "timed_out"
                raise PdfRenderTimeout(f"PDF render timed out after retry (>{t}s)") from exc
        return pdf
    except Exception:
        if status == "succeeded":
            status = "errored"
        raise
    finally:
        render_ms = int((time.monotonic() - started) * 1000)
        size = len(pdf) if status == "succeeded" else 0
        _log.info(
            "pdf_render",
            extra={
                "structured": {
                    "event": "pdf_render",
                    "country": country,
                    "role": role,
                    "render_ms": render_ms,
                    "file_size_bytes": size,
                    "status": status,
                    "fallback_used": fallback_used,
                }
            },
        )
```

- [ ] **Step 4: Re-run — PASS**

```bash
cd backend && pytest tests/services/pdf/test_renderer_telemetry.py tests/services/pdf/test_renderer.py -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pdf/renderer.py backend/tests/services/pdf/test_renderer_telemetry.py
git commit -m "feat(obs): pdf_render structured latency + size logging"
```

---

### Task 15: Smoke test — all 6 templates render to valid PDFs

**Files:**
- Create: `backend/tests/services/pdf/test_templates_smoke.py`

- [ ] **Step 1: Write the parametric smoke test**

```python
# backend/tests/services/pdf/test_templates_smoke.py
import pytest
from tests.fixtures.resume_doc_json import make_resume


@pytest.mark.parametrize("country,role", [
    ("US", "swe"), ("US", "ds"), ("US", "pm"),
    ("IN", "swe"), ("IN", "ds"), ("IN", "pm"),
])
def test_each_template_renders_valid_pdf(country, role):
    from app.services.pdf.renderer import render_pdf_from_doc
    pdf = render_pdf_from_doc(make_resume(), country=country, role=role)
    assert pdf.startswith(b"%PDF-"), f"{country}/{role} did not produce a PDF magic header"
    assert len(pdf) > 2000, f"{country}/{role} PDF suspiciously small ({len(pdf)} bytes)"
```

- [ ] **Step 2: Run — PASS**

```bash
cd backend && pytest tests/services/pdf/test_templates_smoke.py -v
```
Expected: 6 passed.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/services/pdf/test_templates_smoke.py
git commit -m "test(pdf): smoke — all 6 country/role templates render valid PDFs"
```

---

### Task 16: Performance assertion — single-template render under 8s

**Files:**
- Create: `backend/tests/services/pdf/test_renderer_perf.py`

> Spec §10 requires p95 < 8s. We can't measure p95 in unit tests, but we can put a coarse upper bound (single render < 8s on the CI box) — anything slower is a regression worth catching.

- [ ] **Step 1: Write the perf test**

```python
# backend/tests/services/pdf/test_renderer_perf.py
import os
import time
import pytest
from tests.fixtures.resume_doc_json import make_resume

# Skip in CI environments that can't run headless Chromium reliably.
pytestmark = pytest.mark.skipif(
    os.environ.get("PDF_PERF_SKIP") == "1",
    reason="PDF_PERF_SKIP=1 set",
)


def test_single_render_under_8s_after_warmup():
    from app.services.pdf.renderer import render_pdf_from_doc

    # Warmup: launching Chromium dominates the first call; perf budget is per render
    # after browser is hot.
    render_pdf_from_doc(make_resume(), country="US", role="swe")

    started = time.monotonic()
    render_pdf_from_doc(make_resume(), country="US", role="swe")
    elapsed = time.monotonic() - started
    assert elapsed < 8.0, f"warm render took {elapsed:.2f}s (budget 8.0s)"
```

- [ ] **Step 2: Run — PASS**

```bash
cd backend && pytest tests/services/pdf/test_renderer_perf.py -v
```
Expected: 1 passed (will be the slowest test; expected ~1-3s warm).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/services/pdf/test_renderer_perf.py
git commit -m "test(pdf): warm-render perf budget <8s per template"
```

---

### Task 17: API endpoint — `POST /api/v1/exports`

**Files:**
- Create: `backend/app/api/v1/endpoints/exports.py`
- Modify: `backend/app/api/v1/api.py`
- Create: `backend/tests/api/test_exports_endpoint.py`

- [ ] **Step 1: Write failing endpoint tests**

```python
# backend/tests/api/test_exports_endpoint.py
import uuid
from unittest.mock import patch
import pytest


def test_export_requires_auth(client):
    resp = client.post("/api/v1/exports", json={
        "resume_document_id": "x", "country": "US", "role_template": "swe",
    })
    assert resp.status_code in (401, 403)


def test_export_404_on_unknown_resume(client, auth_headers, user_with_credits):
    resp = client.post(
        "/api/v1/exports",
        json={"resume_document_id": str(uuid.uuid4()), "country": "US", "role_template": "swe"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_export_happy_path_debits_one_credit(
    client, auth_headers, user_with_credits, uploaded_resume_doc,
    mock_pdf_render, mock_supabase_upload, mock_signed_url,
):
    starting = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_document_id": uploaded_resume_doc.id,
            "country": "US",
            "role_template": "swe",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["download_url"].startswith("https://")
    assert body["country"] == "US"
    assert body["role_template"] == "swe"
    after = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    assert after == starting - 1


def test_export_refunds_credit_on_render_timeout(
    client, auth_headers, user_with_credits, uploaded_resume_doc,
    mock_pdf_render_timeout,
):
    starting = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_document_id": uploaded_resume_doc.id,
            "country": "US",
            "role_template": "swe",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 500
    after = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    assert after == starting, "credit must be refunded on hard render failure"
```

- [ ] **Step 2: Add the supporting fixtures**

Append to `backend/tests/conftest.py`:

```python
import pytest
import uuid
from unittest.mock import patch


@pytest.fixture
def uploaded_resume_doc(db_session, current_user):
    """A persisted ResumeDocument owned by current_user, used by export tests."""
    from app.models.resume_document import ResumeDocument
    from tests.fixtures.resume_doc_json import make_resume
    doc_json = make_resume()
    row = ResumeDocument(
        id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        original_filename="r.pdf",
        file_path="/tmp/ignored.pdf",
        file_type="pdf",
        parsed_json=doc_json.model_dump(),
        raw_text=doc_json.raw_text,
    )
    db_session.add(row)
    db_session.commit()
    return row


@pytest.fixture
def mock_pdf_render():
    with patch("app.api.v1.endpoints.exports.render_pdf_from_doc", return_value=b"%PDF-stub-content"):
        yield


@pytest.fixture
def mock_pdf_render_timeout():
    from app.services.pdf.renderer import PdfRenderTimeout
    with patch(
        "app.api.v1.endpoints.exports.render_pdf_from_doc",
        side_effect=PdfRenderTimeout("simulated"),
    ):
        yield


@pytest.fixture
def mock_supabase_upload():
    with patch("app.api.v1.endpoints.exports.upload_pdf", return_value="user-1/exp-1.pdf") as m:
        yield m


@pytest.fixture
def mock_signed_url():
    with patch(
        "app.api.v1.endpoints.exports.signed_url",
        return_value="https://supabase.example/file.pdf?token=abc",
    ) as m:
        yield m
```

> **Note:** `db_session`, `current_user`, `client`, `auth_headers`, `user_with_credits` fixtures already exist in `backend/tests/conftest.py` from Phase 1 (Task 14 added the test conftest). If a fixture name differs in the codebase, align this Task to the actual name rather than renaming the existing fixture.

- [ ] **Step 3: Run — FAIL**

```bash
cd backend && pytest tests/api/test_exports_endpoint.py -v
```
Expected: 4 fails (endpoint not registered).

- [ ] **Step 4: Implement the endpoint**

```python
# backend/app/api/v1/endpoints/exports.py
"""Phase-2 PDF export endpoint.

POST /api/v1/exports  — render a resume to PDF, store, return signed URL. Costs 1 credit.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.config import settings
from app.core.supabase_storage import signed_url, upload_pdf
from app.db.session import get_db
from app.middleware.credits import credit_transaction
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.resume_export import ResumeExport
from app.schemas.resume import ResumeDocumentJSON
from app.schemas.resume_export import ExportRequest, ExportResponse
from app.services.pdf.renderer import PdfRenderTimeout, render_pdf_from_doc

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("", response_model=ExportResponse, status_code=201)
async def create_export(
    body: ExportRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    # 1. Verify the resume document exists and belongs to the caller.
    doc_row = db.get(ResumeDocument, body.resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Resume document not found")

    # 2. Optionally hydrate from a specific version.
    if body.resume_version_id:
        version = db.get(ResumeVersion, body.resume_version_id)
        if not version or version.resume_document_id != body.resume_document_id:
            raise HTTPException(status_code=404, detail="Version not found")
        doc_json = ResumeDocumentJSON.model_validate(version.parsed_json)
    else:
        doc_json = ResumeDocumentJSON.model_validate(doc_row.parsed_json)

    export_id = str(uuid.uuid4())
    storage_path = f"{current_user_id}/{export_id}.pdf"

    # 3. Debit 1 credit, render, upload. On render hard-fail the context manager rolls back the debit.
    response_payload: ExportResponse | None = None
    with credit_transaction(db, current_user_id, amount=1, reason="export"):
        try:
            pdf_bytes = render_pdf_from_doc(
                doc_json,
                country=body.country.value,
                role=body.role_template.value,
            )
        except PdfRenderTimeout as exc:
            # Persist a failed-export row for support/debugging — outside the credit
            # transaction's commit boundary, so this insert happens only if we re-raise
            # cleanly. We use a separate session-flush to keep ordering simple.
            db.add(ResumeExport(
                id=export_id,
                user_id=current_user_id,
                resume_document_id=body.resume_document_id,
                resume_version_id=body.resume_version_id,
                country=body.country.value,
                role_template=body.role_template.value,
                storage_path=storage_path,
                status="timed_out",
                error_message=str(exc),
            ))
            # credit_transaction will refund on exception.
            raise HTTPException(status_code=500, detail="PDF render timed out; please retry") from exc

        upload_pdf(pdf_bytes, storage_path)
        url = signed_url(storage_path)
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.SUPABASE_SIGNED_URL_TTL_SECONDS
        )

        db.add(ResumeExport(
            id=export_id,
            user_id=current_user_id,
            resume_document_id=body.resume_document_id,
            resume_version_id=body.resume_version_id,
            country=body.country.value,
            role_template=body.role_template.value,
            storage_path=storage_path,
            status="succeeded",
            file_size_bytes=len(pdf_bytes),
        ))
        response_payload = ExportResponse(
            export_id=export_id,
            download_url=url,
            expires_at=expires_at,
            country=body.country,
            role_template=body.role_template,
        )
    db.commit()
    return response_payload
```

- [ ] **Step 5: Register the router**

Open `backend/app/api/v1/api.py`. Add the import and registration line (alongside the other v1 routers):

```python
from app.api.v1.endpoints import exports
...
api_router.include_router(exports.router)
```

- [ ] **Step 6: Re-run — PASS**

```bash
cd backend && pytest tests/api/test_exports_endpoint.py -v
```
Expected: 4 passed.

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/v1/endpoints/exports.py backend/app/api/v1/api.py backend/tests/api/test_exports_endpoint.py backend/tests/conftest.py
git commit -m "feat(api): POST /api/v1/exports — credit-debited PDF render + storage"
```

---

### Task 18: API endpoint — `GET /api/v1/exports/{id}`

**Files:**
- Modify: `backend/app/api/v1/endpoints/exports.py`
- Modify: `backend/tests/api/test_exports_endpoint.py`

> **Why this endpoint:** signed URLs expire (7-day TTL). The frontend may need to re-issue a download link without re-rendering. `GET` returns a fresh signed URL for an existing successful export at zero credit cost.

- [ ] **Step 1: Add failing test**

Append to `backend/tests/api/test_exports_endpoint.py`:

```python
def test_get_export_returns_fresh_signed_url(
    client, auth_headers, user_with_credits, uploaded_resume_doc,
    mock_pdf_render, mock_supabase_upload, mock_signed_url,
):
    created = client.post(
        "/api/v1/exports",
        json={"resume_document_id": uploaded_resume_doc.id, "country": "US", "role_template": "swe"},
        headers=auth_headers,
    )
    export_id = created.json()["export_id"]
    resp = client.get(f"/api/v1/exports/{export_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["export_id"] == export_id
    assert resp.json()["download_url"].startswith("https://")


def test_get_export_404_for_other_user(client, auth_headers_other_user):
    resp = client.get("/api/v1/exports/does-not-exist", headers=auth_headers_other_user)
    assert resp.status_code == 404
```

If `auth_headers_other_user` is not already in `conftest.py`, add a fixture that mints a JWT for a different `user_id`:

```python
@pytest.fixture
def auth_headers_other_user():
    # Mirror the existing auth_headers fixture but with a different sub.
    from tests.conftest import _make_jwt
    return {"Authorization": f"Bearer {_make_jwt('other-user-id')}"}
```

(If the existing fixture builder has a different name, use that — the goal is "headers for a second user".)

- [ ] **Step 2: Run — FAIL**

```bash
cd backend && pytest tests/api/test_exports_endpoint.py::test_get_export_returns_fresh_signed_url tests/api/test_exports_endpoint.py::test_get_export_404_for_other_user -v
```
Expected: 404 from FastAPI (route not defined).

- [ ] **Step 3: Add the endpoint**

In `backend/app/api/v1/endpoints/exports.py`, after `create_export`:

```python
@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    row = db.get(ResumeExport, export_id)
    if not row or row.user_id != current_user_id or row.status != "succeeded":
        raise HTTPException(status_code=404, detail="Export not found")
    url = signed_url(row.storage_path)
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.SUPABASE_SIGNED_URL_TTL_SECONDS
    )
    return ExportResponse(
        export_id=row.id,
        download_url=url,
        expires_at=expires_at,
        country=row.country,         # str → Country enum coercion via pydantic
        role_template=row.role_template,
    )
```

- [ ] **Step 4: Re-run — PASS**

```bash
cd backend && pytest tests/api/test_exports_endpoint.py -v
```
Expected: all pass (now 6 in this file).

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/endpoints/exports.py backend/tests/api/test_exports_endpoint.py backend/tests/conftest.py
git commit -m "feat(api): GET /api/v1/exports/{id} — refresh signed URL (no credit)"
```

---

### Task 19: End-to-end test — upload → version → export

**Files:**
- Create: `backend/tests/integration/test_export_e2e.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/integration/test_export_e2e.py
import respx
from pathlib import Path
from unittest.mock import patch

FIXTURE = Path(__file__).parent.parent / "fixtures/resumes/simple.pdf"


@respx.mock
def test_export_e2e_after_upload_and_version(
    client, auth_headers, user_with_credits,
    mock_supabase_upload, mock_signed_url,
):
    # 1. Upload
    with FIXTURE.open("rb") as f:
        up = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert up.status_code == 201, up.text
    doc_id = up.json()["resume_document_id"]

    # 2. Apply an empty version (smoke; full diff covered by Phase 1 e2e)
    v = client.post(
        f"/api/v1/resumes/{doc_id}/versions",
        json={"change_set": []},
        headers=auth_headers,
    )
    assert v.status_code == 201
    version_id = v.json()["version_id"]

    # 3. Export — real renderer so we exercise Playwright + templates end-to-end
    starting_bal = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_document_id": doc_id,
            "resume_version_id": version_id,
            "country": "US",
            "role_template": "swe",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload["download_url"].startswith("https://")
    assert payload["country"] == "US"

    # 4. Credit debited
    after_bal = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    assert after_bal == starting_bal - 1

    # 5. GET returns a fresh signed URL without re-debiting
    re_get = client.get(f"/api/v1/exports/{payload['export_id']}", headers=auth_headers)
    assert re_get.status_code == 200
    after_get_bal = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    assert after_get_bal == after_bal
```

- [ ] **Step 2: Run — PASS**

```bash
cd backend && pytest tests/integration/test_export_e2e.py -v
```
Expected: 1 passed (takes ~3-5s due to real Playwright render).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_export_e2e.py
git commit -m "test(e2e): upload → version → export → fresh signed URL"
```

---

### Task 20: Wire smoke test — exports routes appear on the app

**Files:**
- Modify: `backend/tests/smoke/test_phase1_routes.py` (already exists from Phase 1 Task 20) — add a phase-2 route assertion.

> **Why piggyback on the existing Phase 1 smoke file:** the same one-line route-registration assertion pattern; adding a new file would duplicate setup. If the file isn't named `test_phase1_routes.py` exactly, find the existing route-registration smoke test and append to it.

- [ ] **Step 1: Add assertion**

Append to `backend/tests/smoke/test_phase1_routes.py`:

```python
def test_phase2_export_routes_registered(client):
    paths = [r.path for r in client.app.routes]
    assert "/api/v1/exports" in paths
    # Path-param route shows up with the param token in FastAPI's routing tree.
    assert any(p.startswith("/api/v1/exports/{") for p in paths)
```

- [ ] **Step 2: Run — PASS**

```bash
cd backend && pytest tests/smoke/test_phase1_routes.py -v
```
Expected: previous tests + 1 new pass.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/smoke/test_phase1_routes.py
git commit -m "test(smoke): phase-2 export routes registered"
```

---

### Task 21: CI — ensure Playwright Chromium is installed in CI

**Files:**
- Modify: existing CI workflow file (look in `.github/workflows/*.yml`, e.g. `backend-tests.yml` or `ci.yml`).

- [ ] **Step 1: Identify the backend CI job**

Run:
```bash
ls .github/workflows/ 2>/dev/null
grep -l "pytest\|backend" .github/workflows/*.yml 2>/dev/null
```

- [ ] **Step 2: Add a `playwright install chromium` step**

In the backend CI job, after the `pip install -r backend/requirements.txt` step, add:

```yaml
      - name: Install Playwright Chromium
        working-directory: backend
        run: python -m playwright install --with-deps chromium
```

> **Why `--with-deps`:** ubuntu-latest is missing the C libraries Chromium needs. `--with-deps` installs them. Local macOS/dev shells don't need it.

- [ ] **Step 3: Push branch + observe CI**

```bash
git add .github/workflows/
git commit -m "ci: install playwright chromium for phase-2 PDF tests"
git push
```

- [ ] **Step 4: Verify CI green**

Wait for CI on the branch to go green. If it fails on `playwright install`, the most likely cause is sudo prompts from `--with-deps`; use `apt-get install` of the Chromium runtime deps directly as an alternative.

---

### Task 22: README + docs

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Append the Phase 2 endpoints**

Open `README.md` and find the existing "Phase 1 — Resume + JD Backend" block. Append a new section right under it:

```markdown
## Phase 2 — PDF Render (in progress)

New REST endpoints (v1):
- `POST /api/v1/exports` — render a resume document (optionally a specific version) to PDF using a country+role template, upload to Supabase Storage, return signed download URL. Costs 1 credit; refunded on hard render failure.
- `GET /api/v1/exports/{id}` — return a fresh signed download URL for an existing successful export. Zero-cost.

Templates: 6 HTML+CSS templates under `backend/app/services/pdf/templates/` (us|in × swe|ds|pm). Rendering uses headless Chromium via Playwright (`backend/app/services/pdf/renderer.py`).

Architecture: see `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md` §7.7.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README — phase 2 PDF export endpoints + template layout"
```

---

## Self-Review Summary

**Spec coverage check (post-write):**
- §6 Architecture — `services/pdf/{renderer,templates}` directory created: Tasks 5, 6, 13. ✓
- §7.7 PDF renderer (Puppeteer→Playwright, 6 templates, signed URL): Tasks 5–18. ✓
- §7.7 country differences (US Letter/action-first vs IN A4/scope-aware): Tasks 7–12 (per-country @page rules + section labels). ✓
- §7.8 1-credit-per-export + refund on hard fail: Task 17 (uses `credit_transaction` context manager, which refunds on exception). ✓
- §8.1 step 12 Export flow: Tasks 17, 19. ✓
- §9 Puppeteer timeout 15s + retry + 500 + no credit: Tasks 13, 17 (`PdfRenderTimeout` → 500 inside `credit_transaction` → automatic refund). ✓
- §9 Template HTML render fail fallback: Task 13 (`render_html` failure → fall back to `us/swe`). ✓
- §9 Observability — render-time logging: Task 14. ✓
- §10 Render smoke (each of 6 templates): Task 15. ✓
- §10 Performance <8s budget: Task 16. ✓
- §10 Font embedding (Inter + IBM Plex): Typography CSS sets the font stack (Task 6). Chromium subsets and embeds when fonts resolve — visual regression confirms via output PDF size > threshold. Note: production should ensure the fonts are available in the rendering container (host fonts or `@font-face` via local files). Defer hardening to ops follow-up if Chromium's default font fallback differs from local dev.
- §10 Visual regression — **deferred to follow-up.** Phase 2 ships smoke + perf + e2e tests; pixel-diff snapshot tests are a Phase 2.1 polish item.

**Open follow-ups (out of scope here):**
- Phase 2.1: pixel-diff snapshot tests for templates (PDF→PNG via pdf2image + syrupy image comparator).
- Phase 2.2: bundled font files + `@font-face` rules with `file://` URLs in `_typography.css` so renders are font-deterministic across hosts.
- BLOCKERS.md Issue 3 (resume uploads on ephemeral FS) — independent fix; can land before or after Phase 2 without coupling.
- Phase 3: frontend export UI (`/dashboard/resume/[id]/export` — template picker + preview + download).

**Placeholder scan:** none — every step contains real code or runnable commands.

**Type consistency:**
- `country` is `"US"`/`"IN"` (string-enum) everywhere: schema, DB column, template path, render call.
- `role_template`/`role` is `"swe"`/`"ds"`/`"pm"` (lowercase) everywhere: schema, DB column, template path, fixture, renderer call.
- `render_pdf_from_doc(doc, country, role, timeout_s=None)` signature is consistent across renderer module + endpoint + tests.
- `ResumeExport.status` values: `"succeeded"` (default), `"timed_out"`, `"errored"` — used consistently in Task 17, 13, 14.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-20-prism-pro-phase-2-pdf-render.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
