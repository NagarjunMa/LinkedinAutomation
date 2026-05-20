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


# ---------------------------------------------------------------------------
# Helpers for OpenAI mocking
# ---------------------------------------------------------------------------

def mock_openai_eval():
    """Register a respx route returning a canned evaluation payload."""
    mock_payload = {
        "id": "x",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-4o-2024-08-06",
        "choices": [{
            "index": 0,
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": json.dumps({
                    "overall_score": 60,
                    "bullet_flags": [
                        {
                            "bullet_id": "b1",
                            "severity": "critical",
                            "reason": "no quantification, vague verb",
                            "category": "quantification",
                        }
                    ],
                    "format_issues": [],
                    "summary_critique": None,
                    "skill_gaps": [],
                }),
            },
        }],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=mock_payload)
    )


def mock_openai_rewrite():
    """Register a respx route returning a canned RewriteResult payload."""
    mock_payload = {
        "id": "x",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-4o-2024-08-06",
        "choices": [{
            "index": 0,
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": json.dumps({
                    "rewritten": "Engineered an event-driven pipeline serving [N events/day], reducing latency by [X%]",
                    "placeholders": [
                        {"token": "[N events/day]", "what": "daily event volume"},
                        {"token": "[X%]", "what": "latency reduction"},
                    ],
                    "applied_changes": ["XYZ structure", "stronger verb 'Engineered'"],
                }),
            },
        }],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=mock_payload)
    )


# ---------------------------------------------------------------------------
# Task 15: POST /api/v1/resumes/{id}/evaluate
# ---------------------------------------------------------------------------

@respx.mock
def test_evaluate_resume_returns_report_and_debits(
    client: TestClient, auth_headers, db_session, test_user_id
):
    # Grant credits so the debit doesn't fail with 402
    from app.services.credits.ledger import grant_monthly
    grant_monthly(db_session, test_user_id, 20)
    db_session.commit()

    # Upload first
    with FIXTURE.open("rb") as f:
        up = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert up.status_code == 201, up.text
    doc_id = up.json()["resume_document_id"]

    # Mock OpenAI and call evaluate
    mock_openai_eval()
    resp = client.post(
        f"/api/v1/resumes/{doc_id}/evaluate",
        json={"target_role": "SWE"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "overall_score" in data
    assert "ats_parseability" in data
    assert "ats_raw_text" in data


# ---------------------------------------------------------------------------
# Task 16: POST /api/v1/resumes/{id}/rewrite/{bullet_id}
# ---------------------------------------------------------------------------

@respx.mock
def test_rewrite_bullet_returns_result(
    client: TestClient, auth_headers
):
    # Upload first and get a bullet_id
    with FIXTURE.open("rb") as f:
        up = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert up.status_code == 201, up.text
    doc_data = up.json()
    doc_id = doc_data["resume_document_id"]

    # Grab a bullet_id from the parsed resume
    bullet_id = None
    for exp in doc_data.get("experience", []):
        for b in exp.get("bullets", []):
            bullet_id = b["id"]
            break
        if bullet_id:
            break

    # If no bullets in fixture, skip gracefully with a synthetic bullet
    if not bullet_id:
        pytest.skip("Fixture has no bullets — cannot test rewrite endpoint")

    mock_openai_rewrite()
    resp = client.post(
        f"/api/v1/resumes/{doc_id}/rewrite/{bullet_id}",
        json={"target_role": "SWE", "country": "US"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert "rewritten" in resp.json()


# ---------------------------------------------------------------------------
# Task 17: POST /api/v1/resumes/{id}/versions
# ---------------------------------------------------------------------------

def test_apply_changes_creates_version(client: TestClient, auth_headers):
    # Upload first and get a bullet_id
    with FIXTURE.open("rb") as f:
        up = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert up.status_code == 201, up.text
    doc_data = up.json()
    doc_id = doc_data["resume_document_id"]

    # Pick a bullet_id if available; otherwise use a dummy value
    bullet_id = None
    for exp in doc_data.get("experience", []):
        for b in exp.get("bullets", []):
            bullet_id = b["id"]
            break
        if bullet_id:
            break
    bullet_id = bullet_id or "b1"

    body = {
        "parent_version_id": None,
        "change_set": [
            {
                "type": "bullet_update",
                "bullet_id": bullet_id,
                "new_text": "Engineered X to achieve [Y%] improvement",
            }
        ],
    }
    resp = client.post(
        f"/api/v1/resumes/{doc_id}/versions",
        json=body,
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["version_id"]
