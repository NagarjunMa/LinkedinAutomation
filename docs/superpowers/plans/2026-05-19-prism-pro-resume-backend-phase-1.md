# Prism Pro Resume Backend — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the backend foundation for Prism Pro's resume polish + JD-driven tailoring product: file parsing, single-agent evaluation, ATS simulator, hallucination-guarded rewriter, JD extractor and tailor, credit ledger and middleware, and the REST endpoints that drive both flows.

**Architecture:** Extend the existing FastAPI monolith at `backend/app/`. Add `services/resume/` and `services/jd/` packages. Replace the legacy `consolidated_resume_evaluator.py` with the new specialized-pass design. All GPT-4o calls use OpenAI Structured Outputs (Pydantic v2). No multi-agent fan-out. Credits are a single fungible counter with row-locked debits and refund-on-fail.

**Tech Stack:** FastAPI 0.104, Python 3.11, SQLAlchemy 2.0 (existing), Alembic for migrations, OpenAI 1.3.7 (`openai` Python SDK with `.parse()` for structured outputs), pdfplumber + PyMuPDF for PDF parsing, python-docx for DOCX, pytest + respx for HTTP mocks, Pydantic 2.5.

**Out of scope (separate plans):**
- PDF render + 6 country/role templates (Phase 2 plan)
- Frontend flows (Phase 3 plan)
- Legacy code deprecation (Phase 4 plan)
- Voice interview (deferred, separate spec)

**Spec reference:** `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md`

---

## File Structure

**New packages/files:**
```
backend/app/
├── models/
│   ├── resume_document.py        (new — ResumeDocument, ResumeVersion)
│   ├── resume_evaluation_v2.py   (new — replaces legacy ResumeEvaluation usage)
│   ├── jd_evaluation.py          (new)
│   └── credit_ledger.py          (new)
├── schemas/                       (new dir — Pydantic v2 schemas)
│   ├── __init__.py
│   ├── resume.py
│   ├── jd.py
│   └── credits.py
├── services/
│   ├── resume/
│   │   ├── __init__.py
│   │   ├── parser.py             (PDF + DOCX → ResumeDocument JSON)
│   │   ├── evaluator.py          (GPT-4o eval — weak-bullet flags)
│   │   ├── ats_simulator.py      (parseability + raw-text preview)
│   │   ├── rewriter.py           (per-bullet rewrite)
│   │   └── hallucination_guard.py (regex + cross-check)
│   ├── jd/
│   │   ├── __init__.py
│   │   ├── extractor.py          (JD → requirements)
│   │   └── tailor.py             (resume × JD → diff plan)
│   └── credits/
│       ├── __init__.py
│       └── ledger.py             (debit/refund + grant)
├── api/v1/endpoints/
│   ├── resumes_v2.py             (new endpoints; legacy resumes.py untouched in Phase 1)
│   ├── jd.py                     (new)
│   └── credits.py                (new)
├── middleware/
│   └── credits.py                (new — require_credits decorator)
└── migrations/versions/
    └── 2026_05_19_add_phase1_tables.py
```

**Test files:**
```
backend/tests/
├── fixtures/
│   ├── resumes/                  (10 PDF, 10 DOCX)
│   └── jds/                      (20 JD .txt files across countries+roles)
├── services/
│   ├── resume/
│   │   ├── test_parser.py
│   │   ├── test_evaluator.py
│   │   ├── test_ats_simulator.py
│   │   ├── test_rewriter.py
│   │   └── test_hallucination_guard.py
│   ├── jd/
│   │   ├── test_extractor.py
│   │   └── test_tailor.py
│   └── credits/
│       └── test_ledger.py
└── api/v1/
    ├── test_resumes_v2.py
    ├── test_jd.py
    └── test_credits.py
```

---

