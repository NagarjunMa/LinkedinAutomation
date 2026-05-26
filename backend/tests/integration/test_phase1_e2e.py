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
def test_full_happy_path(client: TestClient, auth_headers, user_with_credits, db_session):
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
    SUMMARY_NEW = "Experienced SWE targeting Python roles."
    if not change_set:
        # No bullets in fixture — minimal change set using correct field name
        change_set = [{"type": "summary_update", "new_summary": SUMMARY_NEW}]

    v = client.post(
        f"/api/v1/resumes/{doc_id}/versions",
        json={"parent_version_id": None, "change_set": change_set},
        headers=auth_headers,
    )
    assert v.status_code == 201, f"Version create failed: {v.text}"
    version_id = v.json().get("version_id")
    assert version_id, "version_id missing from response"

    # Assert summary was persisted correctly when summary_update was applied
    if len(change_set) == 1 and change_set[0]["type"] == "summary_update":
        from app.models.resume_document import ResumeVersion
        ver_row = db_session.get(ResumeVersion, version_id)
        assert ver_row is not None, "Version row not found in DB"
        assert ver_row.parsed_json["summary"] == SUMMARY_NEW, (
            f"Expected summary '{SUMMARY_NEW}', got '{ver_row.parsed_json['summary']}'"
        )

    # -----------------------------------------------------------------------
    # 5. Balance should be 20 - 1 (evaluate) - 2 (tailor) = 17
    # -----------------------------------------------------------------------
    bal_resp = client.get("/api/v1/credits/balance", headers=auth_headers)
    assert bal_resp.status_code == 200, f"Balance check failed: {bal_resp.text}"
    balance = bal_resp.json()["balance"]
    assert balance == 17, f"Expected balance 17, got {balance}"


# ---------------------------------------------------------------------------
# Task 15: Full apply → export → analytics e2e test
# ---------------------------------------------------------------------------

