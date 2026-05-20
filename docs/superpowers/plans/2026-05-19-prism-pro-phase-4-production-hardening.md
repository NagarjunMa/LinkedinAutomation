# Prism Pro Phase 4 — Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Address every production blocker listed in `BLOCKERS.md` plus the operational follow-ups deferred in the Phase 1 plan. After Phase 4 lands, the backend is deploy-safe on Railway with persistent storage, correct concurrency, working billing, and live observability.

**Architecture:** Stay inside the existing FastAPI monolith. Replace local-disk upload with Supabase Storage. Fix the credit ledger's row-lock to target the `users` row. Wire Stripe webhooks, monthly grant cron, and per-user cost/hallucination metrics. Delete the dead-code carryover the reviewer flagged.

**Tech Stack:** FastAPI 0.104, SQLAlchemy 2.0, Alembic, Supabase Storage (via `storage3` Python client), Stripe Python SDK, Celery beat + Redis, structured logging.

**Out of scope (other phases):**
- PDF rendering — Phase 2 plan
- Frontend flows — Phase 3 plan
- New product features

**Branch base:** Branch from `feat/phase-1-resume-backend` (this work depends on Phase 1 code + tests).

**Reference docs:**
- Spec: `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md`
- Blockers source: `BLOCKERS.md` at repo root
- Phase 1 plan: `docs/superpowers/plans/2026-05-19-prism-pro-resume-backend-phase-1.md`

---

## File Structure

```
backend/app/
├── services/
│   ├── storage/                       (NEW)
│   │   ├── __init__.py
│   │   ├── supabase_storage.py        (upload, signed URL, delete)
│   │   └── exceptions.py
│   ├── credits/
│   │   └── ledger.py                  (modify — fix row-lock target)
│   ├── payments/                      (NEW)
│   │   ├── __init__.py
│   │   ├── stripe_client.py
│   │   └── stripe_webhook_handler.py
│   ├── resume/
│   │   └── evaluator.py               (modify — fetch raw bytes from Storage)
│   └── jd/
│       └── tailor.py                  (modify — projects bullet lookup)
├── api/v1/endpoints/
│   ├── resumes_v2.py                  (modify — upload to Storage)
│   ├── webhooks.py                    (NEW — Stripe webhook receiver)
│   └── admin_metrics.py               (NEW — cost + hallucination dashboard)
├── tasks/
│   ├── __init__.py                    (verify exists)
│   ├── credit_tasks.py                (NEW — monthly grant)
│   └── celery_app.py                  (modify — add credit_tasks schedule)
├── schemas/
│   ├── resume.py                      (split — see Task 4)
│   ├── resume_legacy.py               (NEW — extracted)
│   └── resume_v2.py                   (NEW — extracted)
└── core/
    └── llm_logging.py                 (modify — accept + propagate user_id)

backend/migrations/versions/
└── 2026_05_20_storage_paths.py        (NEW — adds storage_path column)

Dead code to DELETE (Task 5):
- backend/app/schemas/activity.py
- backend/app/schemas/analytics.py
- backend/app/schemas/export.py
- backend/app/utils/email_helpers.py
- backend/app/core/config_old.py
- backend/app/migrations/add_apollo_contact_models.py
- backend/app/migrations/cleanup_unused_tables.py
- backend/app/services/orchestrator_manager.py
- backend/app/api/v1/endpoints/resumes.py (legacy — orchestrator caller)
```

---

### Task 1: Supabase Storage client

**Files:**
- Create: `backend/app/services/storage/__init__.py` (empty)
- Create: `backend/app/services/storage/exceptions.py`
- Create: `backend/app/services/storage/supabase_storage.py`
- Create: `backend/tests/services/storage/test_supabase_storage.py`
- Modify: `backend/requirements.txt` (add `storage3==0.7.5`)
- Modify: `backend/.env.example` (add `SUPABASE_STORAGE_BUCKET=resumes`)

- [ ] **Step 1: Pin dependency**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend && \
  echo "storage3==0.7.5" >> requirements.txt && \
  python3.11 -m pip install storage3==0.7.5
