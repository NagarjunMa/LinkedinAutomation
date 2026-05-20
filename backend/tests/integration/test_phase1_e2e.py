"""Phase 1 end-to-end happy-path integration test.

Covers the full user journey:
  upload → evaluate → jd/analyze → versions → balance check

All three OpenAI calls are mocked via respx side_effect:
  call 1 — evaluator (evaluate endpoint)
  call 2 — extractor (jd/analyze, first LLM call)
  call 3 — tailor    (jd/analyze, second LLM call)
"""
import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import json
import pytest
import respx
import httpx
from pathlib import Path
from fastapi.testclient import TestClient

FIXTURE = Path(__file__).parent.parent / "fixtures/resumes/simple.pdf"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# ---------------------------------------------------------------------------
# Canned OpenAI responses (3 sequential calls)
# ---------------------------------------------------------------------------

EVAL_RESPONSE = httpx.Response(200, json={
    "id": "eval-1",
    "object": "chat.completion",
    "created": 0,
    "model": "gpt-4o-2024-08-06",
    "choices": [{
        "index": 0,
        "finish_reason": "stop",
        "message": {
            "role": "assistant",
            "content": json.dumps({
                "overall_score": 65,
                "bullet_flags": [
                    {
                        "bullet_id": "b1",
                        "severity": "warning",
                        "reason": "Missing quantification",
                        "category": "quantification",
                    }
                ],
                "format_issues": [],
                "summary_critique": None,
                "skill_gaps": ["Kubernetes"],
            }),
        },
    }],
    "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
})

EXTRACT_RESPONSE = httpx.Response(200, json={
    "id": "extract-1",
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
    "usage": {"prompt_tokens": 80, "completion_tokens": 40, "total_tokens": 120},
})

TAILOR_RESPONSE = httpx.Response(200, json={
    "id": "tailor-1",
    "object": "chat.completion",
    "created": 0,
    "model": "gpt-4o-2024-08-06",
    "choices": [{
        "index": 0,
        "finish_reason": "stop",
        "message": {
            "role": "assistant",
            "content": json.dumps({
                "match_score": 80,
                "must_have_coverage_found": ["Python"],
                "must_have_coverage_missing": [],
                "good_to_have_coverage_found": [],
                "good_to_have_coverage_missing": [],
                "bullets": [],
                "skills_reorder": {"new_order": ["Python", "FastAPI"], "rationale": "JD match"},
                "summary_rewrite": None,
                "suggested_additions": [],
            }),
        },
    }],
    "usage": {"prompt_tokens": 120, "completion_tokens": 60, "total_tokens": 180},
})


# ---------------------------------------------------------------------------
# Helper fixture — grant 20 credits to the test user
# ---------------------------------------------------------------------------

@pytest.fixture
def user_with_credits(db_session, test_user_id):
    """Grant 20 credits to test_user_id so debit-gated endpoints succeed."""
    from app.services.credits.ledger import grant_monthly
    grant_monthly(db_session, test_user_id, 20)
    db_session.commit()
    return test_user_id


# ---------------------------------------------------------------------------
# E2E happy-path test
# ---------------------------------------------------------------------------

@respx.mock
def test_full_happy_path(client: TestClient, auth_headers, user_with_credits):
    """
    Full phase-1 user journey:
      1. Upload resume
      2. Evaluate (1 credit)
      3. JD analyze (2 credits)
      4. Apply accepted diff-plan changes → create version
      5. Check balance = 20 - 1 - 2 = 17
    """
    # -----------------------------------------------------------------------
    # 1. Upload resume (no LLM call)
    # -----------------------------------------------------------------------
    with FIXTURE.open("rb") as f:
        up = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert up.status_code == 201, f"Upload failed: {up.text}"
    up_data = up.json()
    doc_id = up_data["resume_document_id"]

    # Grab a bullet_id if the fixture produced any bullets
    bullet_id = None
    for exp in up_data.get("experience", []):
        for b in exp.get("bullets", []):
            bullet_id = b["id"]
            break
        if bullet_id:
            break

    # -----------------------------------------------------------------------
    # 2. Evaluate (LLM call #1)
    # -----------------------------------------------------------------------
    respx.route(url=OPENAI_URL).mock(
        side_effect=[EVAL_RESPONSE, EXTRACT_RESPONSE, TAILOR_RESPONSE]
    )

    ev = client.post(
        f"/api/v1/resumes/{doc_id}/evaluate",
        json={"target_role": "Senior SWE"},
        headers=auth_headers,
    )
    assert ev.status_code == 200, f"Evaluate failed: {ev.text}"
    ev_data = ev.json()
    assert "overall_score" in ev_data
    assert "ats_parseability" in ev_data
    assert ev_data["overall_score"] == 65

    # -----------------------------------------------------------------------
    # 3. JD analyze (LLM calls #2 + #3: extract + tailor)
    # -----------------------------------------------------------------------
    jd = client.post(
        "/api/v1/jd/analyze",
        json={"resume_document_id": doc_id, "jd_text": "Senior Python engineer at Acme Corp. Must have 5+ years of Python, FastAPI, and PostgreSQL experience."},
        headers=auth_headers,
    )
    assert jd.status_code == 200, f"JD analyze failed: {jd.text}"
    jd_data = jd.json()
    assert "jd_evaluation_id" in jd_data
    assert "extracted_requirements" in jd_data
    assert "diff_plan" in jd_data
    assert jd_data["extracted_requirements"]["must_have"][0]["skill"] == "Python"
    assert jd_data["diff_plan"]["match_score"] == 80

    # -----------------------------------------------------------------------
    # 4. Apply changes — create a version (no LLM call)
    # -----------------------------------------------------------------------
    diffs = jd_data["diff_plan"].get("bullets", [])
    change_set = [
        {"type": "bullet_update", "bullet_id": d["bullet_id"], "new_text": d["new"]}
        for d in diffs
    ]
    # If no bullet diffs, create a synthetic change using any available bullet_id
    if not change_set and bullet_id:
        change_set = [
            {"type": "bullet_update", "bullet_id": bullet_id,
             "new_text": "Architected distributed system serving [N] requests/day"}
        ]
    if not change_set:
        # No bullets in fixture — minimal change set
        change_set = [{"type": "summary_update", "new_text": "Experienced SWE targeting Python roles."}]

    v = client.post(
        f"/api/v1/resumes/{doc_id}/versions",
        json={"parent_version_id": None, "change_set": change_set},
        headers=auth_headers,
    )
    assert v.status_code == 201, f"Version create failed: {v.text}"
    assert v.json().get("version_id"), "version_id missing from response"

    # -----------------------------------------------------------------------
    # 5. Balance should be 20 - 1 (evaluate) - 2 (tailor) = 17
    # -----------------------------------------------------------------------
    bal_resp = client.get("/api/v1/credits/balance", headers=auth_headers)
    assert bal_resp.status_code == 200, f"Balance check failed: {bal_resp.text}"
    balance = bal_resp.json()["balance"]
    assert balance == 17, f"Expected balance 17, got {balance}"
