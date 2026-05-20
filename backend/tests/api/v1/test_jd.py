"""Tests for JD analyze endpoint (Task 18)."""
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
# Canned OpenAI payloads
# ---------------------------------------------------------------------------

EXTRACT_PAYLOAD = {
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
                "must_have": [
                    {"skill": "Python", "evidence_from_jd": "5+ yrs Python", "type": "technical"}
                ],
                "good_to_have": [],
                "soft_skills": ["communication"],
                "seniority": "senior",
                "primary_role_category": "SWE",
                "country_hint": "US",
                "red_flags": [],
            }),
        },
    }],
    "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
}

TAILOR_PAYLOAD = {
    "id": "y",
    "object": "chat.completion",
    "created": 0,
    "model": "gpt-4o-2024-08-06",
    "choices": [{
        "index": 0,
        "finish_reason": "stop",
        "message": {
            "role": "assistant",
            "content": json.dumps({
                "match_score": 75,
                "must_have_coverage_found": ["Python"],
                "must_have_coverage_missing": [],
                "good_to_have_coverage_found": [],
                "good_to_have_coverage_missing": [],
                "bullets": [],
                "skills_reorder": None,
                "summary_rewrite": None,
                "suggested_additions": [],
            }),
        },
    }],
    "usage": {"prompt_tokens": 100, "completion_tokens": 60, "total_tokens": 160},
}


# ---------------------------------------------------------------------------
# Task 18: POST /api/v1/jd/analyze
# ---------------------------------------------------------------------------

@respx.mock
def test_jd_analyze_returns_extraction_and_diff(
    client: TestClient, auth_headers, db_session, test_user_id
):
    """POST /jd/analyze costs 2 credits; returns extraction + diff plan."""
    # Grant credits first (endpoint costs 2)
    from app.services.credits.ledger import grant_monthly
    grant_monthly(db_session, test_user_id, 10)
    db_session.commit()

    # Upload a resume first to get a resume_document_id
    with FIXTURE.open("rb") as f:
        up = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert up.status_code == 201, up.text
    doc_id = up.json()["resume_document_id"]

    # Mock both LLM calls (extractor then tailor) using side_effect list
    respx.route(url=OPENAI_URL).mock(
        side_effect=[
            httpx.Response(200, json=EXTRACT_PAYLOAD),
            httpx.Response(200, json=TAILOR_PAYLOAD),
        ]
    )

    resp = client.post(
        "/api/v1/jd/analyze",
        json={"resume_document_id": doc_id, "jd_text": "Senior Python role at Acme. Must have 5+ years of Python and FastAPI experience."},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "jd_evaluation_id" in data
    assert "extracted_requirements" in data
    assert "diff_plan" in data
    assert data["extracted_requirements"]["must_have"][0]["skill"] == "Python"
    assert data["diff_plan"]["match_score"] == 75


@respx.mock
def test_jd_analyze_returns_402_when_no_credits(
    client: TestClient, auth_headers
):
    """Without credits the endpoint must return 402."""
    # No grant — user has 0 credits

    # Upload a resume
    with FIXTURE.open("rb") as f:
        up = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert up.status_code == 201, up.text
    doc_id = up.json()["resume_document_id"]

    # No LLM mocks needed — should 402 before any LLM call
    JD_LONG = "Senior Python engineer required. Must have 5+ years of experience with Python, FastAPI, and Postgres."
    resp = client.post(
        "/api/v1/jd/analyze",
        json={"resume_document_id": doc_id, "jd_text": JD_LONG},
        headers=auth_headers,
    )
    assert resp.status_code == 402, resp.text


def test_jd_analyze_returns_404_for_unknown_document(
    client: TestClient, auth_headers
):
    """Non-existent resume_document_id returns 404."""
    JD_LONG = "Senior Python engineer required. Must have 5+ years of experience with Python, FastAPI, and Postgres."
    resp = client.post(
        "/api/v1/jd/analyze",
        json={"resume_document_id": "nonexistent-id", "jd_text": JD_LONG},
        headers=auth_headers,
    )
    assert resp.status_code == 404, resp.text


def test_jd_analyze_rejects_short_jd_text(client: TestClient, auth_headers):
    """jd_text shorter than 50 chars returns 422 before any credit debit."""
    resp = client.post(
        "/api/v1/jd/analyze",
        json={"resume_document_id": "any-id", "jd_text": "Too short"},
        headers=auth_headers,
    )
    assert resp.status_code == 422, resp.text