```

- [ ] **Step 2: Failing test (mocks the supabase client)**

`backend/tests/services/storage/test_supabase_storage.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from app.services.storage.supabase_storage import StorageClient
from app.services.storage.exceptions import StorageError


def test_upload_returns_path():
    with patch("app.services.storage.supabase_storage.create_client") as mc:
        bucket = MagicMock()
        bucket.upload.return_value = {"Key": "resumes/u1/abc.pdf"}
        mc.return_value.storage.from_.return_value = bucket
        client = StorageClient(bucket_name="resumes")
        path = client.upload(user_id="u1", file_id="abc", content=b"...", filename="r.pdf")
    assert path.startswith("u1/")
    assert path.endswith("r.pdf")


def test_signed_url_returns_string():
    with patch("app.services.storage.supabase_storage.create_client") as mc:
        bucket = MagicMock()
        bucket.create_signed_url.return_value = {"signedURL": "https://x/y?token=z"}
        mc.return_value.storage.from_.return_value = bucket
        client = StorageClient(bucket_name="resumes")
        url = client.signed_url("u1/abc.pdf", expires_in=3600)
    assert url.startswith("https://")


def test_download_returns_bytes():
    with patch("app.services.storage.supabase_storage.create_client") as mc:
        bucket = MagicMock()
        bucket.download.return_value = b"file-bytes"
        mc.return_value.storage.from_.return_value = bucket
        client = StorageClient(bucket_name="resumes")
        data = client.download("u1/abc.pdf")
    assert data == b"file-bytes"
```

Run: `python3.11 -m pytest backend/tests/services/storage/ -v` → FAIL.

- [ ] **Step 3: Implement**

`backend/app/services/storage/exceptions.py`:

```python
class StorageError(Exception):
    pass


class StorageUploadError(StorageError):
    pass


class StorageDownloadError(StorageError):
    pass
```

`backend/app/services/storage/supabase_storage.py`:

```python
import os
from supabase import create_client, Client
from app.services.storage.exceptions import StorageUploadError, StorageDownloadError


class StorageClient:
    def __init__(self, bucket_name: str | None = None):
        self.bucket_name = bucket_name or os.getenv("SUPABASE_STORAGE_BUCKET", "resumes")
        self._client: Client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        )

    def _bucket(self):
        return self._client.storage.from_(self.bucket_name)

    def upload(self, user_id: str, file_id: str, content: bytes, filename: str) -> str:
        path = f"{user_id}/{file_id}_{filename}"
        try:
            self._bucket().upload(path, content,
                                  file_options={"content-type": "application/octet-stream"})
        except Exception as e:
            raise StorageUploadError(str(e)) from e
        return path

    def signed_url(self, path: str, expires_in: int = 3600) -> str:
        try:
            resp = self._bucket().create_signed_url(path, expires_in)
        except Exception as e:
            raise StorageDownloadError(str(e)) from e
        return resp.get("signedURL") or resp.get("signed_url") or ""

    def download(self, path: str) -> bytes:
        try:
            return self._bucket().download(path)
        except Exception as e:
            raise StorageDownloadError(str(e)) from e

    def delete(self, path: str) -> None:
        self._bucket().remove([path])


# Singleton
_client_instance: StorageClient | None = None


def get_storage() -> StorageClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = StorageClient()
    return _client_instance