def test_apply_then_export_e2e(client, auth_headers, db_session, test_user_id, user_with_credits):
    """Upload → jd/apply → exports → analytics funnel check.

    Seeds a ResumeDocument and JDEvaluation directly (skips upload + analyze LLM
    calls for speed). Mocks render_pdf_from_doc + storage so no Playwright or
    Supabase calls are made.

    Assertions:
    - apply endpoint returns 200 + correct filename_hint suffix
    - export endpoint returns 201 + download_url + filename
    - analytics/jd-progress returns versions_count == 1 + exports_count == 1
    """
    import uuid
    from unittest.mock import patch
    from app.models.resume_document import ResumeDocument
    from app.models.jd_evaluation import JDEvaluation

    # -----------------------------------------------------------------------
    # Seed: one ResumeDocument + one JDEvaluation (Asha Sharma applying to Stripe)
    # -----------------------------------------------------------------------
    doc_id = str(uuid.uuid4())
    db_session.add(ResumeDocument(
        id=doc_id,
        user_id=test_user_id,
        original_filename="asha-resume.pdf",
        file_path="/tmp/ignored.pdf",
        file_type="pdf",
        parsed_json={
            "contact": {"name": "Asha Sharma", "email": "asha@example.com", "links": []},
            "summary": "Senior SWE with 6 years of Python experience.",
            "experience": [{
                "company": "Acme",
                "role": "Senior SWE",
                "bullets": [{"id": "b1", "text": "Built distributed systems at scale.", "raw_text": "Built distributed systems at scale."}],
            }],
            "education": [],
            "skills": {"hard": ["Python", "FastAPI"], "soft": ["communication"]},
            "projects": [],
            "certifications": [],
            "raw_text": "Asha Sharma resume text",
        },
        raw_text="Asha Sharma resume text",
    ))
    jd_id = str(uuid.uuid4())
    db_session.add(JDEvaluation(
        id=jd_id,
        user_id=test_user_id,
        resume_document_id=doc_id,
        jd_text="Senior SWE at Stripe (US). Must have 5+ years Python, FastAPI, AWS.",
        extracted_requirements={
            "company_name": "Stripe",
            "country_hint": "US",
            "primary_role_category": "SWE",
            "must_have": [{"skill": "Python", "evidence_from_jd": "5+ yrs", "type": "technical"}],
            "good_to_have": [],
            "soft_skills": [],
            "seniority": "senior",
            "red_flags": [],
        },
        diff_plan={
            "match_score": 75,
            "must_have_coverage_found": ["Python"],
            "must_have_coverage_missing": [],
            "good_to_have_coverage_found": [],
            "good_to_have_coverage_missing": [],
            "bullets": [],
            "skills_reorder": None,
            "summary_rewrite": None,
            "suggested_additions": [],
        },
        match_score=75,
    ))
    db_session.commit()

    # -----------------------------------------------------------------------
    # 1. Apply — creates a ResumeVersion linked to the JDEvaluation
    # -----------------------------------------------------------------------
    apply_resp = client.post(
        f"/api/v1/jd/{jd_id}/apply",
        json={
            "accepted_changes": [
                {"type": "bullet_update", "bullet_id": "b1",
                 "new_text": "Shipped Python services serving 1M+ req/day on AWS"}
            ],
        },
        headers=auth_headers,
    )
    assert apply_resp.status_code == 200, f"Apply failed: {apply_resp.text}"
    apply_data = apply_resp.json()
    version_id = apply_data["version_id"]
    assert version_id, "version_id missing from apply response"

    # filename_hint format: <name-slug>-<company-slug>-<role>.pdf
    # e.g. "asha-sharma-stripe-swe.pdf" for Asha Sharma + Stripe + SWE
    filename_hint = apply_data["filename_hint"]
    assert "asha-sharma" in filename_hint, f"Expected 'asha-sharma' in filename_hint, got: {filename_hint}"
    assert "stripe" in filename_hint, f"Expected 'stripe' in filename_hint, got: {filename_hint}"
    assert filename_hint.endswith(".pdf"), f"filename_hint should end with .pdf, got: {filename_hint}"

    # -----------------------------------------------------------------------
    # 2. Export — mock render + storage; call POST /api/v1/exports
    # -----------------------------------------------------------------------
    with patch("app.api.v1.endpoints.exports.render_pdf_from_doc", return_value=b"%PDF-1.4 stub"), \
         patch("app.api.v1.endpoints.exports.upload_pdf", return_value=None), \
         patch("app.api.v1.endpoints.exports.signed_url", return_value="https://signed.example/asha-stripe.pdf?token=abc"):

        export_resp = client.post(
            "/api/v1/exports",
            json={
                "resume_document_id": doc_id,
                "resume_version_id": version_id,
                "country": "US",
                "role_template": "swe",
                "filename": filename_hint,
            },
            headers=auth_headers,
        )

    assert export_resp.status_code == 201, f"Export failed: {export_resp.text}"
    export_data = export_resp.json()
    assert export_data["download_url"].startswith("https://"), (
        f"Expected download_url to start with https://, got: {export_data['download_url']}"
    )
    assert export_data["filename"] == filename_hint, (
        f"Expected filename '{filename_hint}', got '{export_data['filename']}'"
    )

    # -----------------------------------------------------------------------
    # 3. Analytics — /api/v1/analytics/jd-progress should show 1 version + 1 export
    # -----------------------------------------------------------------------
    progress_resp = client.get("/api/v1/analytics/jd-progress", headers=auth_headers)
    assert progress_resp.status_code == 200, f"Analytics failed: {progress_resp.text}"
    jd_rows = progress_resp.json()
    assert isinstance(jd_rows, list), "Expected a list from jd-progress"

    matching = [r for r in jd_rows if r["jd_evaluation_id"] == jd_id]
    assert len(matching) == 1, f"Expected exactly 1 row for jd_id={jd_id}, got {matching}"
    row = matching[0]
    assert row["versions_count"] == 1, f"Expected versions_count=1, got {row['versions_count']}"
    assert row["exports_count"] == 1, f"Expected exports_count=1, got {row['exports_count']}"