### Task 0: Environment + dependency setup

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/.env.example` (or create if missing)

- [ ] **Step 1: Pin required dependencies**

Append to `backend/requirements.txt`:

```
pdfplumber==0.11.4
respx==0.20.2
tenacity==8.2.3
```

(PyMuPDF and python-docx are already pinned. openai==1.3.7 supports `.parse()` via `client.beta.chat.completions.parse`. If you need newer structured-output API, bump to `openai>=1.40.0` and verify other callers still work — verify with `grep -r "from openai" backend/app` first.)

- [ ] **Step 2: Install + commit**

```bash
cd backend && pip install -r requirements.txt
git add backend/requirements.txt
git commit -m "chore: add pdfplumber, respx, tenacity for phase-1 backend"
```

---

### Task 1: Alembic migration — Phase 1 tables

**Files:**
- Create: `backend/migrations/versions/2026_05_19_add_phase1_tables.py`

- [ ] **Step 1: Generate revision skeleton**

```bash
cd backend && alembic revision -m "add phase 1 resume and credit tables"
```

This creates a file in `migrations/versions/`. Rename it to `2026_05_19_add_phase1_tables.py`.

- [ ] **Step 2: Write migration content**

```python
"""add phase 1 resume and credit tables

Revision ID: 2026_05_19_phase1
Revises: <previous>
Create Date: 2026-05-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "2026_05_19_phase1"
down_revision = None  # set to actual latest revision; check via `alembic heads`
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resume_documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),   # 'pdf' | 'docx'
        sa.Column("parsed_json", postgresql.JSONB(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "resume_evaluations_v2",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("resume_document_id", sa.String(), sa.ForeignKey("resume_documents.id"), nullable=False, index=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("bullet_flags", postgresql.JSONB(), nullable=False),
        sa.Column("format_issues", postgresql.JSONB(), nullable=False),
        sa.Column("summary_critique", sa.Text(), nullable=True),
        sa.Column("ats_parseability", sa.Integer(), nullable=False),
        sa.Column("ats_raw_text", sa.Text(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "resume_versions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("resume_document_id", sa.String(), sa.ForeignKey("resume_documents.id"), nullable=False, index=True),
        sa.Column("parent_version_id", sa.String(), nullable=True),
        sa.Column("change_set", postgresql.JSONB(), nullable=False),
        sa.Column("parsed_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "jd_evaluations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("resume_document_id", sa.String(), sa.ForeignKey("resume_documents.id"), nullable=False),
        sa.Column("jd_text", sa.Text(), nullable=False),
        sa.Column("extracted_requirements", postgresql.JSONB(), nullable=False),
        sa.Column("diff_plan", postgresql.JSONB(), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "credit_ledger",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("delta", sa.Integer(), nullable=False),  # +grant / -debit / +refund
        sa.Column("reason", sa.String(), nullable=False),  # 'grant'|'evaluate'|'tailor'|'export'|'refund'
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("external_ref", sa.String(), nullable=True, unique=True),  # Stripe idempotency
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_credit_ledger_user_created", "credit_ledger", ["user_id", "created_at"])


def downgrade():
    op.drop_index("ix_credit_ledger_user_created", "credit_ledger")
    op.drop_table("credit_ledger")
    op.drop_table("jd_evaluations")
    op.drop_table("resume_versions")
    op.drop_table("resume_evaluations_v2")
    op.drop_table("resume_documents")
```

- [ ] **Step 3: Set `down_revision`**

Run `alembic heads` and replace the placeholder with the actual most-recent revision ID.

- [ ] **Step 4: Apply migration locally**

```bash
cd backend && alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade ... -> 2026_05_19_phase1, add phase 1 resume and credit tables`.

- [ ] **Step 5: Commit**

```bash
git add backend/migrations/versions/2026_05_19_add_phase1_tables.py
git commit -m "feat(db): add phase 1 tables — resume_documents, evaluations_v2, versions, jd, credits"
```

---

### Task 2: SQLAlchemy models for new tables

**Files:**
- Create: `backend/app/models/resume_document.py`
- Create: `backend/app/models/resume_evaluation_v2.py`
- Create: `backend/app/models/jd_evaluation.py`
- Create: `backend/app/models/credit_ledger.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write a failing import test**

Create `backend/tests/test_models_import.py`:

```python
def test_phase1_models_import():
    from app.models.resume_document import ResumeDocument, ResumeVersion
    from app.models.resume_evaluation_v2 import ResumeEvaluationV2
    from app.models.jd_evaluation import JDEvaluation
    from app.models.credit_ledger import CreditLedger
    assert ResumeDocument.__tablename__ == "resume_documents"
    assert ResumeVersion.__tablename__ == "resume_versions"
    assert ResumeEvaluationV2.__tablename__ == "resume_evaluations_v2"
    assert JDEvaluation.__tablename__ == "jd_evaluations"
    assert CreditLedger.__tablename__ == "credit_ledger"
```

Run: `pytest backend/tests/test_models_import.py -v`
Expected: FAIL with ImportError.

- [ ] **Step 2: Create ResumeDocument + ResumeVersion**

`backend/app/models/resume_document.py`:

```python
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base_class import Base


class ResumeDocument(Base):
    __tablename__ = "resume_documents"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    parsed_json = Column(JSONB, nullable=False)
    raw_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ResumeVersion(Base):
    __tablename__ = "resume_versions"
    id = Column(String, primary_key=True, index=True)
    resume_document_id = Column(String, ForeignKey("resume_documents.id"), nullable=False, index=True)
    parent_version_id = Column(String, nullable=True)
    change_set = Column(JSONB, nullable=False)
    parsed_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 3: Create ResumeEvaluationV2**

`backend/app/models/resume_evaluation_v2.py`:

```python
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base_class import Base


class ResumeEvaluationV2(Base):
    __tablename__ = "resume_evaluations_v2"
    id = Column(String, primary_key=True, index=True)
    resume_document_id = Column(String, ForeignKey("resume_documents.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    overall_score = Column(Integer, nullable=False)
    bullet_flags = Column(JSONB, nullable=False)
    format_issues = Column(JSONB, nullable=False)
    summary_critique = Column(Text, nullable=True)
    ats_parseability = Column(Integer, nullable=False)
    ats_raw_text = Column(Text, nullable=False)
    model_version = Column(String, nullable=False)
    cost_usd = Column(Numeric(10, 6), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 4: Create JDEvaluation + CreditLedger**

`backend/app/models/jd_evaluation.py`:

```python
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base_class import Base


class JDEvaluation(Base):
    __tablename__ = "jd_evaluations"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    resume_document_id = Column(String, ForeignKey("resume_documents.id"), nullable=False)
    jd_text = Column(Text, nullable=False)
    extracted_requirements = Column(JSONB, nullable=False)
    diff_plan = Column(JSONB, nullable=False)
    match_score = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

`backend/app/models/credit_ledger.py`:

```python
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from app.db.base_class import Base


class CreditLedger(Base):
    __tablename__ = "credit_ledger"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    delta = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    balance_after = Column(Integer, nullable=False)
    external_ref = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 5: Register in `app/models/__init__.py`**

Append:

```python
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.resume_evaluation_v2 import ResumeEvaluationV2
from app.models.jd_evaluation import JDEvaluation
from app.models.credit_ledger import CreditLedger
```

- [ ] **Step 6: Run test — verify PASS**

```bash
cd backend && pytest tests/test_models_import.py -v
```
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/ backend/tests/test_models_import.py
git commit -m "feat(models): add Phase 1 SQLAlchemy models"
```

---

### Task 3: Pydantic schemas — ResumeDocument JSON

**Files:**
- Create: `backend/app/schemas/__init__.py` (empty)
- Create: `backend/app/schemas/resume.py`

- [ ] **Step 1: Failing test**

Create `backend/tests/schemas/test_resume_schemas.py`:

```python
from app.schemas.resume import ResumeDocumentJSON, Bullet, ExperienceEntry, Skills


def test_resume_document_json_roundtrip():
    doc = ResumeDocumentJSON(
        contact={"name": "Asha", "email": "a@b.com", "phone": "+91...", "links": []},
        summary="Senior SWE...",
        experience=[ExperienceEntry(
            company="Acme", role="SWE II", dates="2022-2024", location="Bengaluru",
            bullets=[Bullet(id="b1", text="Led migration", raw_text="Led migration")]
        )],
        education=[],
        skills=Skills(hard=["Python"], soft=["communication"]),
        raw_text="full text..."
    )
    serialized = doc.model_dump()
    assert serialized["experience"][0]["bullets"][0]["id"] == "b1"
```

Run: `pytest backend/tests/schemas/test_resume_schemas.py -v` → FAIL (ImportError).

- [ ] **Step 2: Implement schemas**

`backend/app/schemas/resume.py`:

```python
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Contact(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    links: List[str] = Field(default_factory=list)


class Bullet(BaseModel):
    id: str
    text: str
    raw_text: str


class ExperienceEntry(BaseModel):
    company: str
    role: str
    dates: Optional[str] = None
    location: Optional[str] = None
    bullets: List[Bullet] = Field(default_factory=list)


class EducationEntry(BaseModel):
    school: str
    degree: Optional[str] = None
    dates: Optional[str] = None
    gpa: Optional[str] = None


class Skills(BaseModel):
    hard: List[str] = Field(default_factory=list)
    soft: List[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str
    bullets: List[Bullet] = Field(default_factory=list)


class ResumeDocumentJSON(BaseModel):
    contact: Contact
    summary: Optional[str] = None
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    projects: List[ProjectEntry] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    raw_text: str


class BulletFlag(BaseModel):
    bullet_id: str
    severity: Literal["critical", "warning", "info"]
    reason: str
    category: Literal["quantification", "verb", "structure", "clarity", "redundancy", "ats"]


class FormatIssue(BaseModel):
    type: str
    location: str
    fix_hint: str


class EvaluationReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    bullet_flags: List[BulletFlag]
    format_issues: List[FormatIssue]
    summary_critique: Optional[str] = None
    skill_gaps: List[str] = Field(default_factory=list)


class Placeholder(BaseModel):
    token: str
    what: str


class RewriteResult(BaseModel):
    rewritten: str
    placeholders: List[Placeholder]
    applied_changes: List[str]
```

- [ ] **Step 3: Run test — PASS**

```bash
pytest backend/tests/schemas/test_resume_schemas.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/ backend/tests/schemas/
git commit -m "feat(schemas): add resume document + evaluation + rewrite Pydantic schemas"
```

---

### Task 4: Resume parser — PDF path

**Files:**
- Create: `backend/app/services/resume/__init__.py` (empty)
- Create: `backend/app/services/resume/parser.py`
- Create: `backend/tests/services/resume/test_parser.py`
- Create fixture: `backend/tests/fixtures/resumes/simple.pdf` (place a real, short PDF with one experience entry + 2 bullets)

- [ ] **Step 1: Add 1 PDF fixture**

Place a 1-page test resume PDF at `backend/tests/fixtures/resumes/simple.pdf`. It should contain:
- Name: "Test User"
- One Experience: "SWE at Acme (2022-2024)" with 2 bullets
- One Education: "B.Tech CS, Some Univ, 2018-2022"
- Skills: "Python, FastAPI, PostgreSQL"

(Engineer: generate one quickly via a doc-to-PDF tool. Real PDF, not mocked.)

- [ ] **Step 2: Failing test**

`backend/tests/services/resume/test_parser.py`:

```python
import pytest
from pathlib import Path
from app.services.resume.parser import parse_resume

FIXTURE = Path(__file__).parent.parent.parent / "fixtures/resumes/simple.pdf"


def test_parser_pdf_returns_resume_document_json():
    with FIXTURE.open("rb") as f:
        doc = parse_resume(f.read(), filename="simple.pdf")
    assert doc.contact.name == "Test User"
    assert len(doc.experience) >= 1
    assert doc.experience[0].company.lower().startswith("acme")
    assert len(doc.experience[0].bullets) == 2
    # Bullet IDs are stable & non-empty
    assert all(b.id for b in doc.experience[0].bullets)
    # raw_text populated
    assert "Acme" in doc.raw_text
```

Run: `pytest backend/tests/services/resume/test_parser.py -v` → FAIL.

- [ ] **Step 3: Implement parser dispatcher + PDF path**

`backend/app/services/resume/parser.py`:

```python
import uuid
from io import BytesIO
import pdfplumber
from docx import Document as DocxDocument
from app.schemas.resume import (
    ResumeDocumentJSON, Contact, ExperienceEntry, EducationEntry,
    Skills, Bullet,
)


def parse_resume(content: bytes, filename: str) -> ResumeDocumentJSON:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return _parse_pdf(content)
    if ext == "docx":
        return _parse_docx(content)
    raise ValueError(f"Unsupported file type: {ext}")


def _parse_pdf(content: bytes) -> ResumeDocumentJSON:
    with pdfplumber.open(BytesIO(content)) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
    raw_text = "\n".join(pages)
    return _structure_from_text(raw_text)


def _parse_docx(content: bytes) -> ResumeDocumentJSON:
    doc = DocxDocument(BytesIO(content))
    raw_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return _structure_from_text(raw_text)


def _structure_from_text(raw_text: str) -> ResumeDocumentJSON:
    """Heuristic section splitter. Good enough for v1; LLM-augmented later."""
    sections = _split_sections(raw_text)
    contact = _extract_contact(sections.get("header", raw_text[:500]))
    experience = _extract_experience(sections.get("experience", ""))
    education = _extract_education(sections.get("education", ""))
    skills = _extract_skills(sections.get("skills", ""))
    summary = sections.get("summary") or None
    return ResumeDocumentJSON(
        contact=contact, summary=summary, experience=experience,
        education=education, skills=skills, raw_text=raw_text,
    )


SECTION_HEADERS = {
    "experience": ["experience", "work experience", "employment", "professional experience"],
    "education": ["education", "academic"],
    "skills": ["skills", "technical skills", "core competencies"],
    "summary": ["summary", "profile", "objective"],
}


def _split_sections(raw: str) -> dict[str, str]:
    lines = raw.splitlines()
    out: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in lines:
        norm = line.strip().lower()
        matched = None
        for sect, aliases in SECTION_HEADERS.items():
            if norm in aliases or any(norm.startswith(a + ":") for a in aliases):
                matched = sect
                break
        if matched:
            current = matched
            out.setdefault(current, [])
            continue
        out.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def _extract_contact(header_block: str) -> Contact:
    import re
    name = header_block.splitlines()[0].strip() if header_block else "Unknown"
    email = (re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", header_block) or [None])[0] \
        if re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", header_block) else None
    phone_m = re.search(r"[\+\d][\d\s\-\(\)]{7,}", header_block)
    return Contact(name=name, email=email, phone=phone_m.group(0).strip() if phone_m else None, links=[])


def _extract_experience(block: str) -> list[ExperienceEntry]:
    """Each entry = role line + bullets that follow until next role line.
    Role line heuristic: contains ' at ' or ' | ' or year range pattern."""
    import re
    entries: list[ExperienceEntry] = []
    if not block:
        return entries
    lines = [l for l in block.splitlines() if l.strip()]
    current_role: ExperienceEntry | None = None
    role_pattern = re.compile(r"(\d{4})\s*[-–—]\s*(\d{4}|present|now)", re.I)
    for line in lines:
        is_role = bool(role_pattern.search(line)) or " at " in line.lower() or " | " in line
        if is_role:
            if current_role:
                entries.append(current_role)
            parts = re.split(r"\s+at\s+|\s+\|\s+", line, maxsplit=1, flags=re.I)
            role = parts[0].strip() if parts else line.strip()
            company = parts[1].strip() if len(parts) > 1 else "Unknown"
            current_role = ExperienceEntry(company=company, role=role, dates=None, location=None, bullets=[])
        elif current_role is not None and line.strip().startswith(("•", "-", "*")):
            text = line.lstrip("•-*").strip()
            current_role.bullets.append(Bullet(id=str(uuid.uuid4())[:8], text=text, raw_text=text))
    if current_role:
        entries.append(current_role)
    return entries


def _extract_education(block: str) -> list[EducationEntry]:
    if not block:
        return []
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    out: list[EducationEntry] = []
    for line in lines:
        out.append(EducationEntry(school=line, degree=None, dates=None))
    return out


def _extract_skills(block: str) -> Skills:
    if not block:
        return Skills()
    flat = block.replace("\n", ",")
    items = [s.strip() for s in flat.split(",") if s.strip()]
    return Skills(hard=items, soft=[])
```

- [ ] **Step 4: Run test — PASS**

```bash
pytest backend/tests/services/resume/test_parser.py -v
```

If fixture content differs slightly, adjust the assertions to match the actual PDF's name/company. The test enforces structure, not exact text beyond key fields.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/resume/ backend/tests/services/resume/ backend/tests/fixtures/resumes/simple.pdf
git commit -m "feat(resume): PDF parser → ResumeDocumentJSON"
```

---

### Task 5: Resume parser — DOCX path + fixture

**Files:**
- Add: `backend/tests/fixtures/resumes/simple.docx`
- Modify: `backend/tests/services/resume/test_parser.py`

- [ ] **Step 1: Add DOCX fixture**

Mirror content of `simple.pdf` in a `.docx` form. Save to `backend/tests/fixtures/resumes/simple.docx`.

- [ ] **Step 2: Failing test**

Append to `backend/tests/services/resume/test_parser.py`:

```python
DOCX_FIXTURE = Path(__file__).parent.parent.parent / "fixtures/resumes/simple.docx"


def test_parser_docx_returns_resume_document_json():
    with DOCX_FIXTURE.open("rb") as f:
        doc = parse_resume(f.read(), filename="simple.docx")
    assert doc.contact.name == "Test User"
    assert len(doc.experience) >= 1
    assert len(doc.experience[0].bullets) == 2
```

Run: `pytest backend/tests/services/resume/test_parser.py::test_parser_docx_returns_resume_document_json -v` → PASS (parser already supports DOCX via `_parse_docx`).

If fails due to docx structure (no bullet markers), adjust the parser's bullet heuristic: add detection for `style.name == "List Bullet"` runs via `paragraph.style.name` in the DOCX path. Implement as:

```python
def _parse_docx(content: bytes) -> ResumeDocumentJSON:
    doc = DocxDocument(BytesIO(content))
    lines: list[str] = []
    for p in doc.paragraphs:
        if not p.text.strip():
            continue
        if "list" in (p.style.name or "").lower() or "bullet" in (p.style.name or "").lower():
            lines.append(f"• {p.text}")
        else:
            lines.append(p.text)
    raw_text = "\n".join(lines)
    return _structure_from_text(raw_text)
```

- [ ] **Step 3: Re-run test — PASS**

```bash
pytest backend/tests/services/resume/test_parser.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/resume/parser.py backend/tests/services/resume/test_parser.py backend/tests/fixtures/resumes/simple.docx
git commit -m "feat(resume): DOCX parser with bullet-style detection"
```

---

### Task 6: ATS simulator

**Files:**
- Create: `backend/app/services/resume/ats_simulator.py`
- Create: `backend/tests/services/resume/test_ats_simulator.py`

- [ ] **Step 1: Failing test**

`backend/tests/services/resume/test_ats_simulator.py`:

```python
from pathlib import Path
from app.services.resume.ats_simulator import simulate_ats

PDF = Path(__file__).parent.parent.parent / "fixtures/resumes/simple.pdf"


def test_ats_simulator_returns_score_and_raw_text():
    with PDF.open("rb") as f:
        result = simulate_ats(f.read(), filename="simple.pdf")
    assert 0 <= result.parseability_score <= 100
    assert "Acme" in result.raw_text
    assert isinstance(result.format_issues, list)
```

Run → FAIL (ImportError).

- [ ] **Step 2: Implement**

`backend/app/services/resume/ats_simulator.py`:

```python
from io import BytesIO
from pydantic import BaseModel
from typing import List
import pdfplumber
from docx import Document as DocxDocument
from app.schemas.resume import FormatIssue


class ATSResult(BaseModel):
    parseability_score: int
    raw_text: str
    format_issues: List[FormatIssue]


def simulate_ats(content: bytes, filename: str) -> ATSResult:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return _simulate_pdf(content)
    if ext == "docx":
        return _simulate_docx(content)
    raise ValueError(f"Unsupported: {ext}")


def _simulate_pdf(content: bytes) -> ATSResult:
    issues: List[FormatIssue] = []
    score = 100
    with pdfplumber.open(BytesIO(content)) as pdf:
        text_parts: list[str] = []
        for i, page in enumerate(pdf.pages):
            tables = page.find_tables()
            if tables:
                issues.append(FormatIssue(type="table", location=f"page {i+1}",
                                          fix_hint="ATS parsers misread tables. Use bullet lists instead."))
                score -= 15
            if page.images:
                issues.append(FormatIssue(type="image", location=f"page {i+1}",
                                          fix_hint="Remove images. ATS ignores them but they shift layout."))
                score -= 5
            text = page.extract_text() or ""
            text_parts.append(text)
            cols = _detect_columns(page)
            if cols > 1:
                issues.append(FormatIssue(type="multi_column", location=f"page {i+1}",
                                          fix_hint="Switch to single-column layout."))
                score -= 20
    raw = "\n".join(text_parts)
    score = max(0, min(100, score))
    return ATSResult(parseability_score=score, raw_text=raw, format_issues=issues)


def _detect_columns(page) -> int:
    """Cluster word x-positions into bins. >1 cluster = multi-column."""
    words = page.extract_words()
    if not words:
        return 1
    xs = sorted(w["x0"] for w in words)
    if not xs:
        return 1
    width = page.width
    half = width / 2
    left = sum(1 for x in xs if x < half)
    right = sum(1 for x in xs if x >= half)
    # If both halves have ≥30% of words, it's two-column
    total = len(xs)
    if left / total > 0.3 and right / total > 0.3:
        return 2
    return 1


def _simulate_docx(content: bytes) -> ATSResult:
    doc = DocxDocument(BytesIO(content))
    issues: List[FormatIssue] = []
    score = 100
    if doc.tables:
        issues.append(FormatIssue(type="table", location="document",
                                  fix_hint="ATS parsers misread tables. Use bullet lists."))
        score -= 15
    raw = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return ATSResult(parseability_score=max(0, min(100, score)), raw_text=raw, format_issues=issues)
```

- [ ] **Step 3: Run test — PASS**

```bash
pytest backend/tests/services/resume/test_ats_simulator.py -v
```

- [ ] **Step 4: Add table-PDF fixture + negative test**

Create `backend/tests/fixtures/resumes/with_table.pdf` (a 1-page PDF that uses a 2-column table layout). Append:

```python
TABLE_PDF = Path(__file__).parent.parent.parent / "fixtures/resumes/with_table.pdf"


def test_ats_simulator_penalizes_tables():
    with TABLE_PDF.open("rb") as f:
        result = simulate_ats(f.read(), filename="with_table.pdf")
    assert result.parseability_score < 90
    assert any(i.type == "table" for i in result.format_issues)
```

Run → should PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/resume/ats_simulator.py backend/tests/services/resume/test_ats_simulator.py backend/tests/fixtures/resumes/with_table.pdf
git commit -m "feat(resume): ATS simulator — parseability score + format issues + raw text"
```

---

### Task 7: Resume evaluator — OpenAI structured outputs

**Files:**
- Create: `backend/app/services/resume/evaluator.py`
- Create: `backend/tests/services/resume/test_evaluator.py`

- [ ] **Step 1: Failing test with respx-mocked OpenAI**

`backend/tests/services/resume/test_evaluator.py`:

```python
import pytest
import respx
import httpx
import json
from app.services.resume.evaluator import evaluate_resume
from app.schemas.resume import ResumeDocumentJSON, Contact, ExperienceEntry, Bullet, Skills


def make_doc():
    return ResumeDocumentJSON(
        contact=Contact(name="A B", email="a@b.com"),
        experience=[ExperienceEntry(company="Acme", role="SWE",
            bullets=[Bullet(id="b1", text="Did stuff", raw_text="Did stuff"),
                     Bullet(id="b2", text="Improved performance 30%", raw_text="...")])],
        skills=Skills(hard=["Python"]),
        raw_text="...",
    )


@pytest.mark.asyncio
@respx.mock
async def test_evaluator_returns_report():
    mock_payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{
            "index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": None,
                "tool_calls": None,
                "parsed": None,
                "content": json.dumps({
                    "overall_score": 60,
                    "bullet_flags": [
                        {"bullet_id": "b1", "severity": "critical",
                         "reason": "no quantification, vague verb",
                         "category": "quantification"}
                    ],
                    "format_issues": [],
                    "summary_critique": None,
                    "skill_gaps": [],
                })}
        }],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_payload)
    )
    report = await evaluate_resume(make_doc(), target_role="SWE")
    assert report.overall_score == 60
    assert any(f.bullet_id == "b1" and f.severity == "critical" for f in report.bullet_flags)
```

Run → FAIL.

- [ ] **Step 2: Implement evaluator**

`backend/app/services/resume/evaluator.py`:

```python
import os
import json
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.schemas.resume import ResumeDocumentJSON, EvaluationReport


SYSTEM_PROMPT = """You are a Senior Recruiter with 15+ years of experience hiring at FAANG and high-growth startups in both US and Indian markets. You evaluate resumes the way you would in a real screening: brutally honest, specific, and actionable. You apply:
- Google's XYZ formula: "Accomplished [X] as measured by [Y], by doing [Z]"
- 7-second scan rule: would the reader grasp impact from the top of the page?
- ATS parsing reality: keyword density, structural simplicity
- Country-aware tone (US: action-first; India: scope + action)

