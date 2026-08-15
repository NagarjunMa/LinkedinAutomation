"""Tests for POST /api/v1/jd/{jd_evaluation_id}/apply (Task 6 & 7)."""
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Helpers to seed DB state
# ---------------------------------------------------------------------------

def _seed_resume_doc(db_session: Session, user_id: str, bullet_text: str = "Cut latency 38%."):
    """Create a ResumeDocument and return its id."""
    from app.models.resume_document import ResumeDocument
    from app.schemas.resume_v2 import (
        ResumeDocumentJSON, Contact, ExperienceEntry, Bullet, EducationEntry, Skills
    )

    doc_json = ResumeDocumentJSON(
        contact=Contact(name="Test User", email="t@t.com"),
        experience=[
            ExperienceEntry(
                company="Acme",
                role="SWE",
                dates="2022-2026",
                bullets=[Bullet(id="b1", text=bullet_text, raw_text=bullet_text)],
            )
        ],
        education=[EducationEntry(school="State U", degree="BS CS")],
        skills=Skills(hard=["Python"]),
        raw_text=bullet_text,
    )

    doc_id = str(uuid.uuid4())
    row = ResumeDocument(
        id=doc_id,
        user_id=user_id,
        original_filename="r.pdf",
        file_path="/tmp/r.pdf",
        file_type="pdf",
        parsed_json=doc_json.model_dump(),
        raw_text=doc_json.raw_text,
    )
    db_session.add(row)
    db_session.commit()
    return doc_id


def _seed_jd_evaluation(
    db_session: Session,
    user_id: str,
    doc_id: str,
    company_name: str = "Acme Corp",
    country_hint: str = "US",
    role_category: str = "SWE",
):
    """Create a JDEvaluation row and return its id."""
    from app.models.jd_evaluation import JDEvaluation

    jd_id = str(uuid.uuid4())
    extracted = {
        "must_have": [],
        "good_to_have": [],
        "soft_skills": [],
        "seniority": "mid",
        "primary_role_category": role_category,
        "country_hint": country_hint,
        "red_flags": [],
        "company_name": company_name,
        "job_title": "Senior Backend Engineer",
    }
    diff_plan = {
        "match_score": 80,
        "must_have_coverage_found": [],
        "must_have_coverage_missing": [],
        "good_to_have_coverage_found": [],
        "good_to_have_coverage_missing": [],
        "bullets": [],
        "skills_reorder": None,
        "summary_rewrite": None,
        "suggested_additions": [],
    }
    row = JDEvaluation(
        id=jd_id,
        user_id=user_id,
        resume_document_id=doc_id,
        jd_text="Senior Python role.",
        extracted_requirements=extracted,
        diff_plan=diff_plan,
        match_score=80,
    )
    db_session.add(row)
    db_session.commit()
    return jd_id


# ---------------------------------------------------------------------------
# Task 6: Happy path
# ---------------------------------------------------------------------------