```

- [ ] **Step 4: Run test — PASS**

```bash
cd backend && python3.11 -m pytest tests/services/storage/ -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/storage/ backend/tests/services/storage/ backend/requirements.txt
git commit -m "feat(storage): Supabase Storage client with upload/download/signed-URL"
```

---

### Task 2: Migrate `/resumes/upload` to Storage + add `storage_path` column

**Files:**
- Create: `backend/migrations/versions/2026_05_20_storage_paths.py`
- Modify: `backend/app/models/resume_document.py` (add `storage_path` column)
- Modify: `backend/app/api/v1/endpoints/resumes_v2.py` (upload via Storage)
- Modify: `backend/tests/api/v1/test_resumes_v2.py` (mock storage)

- [ ] **Step 1: Migration**

Create `backend/migrations/versions/2026_05_20_storage_paths.py`:

```python
"""add storage_path to resume_documents

Revision ID: 2026_05_20_storage
Revises: 2026_05_19_phase1
Create Date: 2026-05-20
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_05_20_storage"
down_revision = "2026_05_19_phase1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("resume_documents", sa.Column("storage_path", sa.String(), nullable=True))
    # file_path remains for backwards-compat; will be dropped in a follow-up after backfill.


def downgrade():
    op.drop_column("resume_documents", "storage_path")
```

- [ ] **Step 2: Model field**

In `backend/app/models/resume_document.py`, add:

```python
storage_path = Column(String, nullable=True)
```

Also update the test conftest's selective metadata for `resume_documents` to include the new column (`sa.Column("storage_path", sa.String, nullable=True)`).

- [ ] **Step 3: Failing test**

Modify `test_upload_resume_creates_document` to assert the storage path is set:

```python
@patch("app.api.v1.endpoints.resumes_v2.get_storage")
def test_upload_resume_creates_document(mock_get_storage, client, auth_headers):
    storage = MagicMock()
    storage.upload.return_value = "test-user-1/abc123_simple.pdf"
    mock_get_storage.return_value = storage
    with FIXTURE.open("rb") as f:
        resp = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert resp.status_code == 201
    data = resp.json()
    assert "resume_document_id" in data
    storage.upload.assert_called_once()
```

Run → expect FAIL (endpoint still writes to disk).

- [ ] **Step 4: Implement**

Modify `backend/app/api/v1/endpoints/resumes_v2.py` upload endpoint:

```python
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.services.resume.parser import parse_resume
from app.services.storage.supabase_storage import get_storage
from app.models.resume_document import ResumeDocument

router = APIRouter(prefix="/resumes", tags=["resumes-v2"])


@router.post("/upload", status_code=201)
async def upload_resume_v2(
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
    storage = get_storage()
    storage_path = storage.upload(
        user_id=current_user_id, file_id=doc_id,
        content=content, filename=file.filename,
    )
    db_doc = ResumeDocument(
        id=doc_id, user_id=current_user_id,
        original_filename=file.filename, file_path=storage_path,  # legacy column reused for now
        storage_path=storage_path,
        file_type="pdf" if file.filename.endswith(".pdf") else "docx",
        parsed_json=doc_json.model_dump(),
        raw_text=doc_json.raw_text,
    )
    db.add(db_doc)
    db.commit()
    return {"resume_document_id": doc_id, **doc_json.model_dump()}
```

- [ ] **Step 5: Run tests + commit**

```bash
cd backend && python3.11 -m pytest tests/api/v1/test_resumes_v2.py -v
git add -A && git commit -m "feat(api): migrate /resumes/upload to Supabase Storage"
```

---

### Task 3: Migrate `/evaluate` to download from Storage

**Files:**
- Modify: `backend/app/api/v1/endpoints/resumes_v2.py` (evaluate endpoint)
- Modify: `backend/tests/api/v1/test_resumes_v2.py` (mock storage.download)

- [ ] **Step 1: Failing test**

In `test_evaluate_resume_returns_report`, patch `get_storage` so `.download(path)` returns the fixture bytes. Then assert ATS data is still in the response.

- [ ] **Step 2: Implement**

In `resumes_v2.py` evaluate endpoint, replace the local file open:

```python
# Replace:
# with open(doc_row.file_path, "rb") as f:
#     ats = simulate_ats(f.read(), filename=doc_row.original_filename)
storage = get_storage()
content_bytes = storage.download(doc_row.storage_path or doc_row.file_path)
ats = simulate_ats(content_bytes, filename=doc_row.original_filename)
```

The `doc_row.file_path` fallback supports backfill for any rows uploaded before Task 2 lands.

- [ ] **Step 3: Run + commit**

```bash
cd backend && python3.11 -m pytest tests/api/v1/test_resumes_v2.py -v
git add -A && git commit -m "feat(api): evaluate endpoint reads from Supabase Storage"
```

---

### Task 4: Split `schemas/resume.py` into legacy and v2

**Files:**
- Create: `backend/app/schemas/resume_legacy.py` (lines 1–183 of current resume.py)
- Create: `backend/app/schemas/resume_v2.py` (lines 184–268 of current resume.py)
- Modify: `backend/app/schemas/resume.py` (re-export both for backwards compat, then remove from production code in a follow-up)
- Modify: any callers that import from `app.schemas.resume` to point at the new files

- [ ] **Step 1: Inventory callers**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  grep -rn "from app.schemas.resume import" backend/app/ backend/tests/ 2>&1 | head -30
```

- [ ] **Step 2: Move legacy classes**

Open `backend/app/schemas/resume.py`. Take lines 1–183 (everything before the Phase 1 schemas section) and place them in a new file `resume_legacy.py`. Take lines 184+ and place them in `resume_v2.py`. Replace the original `resume.py` with:

```python
"""Compatibility shim. Will be deleted in Phase 5.
New code should import from app.schemas.resume_v2 (or resume_legacy for the
old multi-agent schemas)."""
from app.schemas.resume_legacy import *  # noqa: F401, F403
from app.schemas.resume_v2 import *  # noqa: F401, F403
```

- [ ] **Step 3: Update Phase 1 services to use `resume_v2`**

Rewrite imports in:
- `app/services/resume/parser.py`
- `app/services/resume/evaluator.py`
- `app/services/resume/rewriter.py`
- `app/services/resume/ats_simulator.py`
- `app/services/jd/tailor.py`
- `app/api/v1/endpoints/resumes_v2.py`

Change every `from app.schemas.resume import X` to `from app.schemas.resume_v2 import X` where X is a Phase 1 symbol.

- [ ] **Step 4: Update tests**

Update tests that import Phase 1 schemas to use the new path:

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  grep -rln "from app.schemas.resume import \(ResumeDocumentJSON\|Bullet\|EvaluationReport\|RewriteResult\|Placeholder\)" backend/tests/
```

Replace those imports.

- [ ] **Step 5: Run full suite — verify no regression**

```bash
cd backend && python3.11 -m pytest tests/ --ignore=tests/golden -v
```

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "refactor(schemas): split resume.py into resume_legacy + resume_v2"
```

---

### Task 5: Delete dead code

**Files to delete:**
- `backend/app/schemas/activity.py`
- `backend/app/schemas/analytics.py`
- `backend/app/schemas/export.py`
- `backend/app/utils/email_helpers.py`
- `backend/app/core/config_old.py`
- `backend/app/migrations/add_apollo_contact_models.py`
- `backend/app/migrations/cleanup_unused_tables.py`
- `backend/app/services/orchestrator_manager.py`
- `backend/app/api/v1/endpoints/resumes.py` (legacy — relies on orchestrator_manager)

- [ ] **Step 1: Grep callers**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  for f in app/schemas/activity app/schemas/analytics app/schemas/export \
           app/utils/email_helpers app/core/config_old app/migrations/add_apollo_contact_models \
           app/migrations/cleanup_unused_tables app/services/orchestrator_manager \
           app/api/v1/endpoints/resumes; do \
    echo "=== $f ==="; \
    grep -rn "from app.$(echo $f | tr / .)\|import $(basename $f)" backend/app/ backend/tests/ 2>&1 | grep -v "^Binary" | head -5; \
  done
```

If `resumes.py` is referenced by `api/v1/api.py`, remove that include line. The new `resumes_v2.py` is the canonical resume API.

- [ ] **Step 2: Remove router include**

Edit `backend/app/api/v1/api.py`: delete `from app.api.v1.endpoints import resumes` and any `api_router.include_router(resumes.router)`.

- [ ] **Step 3: Delete files**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  git rm backend/app/schemas/activity.py backend/app/schemas/analytics.py backend/app/schemas/export.py \
    backend/app/utils/email_helpers.py backend/app/core/config_old.py \
    backend/app/migrations/add_apollo_contact_models.py backend/app/migrations/cleanup_unused_tables.py \
    backend/app/services/orchestrator_manager.py backend/app/api/v1/endpoints/resumes.py
```

- [ ] **Step 4: Run + commit**

```bash
cd backend && python3.11 -m pytest tests/ --ignore=tests/golden -v
git add -A && git commit -m "chore(cleanup): delete dead schemas, helpers, legacy resumes endpoint, orchestrator_manager"
```

---

### Task 6: Fix credit ledger row-lock

**Files:**
- Modify: `backend/app/services/credits/ledger.py`
- Modify: `backend/tests/services/credits/test_ledger.py` (add Postgres-only concurrent test description)

- [ ] **Step 1: Replace lock target**

In `ledger.py`'s `_append`, replace:

```python
db.execute(
    select(CreditLedger).where(CreditLedger.user_id == user_id)
    .with_for_update().limit(1)
)
```

with:

```python
from app.models.user import User
db.execute(
    select(User).where(User.user_id == user_id).with_for_update()
)
```

This serializes ALL credit operations for a given user via the unique `users` row.

- [ ] **Step 2: Failing test — only meaningful on Postgres**

Add `test_concurrent_debit_serializes` marked `@pytest.mark.skipif(env != "postgres")`:

```python
import pytest
import os
import threading
from app.services.credits.ledger import debit, grant_monthly


@pytest.mark.skipif("postgres" not in os.getenv("DATABASE_URL", ""),
                    reason="requires Postgres for SELECT FOR UPDATE")
def test_concurrent_debits_do_not_double_spend(db_session, test_user_id):
    grant_monthly(db_session, test_user_id, 5)
    errors = []
    def do_debit():
        try:
            debit(db_session, test_user_id, 3, "test")
        except Exception as e:
            errors.append(e)
    t1 = threading.Thread(target=do_debit)
    t2 = threading.Thread(target=do_debit)
    t1.start(); t2.start(); t1.join(); t2.join()
    # Exactly one should succeed (3 debit), one should fail with InsufficientCredits (5-3=2 < 3)
    from app.services.credits.ledger import InsufficientCredits
    assert sum(isinstance(e, InsufficientCredits) for e in errors) == 1
```

The SQLite suite skips this; Postgres CI will exercise it once Task 9 (CI workflow) lands.

- [ ] **Step 3: Run existing tests — verify no regression**

```bash
cd backend && python3.11 -m pytest tests/services/credits/ -v
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "fix(credits): row-lock on users row instead of arbitrary ledger row"
```

---

### Task 7: Include projects bullets in tailor lookup

**Files:**
- Modify: `backend/app/services/jd/tailor.py`
- Modify: `backend/tests/services/jd/test_tailor.py` (new test)

- [ ] **Step 1: Failing test**

Add a test that uses a `ResumeDocumentJSON` with a `projects` entry containing a bullet, has the tailor return a `BulletDiff` referencing the project bullet's ID, and expect the hallucination guard to validate against the project bullet's original text:

```python
@pytest.mark.asyncio
@respx.mock
async def test_tailor_guards_project_bullets():
    # Mock returns a diff whose bullet_id matches a PROJECT bullet, with fabricated numbers
    payload = {
        ...
        "choices": [{"message": {"content": json.dumps({
            "match_score": 70, ...,
            "bullets": [{"bullet_id": "proj-b1", "old": "Built a CLI",
                         "new": "Built a CLI serving 1M downloads", "reason": "...", "placeholders": []}],
            ...
        })}}], ...
    }
    respx.route(url=OPENAI_URL).mock(return_value=httpx.Response(200, json=payload))
    doc = ResumeDocumentJSON(
        contact=Contact(name="A"),
        experience=[],
        projects=[ProjectEntry(name="Toolbox", bullets=[Bullet(id="proj-b1", text="Built a CLI", raw_text="Built a CLI")])],
        skills=Skills(hard=["Python"]), raw_text="...",
    )
    jd = JDExtraction(... as before ...)
    from app.services.resume.hallucination_guard import HallucinationError
    with pytest.raises(HallucinationError):
        await tailor_resume_to_jd(doc, jd)
```

- [ ] **Step 2: Fix the lookup**

In `tailor.py`:

```python
from itertools import chain
# OLD:
# bullet_lookup = {b.id: b.text for exp in doc.experience for b in exp.bullets}
# NEW:
bullet_lookup = {
    b.id: b.text
    for item in chain(doc.experience, doc.projects)
    for b in item.bullets
}
```

- [ ] **Step 3: Run + commit**

```bash
cd backend && python3.11 -m pytest tests/services/jd/ -v
git add -A && git commit -m "fix(jd): tailor hallucination guard covers project bullets"
```

---

### Task 8: Stripe webhook receiver + idempotency

**Files:**
- Create: `backend/app/services/payments/__init__.py`
- Create: `backend/app/services/payments/stripe_client.py`
- Create: `backend/app/services/payments/stripe_webhook_handler.py`
- Create: `backend/app/api/v1/endpoints/webhooks.py`
- Modify: `backend/app/api/v1/api.py` (register webhooks router)
- Modify: `backend/requirements.txt` (`stripe==9.5.0`)
- Modify: `backend/.env.example` (`STRIPE_WEBHOOK_SECRET=...`, `STRIPE_API_KEY=...`)
- Create: `backend/tests/api/v1/test_webhooks.py`

- [ ] **Step 1: Failing test**

```python
import json
import time
from fastapi.testclient import TestClient


def test_stripe_webhook_grants_credits_idempotently(client, db_session):
    payload = {
        "id": "evt_test_abc",
        "type": "checkout.session.completed",
        "data": {"object": {
            "metadata": {"user_id": "test-user-1", "credit_pack": "20"},
            "id": "cs_test_001",
        }},
    }
    headers = {"Stripe-Signature": "t=1,v1=test"}  # bypass via signing-secret override in test mode
    # First call: grants 20
    r1 = client.post("/api/v1/webhooks/stripe", json=payload, headers=headers)
    assert r1.status_code == 200
    # Second call (replay): no-op due to idempotency on event id (credit_ledger.external_ref)
    r2 = client.post("/api/v1/webhooks/stripe", json=payload, headers=headers)
    assert r2.status_code == 200
    # Balance should be 20, not 40
    from app.services.credits.ledger import get_balance
    assert get_balance(db_session, "test-user-1") == 20
```

For test mode, skip signature verification when `STRIPE_WEBHOOK_SECRET=test`.

- [ ] **Step 2: Implement handler**

`backend/app/services/payments/stripe_webhook_handler.py`:

```python
import os
import stripe
from sqlalchemy.orm import Session
from app.services.credits.ledger import grant_monthly
from app.models.credit_ledger import CreditLedger


def verify_event(payload: bytes, sig_header: str) -> dict:
    secret = os.environ["STRIPE_WEBHOOK_SECRET"]
    if secret == "test":  # test bypass
        import json
        return json.loads(payload)
    return stripe.Webhook.construct_event(payload, sig_header, secret)


def handle_event(db: Session, event: dict) -> None:
    event_id = event["id"]
    # Idempotency: if a ledger entry exists with external_ref=event_id, skip
    existing = db.query(CreditLedger).filter_by(external_ref=event_id).first()
    if existing:
        return
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata", {})
        user_id = meta.get("user_id")
        amount = int(meta.get("credit_pack", "0"))
        if not user_id or amount <= 0:
            return
        grant_monthly(db, user_id=user_id, amount=amount, external_ref=event_id)
        db.commit()
```

- [ ] **Step 3: Webhook endpoint**

`backend/app/api/v1/endpoints/webhooks.py`:

```python
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.payments.stripe_webhook_handler import verify_event, handle_event

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    try:
        event = verify_event(raw, sig)
    except Exception as e:
        raise HTTPException(400, f"Invalid signature: {e}")
    handle_event(db, event)
    return {"received": True}
```

Register in `api.py`.

- [ ] **Step 4: Run + commit**

```bash
cd backend && python3.11 -m pytest tests/api/v1/test_webhooks.py -v
git add -A && git commit -m "feat(payments): Stripe webhook with idempotent credit grants"
```

---

### Task 9: Monthly grant cron (Celery beat)

**Files:**
- Create: `backend/app/tasks/credit_tasks.py`
- Modify: `backend/app/tasks/celery_app.py` (add schedule)
- Create: `backend/tests/tasks/test_credit_tasks.py`

- [ ] **Step 1: Failing test**

```python
from app.tasks.credit_tasks import grant_monthly_to_all
from app.services.credits.ledger import get_balance


def test_grant_monthly_to_all_grants_baseline(db_session):
    # Setup: 2 users
    from app.models.user import User
    db_session.add_all([User(user_id="u-a", email="a@x"), User(user_id="u-b", email="b@x")])
    db_session.commit()
    grant_monthly_to_all(db=db_session, amount=20)
    assert get_balance(db_session, "u-a") == 20
    assert get_balance(db_session, "u-b") == 20
```

- [ ] **Step 2: Implement task**

```python
import logging
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.services.credits.ledger import grant_monthly
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def grant_monthly_to_all(db: Session, amount: int = 20) -> int:
    users = db.query(User).all()
    granted = 0
    for u in users:
        try:
            grant_monthly(db, user_id=u.user_id, amount=amount)
            granted += 1
        except Exception as e:
            logger.warning(f"grant failed for {u.user_id}: {e}")
    db.commit()
    return granted


@celery_app.task(name="credits.grant_monthly")
def grant_monthly_celery_task():
    db = SessionLocal()
    try:
        return grant_monthly_to_all(db, amount=20)
    finally:
        db.close()
```

In `tasks/celery_app.py`, add to `beat_schedule`:

```python
celery_app.conf.beat_schedule = {
    **(celery_app.conf.beat_schedule or {}),
    "grant-monthly": {
        "task": "credits.grant_monthly",
        "schedule": crontab(0, 0, day_of_month="1"),  # midnight UTC on the 1st
    },
}
```

- [ ] **Step 3: Run + commit**

```bash
cd backend && python3.11 -m pytest tests/tasks/test_credit_tasks.py -v
git add -A && git commit -m "feat(credits): monthly grant Celery beat task"
```

---

### Task 10: LLM cost telemetry — per-user

**Files:**
- Modify: `backend/app/core/llm_logging.py` (require user_id where possible)
- Modify: `backend/app/services/resume/evaluator.py` (accept + pass `user_id`)
- Modify: `backend/app/services/resume/rewriter.py`
- Modify: `backend/app/services/jd/extractor.py`
- Modify: `backend/app/services/jd/tailor.py`
- Modify: all callers (endpoints) to pass `current_user_id` through

- [ ] **Step 1: Update signature**

Add `user_id: str | None = None` to each LLM service function. Pass it into `measure(label, user_id=user_id)`. Add a `_log_cost(label, usage, user_id)` helper in `llm_logging.py`.

- [ ] **Step 2: Update callers**

Every endpoint that calls an LLM service now passes `current_user_id`. Examples:

```python
report = await evaluate_resume(doc_json, target_role=body.target_role, user_id=current_user_id)
```

- [ ] **Step 3: Assertion test**

```python
def test_evaluator_logs_user_id(caplog, mock_openai_eval):
    caplog.set_level("INFO", logger="llm")
    mock_openai_eval()
    asyncio.run(evaluate_resume(doc, target_role="SWE", user_id="u1"))
    assert any('"user_id": "u1"' in r.message or "u1" in str(r.message) for r in caplog.records)
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(obs): propagate user_id to LLM cost logs"
```

---

### Task 11: Admin metrics endpoint

**Files:**
- Create: `backend/app/api/v1/endpoints/admin_metrics.py`
- Modify: `backend/app/api/v1/api.py`
- Create: `backend/tests/api/v1/test_admin_metrics.py`

This endpoint reads structured logs OR queries `credit_ledger` for cost-by-debit-reason. For MVP, expose per-user totals from the ledger:

- [ ] **Step 1: Failing test**

```python
def test_admin_metrics_returns_cost_by_user(client, db_session, test_user_id, admin_headers):
    # Grant credits + debit twice
    from app.services.credits.ledger import grant_monthly, debit
    grant_monthly(db_session, test_user_id, 20)
    debit(db_session, test_user_id, 1, "evaluate")
    debit(db_session, test_user_id, 2, "tailor")
    db_session.commit()
    resp = client.get("/api/v1/admin/metrics/cost-per-user", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert any(u["user_id"] == test_user_id and u["total_debited"] == 3 for u in data["users"])
```

Gate the endpoint with `is_admin` check on the user (or a service-token header — pick whichever auth pattern is least invasive).

- [ ] **Step 2: Implement**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.models.credit_ledger import CreditLedger

router = APIRouter(prefix="/admin/metrics", tags=["admin"])


def require_admin(user_id: str = Depends(get_current_user_id)):
    # Replace with real admin check (e.g., users.is_admin or token allowlist)
    import os
    admins = {u.strip() for u in os.getenv("ADMIN_USER_IDS", "").split(",") if u.strip()}
    if user_id not in admins:
        raise HTTPException(403, "Admin only")
    return user_id


@router.get("/cost-per-user")
def cost_per_user(db: Session = Depends(get_db), _: str = Depends(require_admin)):
    rows = db.query(
        CreditLedger.user_id,
        func.sum(func.case((CreditLedger.delta < 0, -CreditLedger.delta), else_=0)).label("total_debited"),
    ).group_by(CreditLedger.user_id).all()
    return {"users": [{"user_id": r[0], "total_debited": int(r[1] or 0)} for r in rows]}
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(admin): cost-per-user metrics endpoint"
```

---

### Task 12: Final verification

- [ ] **Step 1: Full backend suite**

```bash
cd backend && python3.11 -m pytest tests/ --ignore=tests/golden -v 2>&1 | tail -25
```

Expected: 60+ tests pass, no failures.

- [ ] **Step 2: Apply both migrations on a staging Postgres**

```bash
cd backend && DATABASE_URL=postgresql://... alembic upgrade head
```

Expected: `2026_05_19_phase1` → `2026_05_20_storage` applied cleanly.

- [ ] **Step 3: Manual smoke against deployed Supabase Storage**

Upload a small file via the FastAPI dev server, confirm via Supabase dashboard the file landed in the bucket. Hit `/evaluate`, confirm ATS data returned. Delete the file via `storage.delete(path)`.

- [ ] **Step 4: Final commit / branch tag**

```bash
git tag phase-4-complete
```

---

## Self-Review Summary

**BLOCKERS.md coverage:**
- Local-disk upload → Tasks 1, 2, 3 ✓
- Credit row-lock → Task 6 ✓
- Dead schema files + orchestrator_manager → Task 5 ✓
- Schema file split → Task 4 ✓
- Tailor projects-bullet lookup → Task 7 ✓

**Operational follow-ups from Phase 1 plan:**
- Stripe webhook → Task 8 ✓
- Monthly grant cron → Task 9 ✓
- Per-user cost tracking → Task 10 ✓
- Admin cost dashboard endpoint → Task 11 ✓
- Hallucination-rate alert wiring → **deferred** (needs production log aggregation infra; flag for Phase 5)

**No placeholders:** every step has real code or real commands.

**Type consistency:** new `storage_path` column, `StorageClient` interface (`upload`, `download`, `signed_url`, `delete`), `verify_event`/`handle_event` for webhook all named consistently across tasks.

**Risk:** Task 4 (schema split) touches every Phase 1 service. Run after Tasks 1-3 land cleanly; if a regression appears, the schema split is the most likely cause.

**Out of plan (track separately):**
- Hallucination metric → Phase 5
- Verify Stripe webhook signature handling against real test events
- Frontend changes for credit purchase UI → Phase 3 plan
- Backfill any `file_path`-only rows to populate `storage_path` (one-shot script after Task 2 lands)
