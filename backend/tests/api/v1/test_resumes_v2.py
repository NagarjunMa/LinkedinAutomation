"""Tests for resumes_v2 API endpoints (Tasks 14-17)."""
import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import json
import pytest
import respx
import httpx
from pathlib import Path
from fastapi.testclient import TestClient

FIXTURE = Path(__file__).parent.parent.parent / "fixtures/resumes/simple.pdf"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


# ---------------------------------------------------------------------------
# Task 14: POST /api/v1/resumes/upload
# ---------------------------------------------------------------------------

def test_upload_resume_creates_document(client: TestClient, auth_headers):
    with FIXTURE.open("rb") as f:
        resp = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "resume_document_id" in data
    assert data["contact"]["name"]


def test_upload_resume_rejects_unsupported_type(client: TestClient, auth_headers):
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", b"some text", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 400