def test_apply_happy_path_returns_apply_tailor_response(
    client: TestClient, auth_headers, db_session, test_user_id
):
    """POST /jd/{id}/apply persists a ResumeVersion and returns ApplyTailorResponse."""
    doc_id = _seed_resume_doc(db_session, test_user_id)
    jd_id = _seed_jd_evaluation(db_session, test_user_id, doc_id)

    resp = client.post(
        f"/api/v1/jd/{jd_id}/apply",
        json={
            "accepted_changes": [
                {
                    "type": "bullet_update",
                    "bullet_id": "b1",
                    "new_text": "Cut p99 latency by 50%.",
                }
            ],
            "template_id": None,
        },
        headers=auth_headers,
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Must return all required fields
    assert "version_id" in data
    assert isinstance(data["version_id"], str)
    assert len(data["version_id"]) > 0

    assert "preview_html" in data
    # preview_html may be empty on render failure; check it's a string
    assert isinstance(data["preview_html"], str)

    assert "suggested_template" in data
    # US SWE → us-swe (dash format)
    assert data["suggested_template"] in ("us-swe", "us-ds", "us-pm", "in-swe", "in-ds", "in-pm")

    assert "filename_hint" in data
    assert isinstance(data["filename_hint"], str)

    assert "company_name" in data
    assert data["company_name"] == "Acme Corp"

    # Verify the ResumeVersion was actually persisted
    from app.models.resume_document import ResumeVersion
    version = db_session.get(ResumeVersion, data["version_id"])
    assert version is not None
    assert version.jd_evaluation_id == jd_id
    assert version.accepted_at is not None
    assert version.resume_document_id == doc_id
    assert version.company_name == "Acme Corp"
    assert version.target_role_title == "Senior Backend Engineer"
    assert version.role_category == "SWE"
    assert version.seniority == "mid"
    assert version.country_hint == "US"
    assert version.match_score == 80
    assert version.source_jd_text == "Senior Python role."


def test_apply_returns_404_for_unknown_jd(
    client: TestClient, auth_headers, db_session, test_user_id
):
    """POST /jd/{id}/apply with unknown jd_evaluation_id returns 404."""
    resp = client.post(
        "/api/v1/jd/nonexistent-jd-id/apply",
        json={"accepted_changes": [], "template_id": None},
        headers=auth_headers,
    )
    assert resp.status_code == 404, resp.text


def test_apply_does_not_debit_credits(
    client: TestClient, auth_headers, db_session, test_user_id
):
    """POST /jd/{id}/apply costs 0 credits — no credit_transaction wrap."""
    from app.services.credits.ledger import get_balance, grant_monthly
    # Give user some credits, then apply — balance must not change
    grant_monthly(db_session, test_user_id, 5)
    db_session.commit()

    before = get_balance(db_session, test_user_id)

    doc_id = _seed_resume_doc(db_session, test_user_id)
    jd_id = _seed_jd_evaluation(db_session, test_user_id, doc_id)

    resp = client.post(
        f"/api/v1/jd/{jd_id}/apply",
        json={"accepted_changes": [], "template_id": None},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text

    after = get_balance(db_session, test_user_id)
    assert after == before, f"Credits changed: {before} → {after}"


def test_regenerate_bullet_options_returns_three_options(
    client: TestClient, auth_headers, db_session, test_user_id
):
    from unittest.mock import AsyncMock, patch
    from app.schemas.jd import BulletDiff, BulletOption

    doc_id = _seed_resume_doc(db_session, test_user_id)
    jd_id = _seed_jd_evaluation(db_session, test_user_id, doc_id)
    diff = BulletDiff(
        bullet_id="b1",
        old="Cut latency 38%.",
        new="Improved backend latency by 38%.",
        reason="Aligns with backend JD.",
        placeholders=[],
        options=[
            BulletOption(option_id="conservative", text="Cut latency 38%.", reason="Safe", placeholders=[]),
            BulletOption(option_id="impact", text="Improved backend latency by 38%.", reason="Impact", placeholders=[]),
            BulletOption(option_id="keyword", text="Optimized Python backend latency by 38%.", reason="Keyword", placeholders=[]),
        ],
    )

    with patch(
        "app.application.jd_service.generate_bullet_options",
        new=AsyncMock(return_value=diff),
    ):
        resp = client.post(
            f"/api/v1/jd/{jd_id}/bullets/b1/options",
            headers=auth_headers,
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["bullet_id"] == "b1"
    assert len(body["options"]) == 3
    assert body["options"][0]["option_id"] == "conservative"


# ---------------------------------------------------------------------------
# Task 7: Q6.A invariant — base resume always loaded from ResumeDocument
# ---------------------------------------------------------------------------

def test_apply_uses_base_resume_not_latest_version(
    client: TestClient, auth_headers, db_session, test_user_id
):
    """Applying JD2 must use original bullet text, NOT the text written by JD1's apply.

    Q6.A invariant: the endpoint loads ResumeDocument.parsed_json (the base
    document), never the latest ResumeVersion. So two separate JD applies on
    the same document are independent.
    """
    original_text = "Original bullet text."
    doc_id = _seed_resume_doc(db_session, test_user_id, bullet_text=original_text)

    # Seed JD1 and JD2 both pointing at the same resume document
    jd1_id = _seed_jd_evaluation(
        db_session, test_user_id, doc_id, company_name="Company One"
    )
    jd2_id = _seed_jd_evaluation(
        db_session, test_user_id, doc_id, company_name="Company Two"
    )

    # Apply JD1 — modifies bullet b1
    jd1_new_text = "Rewrote bullet for JD1."
    resp1 = client.post(
        f"/api/v1/jd/{jd1_id}/apply",
        json={
            "accepted_changes": [
                {"type": "bullet_update", "bullet_id": "b1", "new_text": jd1_new_text}
            ],
            "template_id": None,
        },
        headers=auth_headers,
    )
    assert resp1.status_code == 200, resp1.text
    v1_id = resp1.json()["version_id"]

    # Apply JD2 — sends no changes; result must contain ORIGINAL bullet, not JD1 text
    resp2 = client.post(
        f"/api/v1/jd/{jd2_id}/apply",
        json={"accepted_changes": [], "template_id": None},
        headers=auth_headers,
    )
    assert resp2.status_code == 200, resp2.text
    v2_id = resp2.json()["version_id"]

    # Inspect the two created versions
    from app.models.resume_document import ResumeVersion
    v1 = db_session.get(ResumeVersion, v1_id)
    v2 = db_session.get(ResumeVersion, v2_id)

    assert v1 is not None
    assert v2 is not None
    assert v1_id != v2_id

    # v1 must have JD1's rewrite
    v1_bullets = v1.parsed_json["experience"][0]["bullets"]
    assert any(b["text"] == jd1_new_text for b in v1_bullets), (
        f"Expected JD1 text in v1; got {v1_bullets}"
    )

    # v2 must have the ORIGINAL text (not JD1's text)
    v2_bullets = v2.parsed_json["experience"][0]["bullets"]
    assert any(b["text"] == original_text for b in v2_bullets), (
        f"Expected original text in v2; got {v2_bullets}"
    )
    assert not any(b["text"] == jd1_new_text for b in v2_bullets), (
        f"v2 must NOT contain JD1 text; got {v2_bullets}"
    )