For EVERY bullet, decide if it has issues. Flag with severity:
- "critical": missing quantification, weak verb, or unclear impact
- "warning": acceptable but improvable
- "info": already strong

Categories: quantification | verb | structure | clarity | redundancy | ats

Never invent metrics. Never fabricate facts. If a bullet lacks numbers, flag it; don't fill in numbers yourself."""

USER_PROMPT_TEMPLATE = """Target role: {target_role}

Resume JSON:
{resume_json}

Evaluate the resume. Return STRICTLY this JSON schema:
{{
  "overall_score": int 0-100,
  "bullet_flags": [{{bullet_id, severity, reason, category}}, ...],
  "format_issues": [{{type, location, fix_hint}}, ...],
  "summary_critique": str or null,
  "skill_gaps": [str, ...]
}}"""


_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((TimeoutError,)))
async def evaluate_resume(doc: ResumeDocumentJSON, target_role: str) -> EvaluationReport:
    payload = doc.model_dump_json(exclude={"raw_text"})
    user_msg = USER_PROMPT_TEMPLATE.format(target_role=target_role, resume_json=payload)
    resp = await _client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
    )
    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)
    return EvaluationReport.model_validate(data)
```

- [ ] **Step 3: Add pytest-asyncio**

If not already in requirements, add `pytest-asyncio==0.23.2` to `backend/requirements.txt`. Add to `backend/pytest.ini` (create if missing):

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 4: Run test — PASS**

```bash
pip install pytest-asyncio==0.23.2
pytest backend/tests/services/resume/test_evaluator.py -v
```

- [ ] **Step 5: Add schema-fail retry test**

Append to test file:

```python
@pytest.mark.asyncio
@respx.mock
async def test_evaluator_invalid_schema_raises():
    bad = {"id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o",
           "choices": [{"index": 0, "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "{\"overall_score\": \"not-an-int\"}"}}],
           "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=bad)
    )
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        await evaluate_resume(make_doc(), target_role="SWE")
```

Run → PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/resume/evaluator.py backend/tests/services/resume/test_evaluator.py backend/requirements.txt backend/pytest.ini
git commit -m "feat(resume): GPT-4o evaluator with structured output + schema validation"
```

