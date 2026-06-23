"""Tests for resumes_v2 API endpoints (Tasks 14-17)."""
import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import json
import uuid
import pytest
import respx
import httpx
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

FIXTURE = Path(__file__).parent.parent.parent / "fixtures/resumes/simple.pdf"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


# ---------------------------------------------------------------------------
# Task 14: POST /api/v1/resumes/upload  (Phase 4: uses Supabase Storage)
# ---------------------------------------------------------------------------

@patch("app.api.v1.endpoints.resumes_v2.get_storage")
def test_upload_resume_creates_document(mock_get_storage, client: TestClient, auth_headers):
    storage = MagicMock()
    storage.upload.return_value = "test-user-1/abc123_simple.pdf"
    mock_get_storage.return_value = storage
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
    storage.upload.assert_called_once()


def test_upload_resume_rejects_unsupported_type(client: TestClient, auth_headers):
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", b"some text", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@patch("app.api.v1.endpoints.resumes_v2.get_storage")
def test_list_and_get_resume_documents_for_profile_page(mock_get_storage, client: TestClient, auth_headers):
    storage = MagicMock()
    storage.upload.return_value = "test-user-1/abc123_simple.pdf"
    mock_get_storage.return_value = storage

    with FIXTURE.open("rb") as f:
        upload = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert upload.status_code == 201, upload.text
    doc_id = upload.json()["resume_document_id"]

    list_response = client.get("/api/v1/resumes/list", headers=auth_headers)

    assert list_response.status_code == 200, list_response.text
    list_data = list_response.json()
    assert list_data["total_count"] == 1
    assert list_data["resumes"][0]["id"] == doc_id
    assert list_data["resumes"][0]["resume_document_id"] == doc_id
    assert list_data["resumes"][0]["original_filename"] == "simple.pdf"
    assert list_data["resumes"][0]["evaluation_status"] == "pending"

    detail_response = client.get(f"/api/v1/resumes/{doc_id}", headers=auth_headers)

    assert detail_response.status_code == 200, detail_response.text
    detail_data = detail_response.json()
    assert detail_data["resume"]["id"] == doc_id
    assert detail_data["evaluation"] is None


@patch("app.api.v1.endpoints.resumes_v2.get_storage")
def test_delete_resume_document_removes_v2_rows(mock_get_storage, client: TestClient, auth_headers):
    storage = MagicMock()
    storage.upload.return_value = "test-user-1/abc123_simple.pdf"
    mock_get_storage.return_value = storage

    with FIXTURE.open("rb") as f:
        upload = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert upload.status_code == 201, upload.text
    doc_id = upload.json()["resume_document_id"]

    delete_response = client.delete(f"/api/v1/resumes/{doc_id}", headers=auth_headers)

    assert delete_response.status_code == 204, delete_response.text
    storage.delete.assert_called_once_with("test-user-1/abc123_simple.pdf")
    list_response = client.get("/api/v1/resumes/list", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total_count"] == 0


@patch("app.api.v1.endpoints.resumes_v2.get_storage")
def test_delete_resume_document_removes_dependent_rows(
    mock_get_storage, client: TestClient, auth_headers, db_session, test_user_id
):
    from app.models.jd_evaluation import JDEvaluation
    from app.models.resume_document import ResumeVersion
    from app.models.resume_evaluation_v2 import ResumeEvaluationV2
    from app.models.resume_export import ResumeExport

    storage = MagicMock()
    storage.upload.return_value = "test-user-1/abc123_simple.pdf"
    mock_get_storage.return_value = storage

    with FIXTURE.open("rb") as f:
        upload = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert upload.status_code == 201, upload.text
    doc_id = upload.json()["resume_document_id"]
    parsed_json = upload.json()
    parsed_json.pop("resume_document_id")

    jd_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())
    export_id = str(uuid.uuid4())
    evaluation_id = str(uuid.uuid4())
    db_session.add(
        ResumeEvaluationV2(
            id=evaluation_id,
            resume_document_id=doc_id,
            user_id=test_user_id,
            overall_score=92,
            bullet_flags=[],
            format_issues=[],
            summary_critique=None,
            ats_parseability=96,
            ats_raw_text="Resume text",
            model_version="test",
        )
    )
    db_session.add(
        JDEvaluation(
            id=jd_id,
            user_id=test_user_id,
            resume_document_id=doc_id,
            jd_text="Backend engineer role",
            extracted_requirements={
                "must_have": [],
                "good_to_have": [],
                "soft_skills": [],
                "seniority": "senior",
                "primary_role_category": "SWE",
                "country_hint": "US",
                "red_flags": [],
            },
            diff_plan={
                "match_score": 88,
                "must_have_coverage_found": [],
                "must_have_coverage_missing": [],
                "good_to_have_coverage_found": [],
                "good_to_have_coverage_missing": [],
                "bullets": [],
                "skills_reorder": None,
                "summary_rewrite": None,
                "suggested_additions": [],
            },
            match_score=88,
        )
    )
    db_session.add(
        ResumeVersion(
            id=version_id,
            resume_document_id=doc_id,
            change_set=[],
            parsed_json=parsed_json,
            jd_evaluation_id=jd_id,
            template_id="us-swe",
            company_name="Acme",
        )
    )
    db_session.add(
        ResumeExport(
            id=export_id,
            user_id=test_user_id,
            resume_document_id=doc_id,
            resume_version_id=version_id,
            country="US",
            role_template="swe",
            storage_path=None,
            status="succeeded",
            file_size_bytes=1234,
        )
    )
    db_session.commit()

    delete_response = client.delete(f"/api/v1/resumes/{doc_id}", headers=auth_headers)

    assert delete_response.status_code == 204, delete_response.text
    assert db_session.get(ResumeEvaluationV2, evaluation_id) is None
    assert db_session.get(ResumeExport, export_id) is None
    assert db_session.get(ResumeVersion, version_id) is None
    assert db_session.get(JDEvaluation, jd_id) is None


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
                    "readiness_label": "minor_edits",
                    "score_breakdown": {
                        "content_quality": 70,
                        "role_fit": 65,
                        "evidence_strength": 55,
                        "recruiter_readability": 68,
                    },
                    "score_explanation": [
                        {
                            "category": "evidence_strength",
                            "score": 55,
                            "reason": "Most bullets lack measurable outcomes.",
                            "evidence": ["Built API", "Improved performance 30%"],
                            "before_applying_action": "Add verified scope or outcome to weak bullets.",
                        }
                    ],
                    "top_actions_before_applying": ["Add verified scope or outcome to weak bullets."],
                    "parser_confidence": "high",
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
    assert data["readiness_label"] == "minor_edits"
    assert data["score_breakdown"]["evidence_strength"] == 55
    assert data["top_actions_before_applying"]
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