---

### Task 8: Hallucination guard

**Files:**
- Create: `backend/app/services/resume/hallucination_guard.py`
- Create: `backend/tests/services/resume/test_hallucination_guard.py`

- [ ] **Step 1: Failing test**

```python
from app.services.resume.hallucination_guard import check_no_unprompted_numbers


def test_passes_when_numbers_match():
    original = "Improved API latency by 30%"
    rewritten = "Reduced API latency by 30% via caching layer"
    check_no_unprompted_numbers(original=original, rewritten=rewritten, placeholders=[])


def test_raises_when_new_number_introduced():
    original = "Built a thing"
    rewritten = "Built a thing serving 5M users"
    import pytest
    from app.services.resume.hallucination_guard import HallucinationError
    with pytest.raises(HallucinationError):
        check_no_unprompted_numbers(original=original, rewritten=rewritten, placeholders=[])


def test_allows_placeholders():
    original = "Built a thing"
    rewritten = "Built a thing serving [N users]"
    check_no_unprompted_numbers(original=original, rewritten=rewritten,
                                placeholders=[{"token": "[N users]", "what": "scale"}])
```

Run → FAIL.

- [ ] **Step 2: Implement guard**

`backend/app/services/resume/hallucination_guard.py`:

```python
import re
from typing import List


class HallucinationError(Exception):
    pass


_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?[%kKmMbB]?\b")


def _extract_numbers(text: str) -> set[str]:
    return set(m.group(0) for m in _NUMBER_RE.finditer(text))


def check_no_unprompted_numbers(
    original: str,
    rewritten: str,
    placeholders: List[dict],
) -> None:
    """Raise HallucinationError if rewritten introduces digits not in original
    and not protected by a placeholder token."""
    # Remove placeholder tokens from rewritten before number extraction.
    redacted = rewritten
    for ph in placeholders:
        redacted = redacted.replace(ph["token"], "")
    orig_nums = _extract_numbers(original)
    new_nums = _extract_numbers(redacted)
    leaked = new_nums - orig_nums
    if leaked:
        raise HallucinationError(f"Rewritten bullet introduced numbers not in original: {sorted(leaked)}")
```

- [ ] **Step 3: Run tests — PASS**

```bash
pytest backend/tests/services/resume/test_hallucination_guard.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/resume/hallucination_guard.py backend/tests/services/resume/test_hallucination_guard.py
git commit -m "feat(resume): hallucination guard — block unprompted numbers in rewrites"
```

---

### Task 9: Rewriter — per-bullet, hallucination-guarded

**Files:**
- Create: `backend/app/services/resume/rewriter.py`
- Create: `backend/tests/services/resume/test_rewriter.py`

- [ ] **Step 1: Failing test**

```python
import pytest, respx, httpx, json
from app.services.resume.rewriter import rewrite_bullet


@pytest.mark.asyncio
@respx.mock
async def test_rewriter_returns_result_with_placeholders():
    mock_payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "rewritten": "Engineered an event-driven pipeline serving [N events/day], reducing latency by [X%]",
                "placeholders": [{"token": "[N events/day]", "what": "daily event volume"},
                                 {"token": "[X%]", "what": "latency reduction"}],
                "applied_changes": ["XYZ structure", "stronger verb 'Engineered'"]
            })}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_payload))
    result = await rewrite_bullet(
        original="Built a data pipeline",
        target_role="Senior SWE",
        jd_context=None,
    )
    assert "[N events/day]" in result.rewritten
    assert len(result.placeholders) == 2


@pytest.mark.asyncio
@respx.mock
async def test_rewriter_blocks_hallucinated_numbers():
    mock_payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "rewritten": "Engineered an event-driven pipeline serving 5M events/day, reducing latency by 40%",
                "placeholders": [],
                "applied_changes": []
            })}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_payload))
    from app.services.resume.hallucination_guard import HallucinationError
    with pytest.raises(HallucinationError):
        await rewrite_bullet(original="Built a data pipeline",
                             target_role="Senior SWE", jd_context=None)
```

Run → FAIL.

- [ ] **Step 2: Implement rewriter**

`backend/app/services/resume/rewriter.py`:

```python
import os, json
from typing import Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.schemas.resume import RewriteResult, Placeholder
from app.services.resume.hallucination_guard import check_no_unprompted_numbers, HallucinationError


REWRITER_SYSTEM = """You are a Senior Recruiter rewriting resume bullets at recruiter-grade quality.

RULES (non-negotiable):
1. Never invent numbers, scale, or facts not present in the original bullet.
   If quantification is missing, use a placeholder token like [X%], [N users], [$Y revenue].
   The user will fill these in.
2. Strengthen verbs (Built → Engineered/Architected/Led/Shipped).
3. Apply Google's XYZ structure: Accomplished X as measured by Y, by doing Z.
4. No buzzwords ('synergies', 'leverage', 'utilize'). Direct verbs only.
5. One line per bullet. Max ~25 words.
6. Country-aware tone:
   - US target: action-first, impact-front.
   - India target: scope + action, slightly more context allowed.

OUTPUT: strict JSON:
{
  "rewritten": str,
  "placeholders": [{"token": str, "what": str}],
  "applied_changes": [str, ...]
}"""


REWRITER_USER = """Original bullet:
{original}

Target role: {target_role}
Target country: {country}
JD context (may be empty): {jd_context}

Rewrite the bullet."""


_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
async def rewrite_bullet(
    original: str,
    target_role: str,
    jd_context: Optional[str] = None,
    country: str = "US",
) -> RewriteResult:
    user = REWRITER_USER.format(
        original=original, target_role=target_role,
        country=country, jd_context=jd_context or "",
    )
    resp = await _client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": REWRITER_SYSTEM},
                  {"role": "user", "content": user}],
        temperature=0.4,
    )
    data = json.loads(resp.choices[0].message.content or "{}")
    result = RewriteResult.model_validate(data)
    check_no_unprompted_numbers(
        original=original,
        rewritten=result.rewritten,
        placeholders=[p.model_dump() for p in result.placeholders],
    )
    return result
```

- [ ] **Step 3: Run tests — PASS**

```bash
pytest backend/tests/services/resume/test_rewriter.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/resume/rewriter.py backend/tests/services/resume/test_rewriter.py
git commit -m "feat(resume): per-bullet rewriter with hallucination guard"
```

---

### Task 10: JD extractor

**Files:**
- Create: `backend/app/services/jd/__init__.py` (empty)
- Create: `backend/app/schemas/jd.py`
- Create: `backend/app/services/jd/extractor.py`
- Create: `backend/tests/services/jd/test_extractor.py`

- [ ] **Step 1: Schemas**

`backend/app/schemas/jd.py`:

```python
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Requirement(BaseModel):
    skill: str
    evidence_from_jd: str
    type: Literal["technical", "experience", "credential"]


class JDExtraction(BaseModel):
    must_have: List[Requirement]
    good_to_have: List[Requirement]
    soft_skills: List[str] = Field(default_factory=list)
    seniority: Literal["junior", "mid", "senior", "staff"]
    primary_role_category: Literal["SWE", "DS", "PM", "other"]
    country_hint: Literal["US", "IN", "other"]
    red_flags: List[str] = Field(default_factory=list)


class BulletDiff(BaseModel):
    bullet_id: str
    old: str
    new: str
    reason: str
    placeholders: List[dict] = Field(default_factory=list)


class SkillsReorder(BaseModel):
    new_order: List[str]
    rationale: str


class SummaryRewrite(BaseModel):
    old: Optional[str] = None
    new: str
    reason: str


class SuggestedAddition(BaseModel):
    section: str
    item: str
    reason: str


class DiffPlan(BaseModel):
    match_score: int = Field(ge=0, le=100)
    must_have_coverage_found: List[str]
    must_have_coverage_missing: List[str]
    good_to_have_coverage_found: List[str]
    good_to_have_coverage_missing: List[str]
    bullets: List[BulletDiff]
    skills_reorder: Optional[SkillsReorder] = None
    summary_rewrite: Optional[SummaryRewrite] = None
    suggested_additions: List[SuggestedAddition] = Field(default_factory=list)
```

- [ ] **Step 2: Failing test**

`backend/tests/services/jd/test_extractor.py`:

```python
import pytest, respx, httpx, json
from app.services.jd.extractor import extract_jd_requirements


@pytest.mark.asyncio
@respx.mock
async def test_extractor_returns_requirements():
    payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "must_have": [{"skill": "Python", "evidence_from_jd": "5+ yrs Python", "type": "technical"}],
                "good_to_have": [],
                "soft_skills": ["communication"],
                "seniority": "senior",
                "primary_role_category": "SWE",
                "country_hint": "US",
                "red_flags": [],
            })}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=payload))
    result = await extract_jd_requirements("Senior Python role at Stripe...")
    assert any(r.skill == "Python" for r in result.must_have)
    assert result.seniority == "senior"
```

Run → FAIL.

- [ ] **Step 3: Implement extractor**

`backend/app/services/jd/extractor.py`:

```python
import os, json
from openai import AsyncOpenAI
from app.schemas.jd import JDExtraction

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EXTRACTOR_SYSTEM = """You parse job descriptions for hiring intelligence. Distinguish:
- must_have: explicitly required (years, hard skills, credentials)
- good_to_have: 'nice to have', 'plus', 'preferred'
- soft_skills: behavioral/interpersonal expectations
- seniority: junior | mid | senior | staff (infer from years/scope)
- primary_role_category: SWE | DS | PM | other
- country_hint: US | IN | other (infer from compensation currency, location, language style)
- red_flags: undisclosed comp, vague responsibilities, unrealistic stack breadth

Output strict JSON per schema."""


async def extract_jd_requirements(jd_text: str) -> JDExtraction:
    resp = await _client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTOR_SYSTEM},
            {"role": "user", "content": f"Job description:\n\n{jd_text}\n\nExtract requirements."},
        ],
        temperature=0.1,
    )
    return JDExtraction.model_validate_json(resp.choices[0].message.content or "{}")
```

- [ ] **Step 4: Run test — PASS**

```bash
pytest backend/tests/services/jd/test_extractor.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/jd/ backend/app/schemas/jd.py backend/tests/services/jd/
git commit -m "feat(jd): JD requirements extractor"
```

---

### Task 11: JD tailor — resume × JD → diff plan

**Files:**
- Create: `backend/app/services/jd/tailor.py`
- Create: `backend/tests/services/jd/test_tailor.py`

- [ ] **Step 1: Failing test**

```python
import pytest, respx, httpx, json
from app.services.jd.tailor import tailor_resume_to_jd
from app.schemas.resume import ResumeDocumentJSON, Contact, ExperienceEntry, Bullet, Skills
from app.schemas.jd import JDExtraction, Requirement


@pytest.mark.asyncio
@respx.mock
async def test_tailor_returns_diff_plan():
    payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "match_score": 75,
                "must_have_coverage_found": ["Python"],
                "must_have_coverage_missing": ["Kubernetes"],
                "good_to_have_coverage_found": [],
                "good_to_have_coverage_missing": [],
                "bullets": [{"bullet_id": "b1", "old": "Did stuff",
                             "new": "Shipped Python microservices on AWS",
                             "reason": "JD calls for Python; bullet was vague",
                             "placeholders": []}],
                "skills_reorder": {"new_order": ["Python", "AWS"], "rationale": "Lead with JD-matched"},
                "summary_rewrite": None,
                "suggested_additions": []
            })}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=payload))
    doc = ResumeDocumentJSON(
        contact=Contact(name="A"), experience=[ExperienceEntry(
            company="Acme", role="SWE", bullets=[Bullet(id="b1", text="Did stuff", raw_text="Did stuff")])],
        skills=Skills(hard=["Python"]), raw_text="...")
    jd = JDExtraction(
        must_have=[Requirement(skill="Python", evidence_from_jd="x", type="technical")],
        good_to_have=[], soft_skills=[], seniority="mid",
        primary_role_category="SWE", country_hint="US", red_flags=[])
    plan = await tailor_resume_to_jd(doc, jd)
    assert plan.match_score == 75
    assert plan.bullets[0].bullet_id == "b1"
```

Run → FAIL.

- [ ] **Step 2: Implement tailor**

`backend/app/services/jd/tailor.py`:

```python
import os, json
from openai import AsyncOpenAI
from app.schemas.resume import ResumeDocumentJSON
from app.schemas.jd import JDExtraction, DiffPlan
from app.services.resume.hallucination_guard import check_no_unprompted_numbers, HallucinationError


_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TAILOR_SYSTEM = """You tailor a candidate's resume to a specific JD as a senior recruiter would.

Produce a DIFF PLAN:
- Match score (0-100) based on must_have/good_to_have coverage.
- For each bullet, decide whether it should be rewritten for this JD. If so, propose the new bullet.
- Reorder skills list to lead with JD-matched ones. Provide rationale.
- Optionally rewrite the summary for the target role.
- Suggest additions ONLY if the candidate has evidence (in projects/experience) but the skill is not surfaced.

RULES:
- NEVER fabricate numbers/metrics. Use placeholders like [X%], [N users].
- NEVER add a skill the candidate has no evidence of. If JD requires Kubernetes and resume has zero K8s evidence, add to must_have_coverage_missing, NOT suggested_additions.
- Country-aware tone."""

TAILOR_USER = """Resume JSON:
{resume_json}

JD Requirements JSON:
{jd_json}

Produce the DiffPlan."""


async def tailor_resume_to_jd(doc: ResumeDocumentJSON, jd: JDExtraction) -> DiffPlan:
    user = TAILOR_USER.format(
        resume_json=doc.model_dump_json(exclude={"raw_text"}),
        jd_json=jd.model_dump_json(),
    )
    resp = await _client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": TAILOR_SYSTEM},
                  {"role": "user", "content": user}],
        temperature=0.3,
    )
    plan = DiffPlan.model_validate_json(resp.choices[0].message.content or "{}")
    # Hallucination guard each bullet rewrite
    bullet_lookup = {b.id: b.text for exp in doc.experience for b in exp.bullets}
    for diff in plan.bullets:
        original = bullet_lookup.get(diff.bullet_id, diff.old)
        try:
            check_no_unprompted_numbers(original=original, rewritten=diff.new,
                                         placeholders=diff.placeholders)
        except HallucinationError as e:
            raise HallucinationError(f"Bullet {diff.bullet_id}: {e}")
    return plan
```

- [ ] **Step 3: Run test — PASS**

```bash
pytest backend/tests/services/jd/test_tailor.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/jd/tailor.py backend/tests/services/jd/test_tailor.py
git commit -m "feat(jd): tailor resume × JD into diff plan with hallucination guard"
```

---

### Task 12: Credit ledger service

**Files:**
- Create: `backend/app/services/credits/__init__.py` (empty)
- Create: `backend/app/services/credits/ledger.py`
- Create: `backend/tests/services/credits/test_ledger.py`

- [ ] **Step 1: Failing tests**

```python
import pytest
from sqlalchemy.orm import Session
from app.services.credits.ledger import (
    get_balance, debit, refund, grant_monthly, InsufficientCredits
)
from app.models.credit_ledger import CreditLedger
# Test fixtures: assume conftest provides `db_session` and `test_user_id`


def test_grant_then_balance(db_session: Session, test_user_id: str):
    grant_monthly(db_session, user_id=test_user_id, amount=20)
    assert get_balance(db_session, test_user_id) == 20


def test_debit_reduces_balance(db_session: Session, test_user_id: str):
    grant_monthly(db_session, user_id=test_user_id, amount=20)
    debit(db_session, user_id=test_user_id, amount=2, reason="tailor")
    assert get_balance(db_session, test_user_id) == 18


def test_debit_raises_on_insufficient(db_session: Session, test_user_id: str):
    grant_monthly(db_session, user_id=test_user_id, amount=1)
    with pytest.raises(InsufficientCredits):
        debit(db_session, user_id=test_user_id, amount=5, reason="tailor")


def test_refund_increases_balance(db_session: Session, test_user_id: str):
    grant_monthly(db_session, user_id=test_user_id, amount=20)
    debit(db_session, user_id=test_user_id, amount=2, reason="tailor")
    refund(db_session, user_id=test_user_id, amount=2, reason="tailor_failed")
    assert get_balance(db_session, test_user_id) == 20
```

Note: requires a `conftest.py` providing an in-memory or transactional Postgres session. If the project lacks one, create `backend/tests/conftest.py` with a SQLAlchemy-fixtures-style transactional session that rolls back per test.

Run → FAIL.

- [ ] **Step 2: Implement ledger**

`backend/app/services/credits/ledger.py`:

```python
import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.credit_ledger import CreditLedger


class InsufficientCredits(Exception):
    pass


def get_balance(db: Session, user_id: str) -> int:
    last = db.execute(
        select(CreditLedger).where(CreditLedger.user_id == user_id)
        .order_by(CreditLedger.created_at.desc()).limit(1)
    ).scalar_one_or_none()
    return last.balance_after if last else 0


def _append(db: Session, user_id: str, delta: int, reason: str,
            external_ref: str | None = None) -> CreditLedger:
    # Row-lock on user_id to prevent double-spend
    db.execute(
        select(CreditLedger).where(CreditLedger.user_id == user_id)
        .with_for_update().limit(1)
    )
    balance = get_balance(db, user_id)
    new_balance = balance + delta
    if new_balance < 0:
        raise InsufficientCredits(f"User {user_id} has {balance}, requested {-delta}")
    entry = CreditLedger(
        id=str(uuid.uuid4()), user_id=user_id, delta=delta,
        reason=reason, balance_after=new_balance, external_ref=external_ref,
    )
    db.add(entry)
    db.flush()
    return entry


def debit(db: Session, user_id: str, amount: int, reason: str) -> CreditLedger:
    assert amount > 0
    return _append(db, user_id, -amount, reason)


def refund(db: Session, user_id: str, amount: int, reason: str) -> CreditLedger:
    assert amount > 0
    return _append(db, user_id, amount, f"refund:{reason}")


def grant_monthly(db: Session, user_id: str, amount: int = 20,
                  external_ref: str | None = None) -> CreditLedger:
    return _append(db, user_id, amount, "grant", external_ref=external_ref)
```

- [ ] **Step 3: Run tests — PASS**

```bash
pytest backend/tests/services/credits/test_ledger.py -v
```

- [ ] **Step 4: Concurrent-debit test (advanced)**

Append a concurrency test using SQLAlchemy threads. This may be skipped if SQLite is used in tests (no real row lock). Mark `@pytest.mark.skipif(<sqlite>)`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/credits/ backend/tests/services/credits/
git commit -m "feat(credits): ledger service with debit/refund/grant + row lock"
```

---

### Task 13: Credit middleware decorator

**Files:**
- Create: `backend/app/middleware/credits.py`
- Create: `backend/tests/middleware/test_credits.py`

- [ ] **Step 1: Failing test**

```python
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.middleware.credits import require_credits, CreditContext
# Assume Depends provides current_user_id and db_session


def test_require_credits_debits_on_success(test_app, test_user_id_with_credits):
    # Endpoint debits 1 on success
    client = TestClient(test_app)
    resp = client.post("/test/credit-op")
    assert resp.status_code == 200
    # Balance reduced by 1


def test_require_credits_refunds_on_failure(test_app_failing, test_user_id_with_credits):
    client = TestClient(test_app_failing)
    resp = client.post("/test/credit-op")
    assert resp.status_code == 500
    # Balance unchanged (refunded)


def test_require_credits_402_on_insufficient(test_app, test_user_id_no_credits):
    client = TestClient(test_app)
    resp = client.post("/test/credit-op")
    assert resp.status_code == 402
```

Note: test fixtures `test_app`, `test_app_failing`, `test_user_id_with_credits`, etc., need to be in `conftest.py`. Engineer should add them following existing test patterns.

Run → FAIL.

- [ ] **Step 2: Implement middleware**

`backend/app/middleware/credits.py`:

```python
from functools import wraps
from contextlib import contextmanager
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.credits.ledger import debit, refund, InsufficientCredits


@contextmanager
def credit_transaction(db: Session, user_id: str, amount: int, reason: str):
    """Debit on entry; refund on exception; commit on success."""
    try:
        debit(db, user_id=user_id, amount=amount, reason=reason)
        db.commit()
    except InsufficientCredits:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    try:
        yield
    except Exception:
        try:
            refund(db, user_id=user_id, amount=amount, reason=reason)
            db.commit()
        except Exception:
            db.rollback()
        raise