def test_evaluate_rejects_short_target_role(client: TestClient, auth_headers):
    """target_role shorter than 2 chars returns 422 before any credit debit."""
    resp = client.post(
        "/api/v1/resumes/some-doc-id/evaluate",
        json={"target_role": "X"},
        headers=auth_headers,
    )
    assert resp.status_code == 422, resp.text


def test_versions_rejects_foreign_parent_version(client: TestClient, auth_headers):
    """parent_version_id that belongs to a different resume document returns 404."""
    # Upload two separate resume documents
    with FIXTURE.open("rb") as f:
        up1 = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert up1.status_code == 201, up1.text
    doc_id_1 = up1.json()["resume_document_id"]

    with FIXTURE.open("rb") as f:
        up2 = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert up2.status_code == 201, up2.text
    doc_id_2 = up2.json()["resume_document_id"]

    # Create a version on doc_id_1
    v_resp = client.post(
        f"/api/v1/resumes/{doc_id_1}/versions",
        json={
            "parent_version_id": None,
            "change_set": [{"type": "summary_update", "new_summary": "Updated summary."}],
        },
        headers=auth_headers,
    )
    assert v_resp.status_code == 201, v_resp.text
    version_id_from_doc1 = v_resp.json()["version_id"]

    # Attempt to use version from doc_id_1 as parent for doc_id_2 — must return 404
    bad_resp = client.post(
        f"/api/v1/resumes/{doc_id_2}/versions",
        json={
            "parent_version_id": version_id_from_doc1,
            "change_set": [{"type": "summary_update", "new_summary": "Should be rejected."}],
        },
        headers=auth_headers,
    )
    assert bad_resp.status_code == 404, bad_resp.text


# ---------------------------------------------------------------------------
# Issue 6: apply_changes must update project bullets, not just experience
# ---------------------------------------------------------------------------


def test_apply_changes_updates_project_bullets():
    """apply_changes with a bullet_update for a project bullet must update that bullet."""
    from app.api.v1.endpoints.resumes_v2 import apply_changes
    from app.schemas.resume_v2 import (
        ResumeDocumentJSON, Contact, ExperienceEntry, Bullet,
        EducationEntry, Skills, ProjectEntry, ChangeItem,
    )

    project_bullet_id = "proj-b1"
    original_text = "Built an OSS library."
    new_text = "Built an OSS library with 500+ GitHub stars."

    doc = ResumeDocumentJSON(
        contact=Contact(name="Dev", email="dev@example.com"),
        experience=[],
        education=[EducationEntry(school="State U", degree="BS CS")],
        skills=Skills(hard=["Python"]),
        projects=[
            ProjectEntry(
                name="OSS Lib",
                bullets=[Bullet(id=project_bullet_id, text=original_text, raw_text=original_text)],
            )
        ],
        raw_text=original_text,
    )

    changes = [
        ChangeItem(type="bullet_update", bullet_id=project_bullet_id, new_text=new_text)
    ]

    result = apply_changes(doc, changes)

    project_bullets = result.projects[0].bullets
    assert any(b.text == new_text for b in project_bullets), (
        f"Expected project bullet text '{new_text}'; got {[b.text for b in project_bullets]}"
    )