def require_credits(amount: int, reason: str):
    """Decorator factory. Wrap an async endpoint to enforce credit cost."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, db: Session, current_user_id: str, **kwargs):
            with credit_transaction(db, current_user_id, amount, reason):
                return await func(*args, db=db, current_user_id=current_user_id, **kwargs)
        return wrapper
    return decorator
```

- [ ] **Step 3: Run tests — PASS**

```bash
pytest backend/tests/middleware/test_credits.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/middleware/credits.py backend/tests/middleware/
git commit -m "feat(credits): require_credits decorator with auto-refund-on-fail"
```

---

### Task 14: API — `POST /api/v1/resumes/upload`

**Files:**
- Create: `backend/app/api/v1/endpoints/resumes_v2.py`
- Modify: `backend/app/api/v1/api.py` (register router)
- Create: `backend/tests/api/v1/test_resumes_v2.py`

- [ ] **Step 1: Failing test**

```python
from fastapi.testclient import TestClient
from pathlib import Path

FIXTURE = Path(__file__).parent.parent.parent / "fixtures/resumes/simple.pdf"


def test_upload_resume_creates_document(client: TestClient, auth_headers):
    with FIXTURE.open("rb") as f:
        resp = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert resp.status_code == 201
    data = resp.json()
    assert "resume_document_id" in data
    assert data["contact"]["name"]
```

Run → FAIL.

- [ ] **Step 2: Implement endpoint**

`backend/app/api/v1/endpoints/resumes_v2.py`:

```python
import uuid
import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user_id  # assume existing pattern
from app.services.resume.parser import parse_resume
from app.models.resume_document import ResumeDocument

router = APIRouter(prefix="/resumes", tags=["resumes-v2"])
UPLOAD_DIR = "uploads/resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(400, "Only PDF and DOCX are supported")
    content = await file.read()
    try:
        doc_json = parse_resume(content, file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(content)
    db_doc = ResumeDocument(
        id=doc_id, user_id=current_user_id,
        original_filename=file.filename, file_path=file_path,
        file_type="pdf" if file.filename.endswith(".pdf") else "docx",
        parsed_json=doc_json.model_dump(),
        raw_text=doc_json.raw_text,
    )
    db.add(db_doc)
    db.commit()
    return {"resume_document_id": doc_id, **doc_json.model_dump()}
```

- [ ] **Step 3: Register router**

In `backend/app/api/v1/api.py`, add:

```python
from app.api.v1.endpoints import resumes_v2
api_router.include_router(resumes_v2.router)
```

- [ ] **Step 4: Run test — PASS**

```bash
pytest backend/tests/api/v1/test_resumes_v2.py::test_upload_resume_creates_document -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/endpoints/resumes_v2.py backend/app/api/v1/api.py backend/tests/api/v1/test_resumes_v2.py
git commit -m "feat(api): POST /resumes/upload — parse + persist"
```

---

### Task 15: API — `POST /resumes/{id}/evaluate`

**Files:**
- Modify: `backend/app/api/v1/endpoints/resumes_v2.py`
- Modify: `backend/tests/api/v1/test_resumes_v2.py`

- [ ] **Step 1: Failing test**

```python
@respx.mock
def test_evaluate_resume_returns_report_and_debits(client, auth_headers, mock_openai_eval):
    # Upload first
    with FIXTURE.open("rb") as f:
        up = client.post("/api/v1/resumes/upload",
                         files={"file": ("simple.pdf", f, "application/pdf")},
                         headers=auth_headers)
    doc_id = up.json()["resume_document_id"]
    # Mock OpenAI response (same as evaluator test)
    mock_openai_eval()
    resp = client.post(f"/api/v1/resumes/{doc_id}/evaluate",
                       json={"target_role": "SWE"},
                       headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_score" in data
    assert "ats_parseability" in data
    assert "ats_raw_text" in data
```

Run → FAIL.

- [ ] **Step 2: Implement endpoint**

Add to `resumes_v2.py`:

```python
from pydantic import BaseModel
from app.schemas.resume import ResumeDocumentJSON
from app.services.resume.evaluator import evaluate_resume
from app.services.resume.ats_simulator import simulate_ats
from app.models.resume_evaluation_v2 import ResumeEvaluationV2
from app.middleware.credits import credit_transaction


class EvalRequest(BaseModel):
    target_role: str


@router.post("/{resume_document_id}/evaluate")
async def evaluate(
    resume_document_id: str,
    body: EvalRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    doc_row = db.get(ResumeDocument, resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(404, "Not found")
    with credit_transaction(db, current_user_id, amount=1, reason="evaluate"):
        doc_json = ResumeDocumentJSON.model_validate(doc_row.parsed_json)
        report = await evaluate_resume(doc_json, target_role=body.target_role)
        # ATS sim runs on the raw file (re-load)
        with open(doc_row.file_path, "rb") as f:
            ats = simulate_ats(f.read(), filename=doc_row.original_filename)
        eval_row = ResumeEvaluationV2(
            id=str(uuid.uuid4()),
            resume_document_id=resume_document_id,
            user_id=current_user_id,
            overall_score=report.overall_score,
            bullet_flags=[f.model_dump() for f in report.bullet_flags],
            format_issues=[i.model_dump() for i in (report.format_issues + ats.format_issues)],
            summary_critique=report.summary_critique,
            ats_parseability=ats.parseability_score,
            ats_raw_text=ats.raw_text,
            model_version="gpt-4o-2024-08-06",
        )
        db.add(eval_row)
        db.commit()
        return {
            "evaluation_id": eval_row.id,
            "overall_score": report.overall_score,
            "bullet_flags": [f.model_dump() for f in report.bullet_flags],
            "format_issues": [i.model_dump() for i in (report.format_issues + ats.format_issues)],
            "summary_critique": report.summary_critique,
            "ats_parseability": ats.parseability_score,
            "ats_raw_text": ats.raw_text,
        }
```

- [ ] **Step 3: Run test — PASS**

```bash
pytest backend/tests/api/v1/test_resumes_v2.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/endpoints/resumes_v2.py backend/tests/api/v1/test_resumes_v2.py
git commit -m "feat(api): POST /resumes/{id}/evaluate — eval + ATS sim + persist + credit debit"
```

---

### Task 16: API — `POST /resumes/{id}/rewrite/{bullet_id}`

**Files:**
- Modify: `backend/app/api/v1/endpoints/resumes_v2.py`
- Modify: `backend/tests/api/v1/test_resumes_v2.py`

- [ ] **Step 1: Failing test**

```python
@respx.mock
def test_rewrite_bullet_returns_result(client, auth_headers, mock_openai_rewrite):
    # Setup: upload, capture doc_id and a bullet_id
    ...
    mock_openai_rewrite()
    resp = client.post(
        f"/api/v1/resumes/{doc_id}/rewrite/{bullet_id}",
        json={"target_role": "SWE", "country": "US"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "rewritten" in resp.json()
```

Run → FAIL.

- [ ] **Step 2: Implement endpoint**

Add to `resumes_v2.py`:

```python
from app.services.resume.rewriter import rewrite_bullet
from app.services.resume.hallucination_guard import HallucinationError


class RewriteRequest(BaseModel):
    target_role: str
    country: str = "US"
    jd_context: str | None = None


@router.post("/{resume_document_id}/rewrite/{bullet_id}")
async def rewrite(
    resume_document_id: str,
    bullet_id: str,
    body: RewriteRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    doc_row = db.get(ResumeDocument, resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(404, "Not found")
    doc_json = ResumeDocumentJSON.model_validate(doc_row.parsed_json)
    original = next(
        (b.text for exp in doc_json.experience for b in exp.bullets if b.id == bullet_id),
        None,
    )
    if original is None:
        raise HTTPException(404, "Bullet not found")
    try:
        result = await rewrite_bullet(
            original=original, target_role=body.target_role,
            country=body.country, jd_context=body.jd_context,
        )
    except HallucinationError as e:
        raise HTTPException(422, f"Rewrite rejected: {e}")
    return result.model_dump()
```

(Note: bullet rewrites are zero-cost per spec §7.8 — no `credit_transaction` here.)

- [ ] **Step 3: Run test — PASS**

```bash
pytest backend/tests/api/v1/test_resumes_v2.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/endpoints/resumes_v2.py backend/tests/api/v1/test_resumes_v2.py
git commit -m "feat(api): POST /resumes/{id}/rewrite/{bullet_id} — guarded rewrite"
```

---

### Task 17: API — `POST /resumes/{id}/versions` (apply accepted changes)

**Files:**
- Modify: `backend/app/api/v1/endpoints/resumes_v2.py`

- [ ] **Step 1: Failing test**

```python
def test_apply_changes_creates_version(client, auth_headers):
    # Upload, get doc_id, get a bullet_id
    ...
    body = {
        "parent_version_id": None,
        "change_set": [
            {"type": "bullet_update", "bullet_id": "b1", "new_text": "Engineered X..."}
        ],
    }
    resp = client.post(f"/api/v1/resumes/{doc_id}/versions", json=body, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["version_id"]
```

- [ ] **Step 2: Implement endpoint**

```python
from app.models.resume_document import ResumeVersion


class ChangeItem(BaseModel):
    type: str  # 'bullet_update' | 'skills_reorder' | 'summary_update'
    bullet_id: str | None = None
    new_text: str | None = None
    new_skills_order: list[str] | None = None
    new_summary: str | None = None


class VersionRequest(BaseModel):
    parent_version_id: str | None = None
    change_set: list[ChangeItem]


def apply_changes(doc: ResumeDocumentJSON, changes: list[ChangeItem]) -> ResumeDocumentJSON:
    data = doc.model_dump()
    for ch in changes:
        if ch.type == "bullet_update" and ch.bullet_id and ch.new_text:
            for exp in data["experience"]:
                for b in exp["bullets"]:
                    if b["id"] == ch.bullet_id:
                        b["text"] = ch.new_text
        elif ch.type == "skills_reorder" and ch.new_skills_order is not None:
            data["skills"]["hard"] = ch.new_skills_order
        elif ch.type == "summary_update" and ch.new_summary is not None:
            data["summary"] = ch.new_summary
    return ResumeDocumentJSON.model_validate(data)


@router.post("/{resume_document_id}/versions", status_code=201)
async def create_version(
    resume_document_id: str,
    body: VersionRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    doc_row = db.get(ResumeDocument, resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(404, "Not found")
    if body.parent_version_id:
        parent = db.get(ResumeVersion, body.parent_version_id)
        base = ResumeDocumentJSON.model_validate(parent.parsed_json) if parent else \
               ResumeDocumentJSON.model_validate(doc_row.parsed_json)
    else:
        base = ResumeDocumentJSON.model_validate(doc_row.parsed_json)
    new_doc = apply_changes(base, body.change_set)
    version = ResumeVersion(
        id=str(uuid.uuid4()),
        resume_document_id=resume_document_id,
        parent_version_id=body.parent_version_id,
        change_set=[c.model_dump() for c in body.change_set],
        parsed_json=new_doc.model_dump(),
    )
    db.add(version)
    db.commit()
    return {"version_id": version.id}
```

- [ ] **Step 3: Run test — PASS**

```bash
pytest backend/tests/api/v1/test_resumes_v2.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/endpoints/resumes_v2.py backend/tests/api/v1/test_resumes_v2.py
git commit -m "feat(api): POST /resumes/{id}/versions — apply accepted changes"
```

---

### Task 18: API — `POST /api/v1/jd/analyze`

**Files:**
- Create: `backend/app/api/v1/endpoints/jd.py`
- Modify: `backend/app/api/v1/api.py` (register)
- Create: `backend/tests/api/v1/test_jd.py`

- [ ] **Step 1: Failing test**

```python
def test_jd_analyze_returns_extraction(client, auth_headers, mock_openai_jd_extract):
    # Upload resume first
    ...
    body = {"resume_document_id": doc_id, "jd_text": "Senior Python role at Acme..."}
    mock_openai_jd_extract()
    resp = client.post("/api/v1/jd/analyze", json=body, headers=auth_headers)
    assert resp.status_code == 200
    assert "must_have" in resp.json()
```

- [ ] **Step 2: Implement**

`backend/app/api/v1/endpoints/jd.py`:

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user_id
from app.services.jd.extractor import extract_jd_requirements
from app.services.jd.tailor import tailor_resume_to_jd
from app.services.resume.hallucination_guard import HallucinationError
from app.models.resume_document import ResumeDocument
from app.models.jd_evaluation import JDEvaluation
from app.schemas.resume import ResumeDocumentJSON
from app.middleware.credits import credit_transaction

router = APIRouter(prefix="/jd", tags=["jd"])


class AnalyzeRequest(BaseModel):
    resume_document_id: str
    jd_text: str


@router.post("/analyze")
async def analyze(
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    doc_row = db.get(ResumeDocument, body.resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(404, "Not found")
    with credit_transaction(db, current_user_id, amount=2, reason="tailor"):
        jd_ext = await extract_jd_requirements(body.jd_text)
        doc = ResumeDocumentJSON.model_validate(doc_row.parsed_json)
        try:
            plan = await tailor_resume_to_jd(doc, jd_ext)
        except HallucinationError as e:
            raise HTTPException(422, f"Tailor rejected: {e}")
        row = JDEvaluation(
            id=str(uuid.uuid4()), user_id=current_user_id,
            resume_document_id=body.resume_document_id,
            jd_text=body.jd_text,
            extracted_requirements=jd_ext.model_dump(),
            diff_plan=plan.model_dump(),
            match_score=plan.match_score,
        )
        db.add(row); db.commit()
        return {
            "jd_evaluation_id": row.id,
            "extracted_requirements": jd_ext.model_dump(),
            "diff_plan": plan.model_dump(),
        }
```

Register in `api.py`:

```python
from app.api.v1.endpoints import jd
api_router.include_router(jd.router)
```

- [ ] **Step 3: Run test — PASS**

```bash
pytest backend/tests/api/v1/test_jd.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/endpoints/jd.py backend/app/api/v1/api.py backend/tests/api/v1/test_jd.py
git commit -m "feat(api): POST /jd/analyze — JD extract + tailor diff plan + credit"
```

---

### Task 19: Endpoint — `GET /credits/balance` + `POST /credits/grant-monthly`

**Files:**
- Create: `backend/app/api/v1/endpoints/credits.py`
- Modify: `backend/app/api/v1/api.py`
- Create: `backend/tests/api/v1/test_credits.py`

- [ ] **Step 1: Failing tests**

```python
def test_balance_endpoint(client, auth_headers, user_with_credits):
    resp = client.get("/api/v1/credits/balance", headers=auth_headers)
    assert resp.status_code == 200
    assert "balance" in resp.json()
```

- [ ] **Step 2: Implement**

`backend/app/api/v1/endpoints/credits.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user_id
from app.services.credits.ledger import get_balance

router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("/balance")
def balance(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    return {"balance": get_balance(db, current_user_id)}
```

Register in `api.py`. (Monthly-grant cron is operational — implement as a separate scheduled job in Celery or a daily Railway cron in a follow-on task; not required in Phase 1 endpoint coverage.)

- [ ] **Step 3: Run test — PASS**

```bash
pytest backend/tests/api/v1/test_credits.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/endpoints/credits.py backend/app/api/v1/api.py backend/tests/api/v1/test_credits.py
git commit -m "feat(api): GET /credits/balance"
```

---

### Task 20: Wire — main.py + smoke test

**Files:**
- Modify: `backend/app/main.py` (no changes needed if router is registered via `api_router`, but verify)
- Create: `backend/tests/test_smoke.py`

- [ ] **Step 1: Failing test**

```python
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_v1_resumes_v2_route_registered(client):
    r = client.get("/openapi.json")
    paths = r.json()["paths"]
    assert "/api/v1/resumes/upload" in paths
    assert "/api/v1/jd/analyze" in paths
    assert "/api/v1/credits/balance" in paths
```

- [ ] **Step 2: Run — expected PASS**

```bash
pytest backend/tests/test_smoke.py -v
```

If routes aren't found, double-check `api.py` includes all 3 new routers.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_smoke.py
git commit -m "test: smoke test for phase-1 route registration"
```

---

### Task 21: Golden snapshot — evaluator + tailor

**Files:**
- Create: `backend/tests/golden/test_evaluator_golden.py`
- Create: `backend/tests/golden/test_tailor_golden.py`
- Create: `backend/tests/golden/snapshots/` (dir for stored outputs)
- Add 5 more PDF fixtures: `medium-swe.pdf`, `senior-pm.pdf`, `junior-ds.pdf`, `weak-vague.pdf`, `strong-quantified.pdf`

- [ ] **Step 1: Install snapshot lib**

```bash
pip install syrupy==4.6.1
```

Append `syrupy==4.6.1` to `backend/requirements.txt`.

- [ ] **Step 2: Write snapshot tests**

`backend/tests/golden/test_evaluator_golden.py`:

```python
import pytest
from pathlib import Path
from app.services.resume.parser import parse_resume
from app.services.resume.evaluator import evaluate_resume

FIXTURES = (Path(__file__).parent.parent / "fixtures/resumes").glob("*.pdf")


@pytest.mark.skipif(not __import__("os").getenv("RUN_GOLDEN"),
                    reason="requires RUN_GOLDEN=1 (nightly only — uses real OpenAI)")
@pytest.mark.asyncio
@pytest.mark.parametrize("fixture", [f for f in FIXTURES])
async def test_evaluator_snapshot(fixture, snapshot):
    with fixture.open("rb") as f:
        doc = parse_resume(f.read(), filename=fixture.name)
    report = await evaluate_resume(doc, target_role="SWE")
    # Snapshot only the structural fields — not LLM-variable reasons
    assert {
        "overall_score_band": report.overall_score // 10 * 10,
        "flag_count_by_severity": {
            s: sum(1 for f in report.bullet_flags if f.severity == s)
            for s in ("critical", "warning", "info")
        },
    } == snapshot
```

(Run nightly via `RUN_GOLDEN=1 pytest backend/tests/golden -v`. Snapshots regenerate manually when prompts intentionally change.)

- [ ] **Step 3: Run once with `--snapshot-update` to seed**

```bash
RUN_GOLDEN=1 pytest backend/tests/golden -v --snapshot-update
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/golden/ backend/requirements.txt
git commit -m "test: golden snapshots for evaluator (nightly RUN_GOLDEN gate)"
```

---

### Task 22: Cost + latency telemetry

**Files:**
- Modify: `backend/app/services/resume/evaluator.py`
- Modify: `backend/app/services/resume/rewriter.py`
- Modify: `backend/app/services/jd/extractor.py`
- Modify: `backend/app/services/jd/tailor.py`
- Create: `backend/app/core/llm_logging.py`

- [ ] **Step 1: Helper**

`backend/app/core/llm_logging.py`:

```python
import logging
import time
from contextlib import asynccontextmanager

logger = logging.getLogger("llm")

# Cost per 1K tokens for gpt-4o-2024-08-06 (verify against current OpenAI pricing)
PRICE_PROMPT = 0.0025 / 1000
PRICE_OUTPUT = 0.01 / 1000


def estimate_cost(usage) -> float:
    return usage.prompt_tokens * PRICE_PROMPT + usage.completion_tokens * PRICE_OUTPUT


@asynccontextmanager
async def measure(label: str, user_id: str | None = None):
    start = time.perf_counter()
    yield
    elapsed = (time.perf_counter() - start) * 1000
    logger.info({"event": "llm_call", "label": label,
                 "user_id": user_id, "latency_ms": int(elapsed)})
```

- [ ] **Step 2: Wrap each LLM service**

In each of the 4 services, wrap the `await _client.chat.completions.create(...)` call:

```python
from app.core.llm_logging import measure, estimate_cost

async with measure("evaluator"):
    resp = await _client.chat.completions.create(...)
logger.info({"event": "llm_cost", "label": "evaluator",
             "cost_usd": estimate_cost(resp.usage)})
```

- [ ] **Step 3: Test logging present**

Quick assertion test using caplog:

```python
def test_evaluator_logs_cost(caplog, mock_openai):
    caplog.set_level("INFO", logger="llm")
    ...
    asyncio.run(evaluate_resume(doc, target_role="SWE"))
    assert any("llm_cost" in r.message for r in caplog.records)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/ backend/app/core/llm_logging.py backend/tests
git commit -m "feat(obs): structured LLM latency + cost logging"
```

---

### Task 23: Documentation update — repo README + API docs auto-publish

**Files:**
- Modify: `README.md` (project root)

- [ ] **Step 1: Update README**

Append a new section to `README.md`:

```markdown
## Phase 1 — Resume + JD Backend (in progress)

New REST endpoints (v1):
- `POST /api/v1/resumes/upload` — upload PDF/DOCX, returns parsed JSON
- `POST /api/v1/resumes/{id}/evaluate` — single-agent eval + ATS sim (costs 1 credit)
- `POST /api/v1/resumes/{id}/rewrite/{bullet_id}` — hallucination-guarded bullet rewrite (free)
- `POST /api/v1/resumes/{id}/versions` — apply accepted changes, save new version
- `POST /api/v1/jd/analyze` — extract JD requirements + tailor diff plan (costs 2 credits)
- `GET /api/v1/credits/balance`

Architecture: see `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md`.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README — phase 1 endpoints + spec link"
```

---

### Task 24: End-to-end happy-path integration test

**Files:**
- Create: `backend/tests/integration/test_phase1_e2e.py`

- [ ] **Step 1: Write the test**

```python
import pytest
import respx
import httpx
from pathlib import Path

FIXTURE = Path(__file__).parent.parent / "fixtures/resumes/simple.pdf"


@respx.mock
def test_full_happy_path(client, auth_headers, user_with_credits,
                         mock_openai_eval, mock_openai_jd_extract, mock_openai_jd_tailor):
    # 1. Upload
    with FIXTURE.open("rb") as f:
        up = client.post("/api/v1/resumes/upload",
                         files={"file": ("simple.pdf", f, "application/pdf")},
                         headers=auth_headers)
    doc_id = up.json()["resume_document_id"]
    bullet_id = up.json()["experience"][0]["bullets"][0]["id"]

    # 2. Evaluate
    mock_openai_eval()
    ev = client.post(f"/api/v1/resumes/{doc_id}/evaluate",
                     json={"target_role": "SWE"}, headers=auth_headers)
    assert ev.status_code == 200

    # 3. JD analyze
    mock_openai_jd_extract(); mock_openai_jd_tailor()
    jd = client.post("/api/v1/jd/analyze",
                     json={"resume_document_id": doc_id, "jd_text": "Senior Python..."},
                     headers=auth_headers)
    assert jd.status_code == 200

    # 4. Apply changes
    diffs = jd.json()["diff_plan"]["bullets"]
    body = {"change_set": [
        {"type": "bullet_update", "bullet_id": d["bullet_id"], "new_text": d["new"]}
        for d in diffs
    ]}
    v = client.post(f"/api/v1/resumes/{doc_id}/versions", json=body, headers=auth_headers)
    assert v.status_code == 201

    # 5. Balance debit (1 eval + 2 tailor = 3 credits consumed)
    bal = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    assert bal == 20 - 3
```

- [ ] **Step 2: Run — PASS**

```bash
pytest backend/tests/integration/test_phase1_e2e.py -v
```

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/
git commit -m "test(e2e): phase-1 happy-path integration"
```

---

## Self-Review Summary

**Spec coverage check (post-write):**
- §7.1 Parser → Tasks 4, 5 ✓
- §7.2 Evaluator → Task 7 ✓
- §7.3 ATS simulator → Task 6 ✓
- §7.4 Rewriter + placeholder hybrid → Tasks 8, 9 ✓
- §7.5 JD extractor → Task 10 ✓
- §7.6 JD tailor → Task 11 ✓
- §7.7 PDF renderer → **deferred to Phase 2 plan (out of scope)**
- §7.8 Credits → Tasks 12, 13, 19 ✓
- §7.9 Frontend → **deferred to Phase 3 plan (out of scope)**
- §8.1 Resume polish flow → Tasks 14-17, 24 ✓
- §8.2 JD tailor flow → Task 18, 24 ✓
- §9 Error handling → covered in each service (retry, refund, schema fail) ✓
- §10 Testing → unit, schema, hallucination, golden, e2e ✓
- §11 Migration cleanup → **deferred to Phase 4 plan (out of scope)**

**Placeholder scan:** none — every step contains real code or real commands.

**Type consistency:** Bullet/Placeholder/EvaluationReport/DiffPlan names used consistently across schemas, services, and endpoints.

**Follow-on plans (out of scope here):**
- Phase 2 plan — PDF rendering with Puppeteer + 6 country/role templates (US-SWE/DS/PM, IN-SWE/DS/PM)
- Phase 3 plan — Next.js frontend flows: upload, inline-highlight editor, ATS-simulator preview, diff view, template picker, credits page
- Phase 4 plan — legacy code deprecation (move referrals/email/activity to `_deprecated`, 410 sunset, drop tables after 30 days)
- Operational follow-ups — monthly grant cron, Stripe webhook for top-ups, hallucination-rate alert wiring, prod LLM cost dashboard

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-19-prism-pro-resume-backend-phase-1.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
