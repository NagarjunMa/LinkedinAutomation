"""Tests for the apply-flow export shape (resume_version_id + template_id)."""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def resume_version(db_session: Session, test_user_id: str):
    """Persist a ResumeDocument + ResumeVersion and return the version row."""
    from app.models.resume_document import ResumeDocument, ResumeVersion
    from tests.fixtures.resume_doc_json import make_resume

    doc_json = make_resume()
    doc_id = str(uuid.uuid4())
    doc = ResumeDocument(
        id=doc_id,
        user_id=test_user_id,
        original_filename="r.pdf",
        file_path="/tmp/r.pdf",
        file_type="pdf",
        parsed_json=doc_json.model_dump(),
        raw_text=doc_json.raw_text,
    )
    db_session.add(doc)
    db_session.commit()

    version_id = str(uuid.uuid4())
    version = ResumeVersion(
        id=version_id,
        resume_document_id=doc_id,
        parent_version_id=None,
        change_set=[],
        parsed_json=doc_json.model_dump(),
        template_id="us-swe",
    )
    db_session.add(version)
    db_session.commit()
    return version


# ---------------------------------------------------------------------------
# Issue 1 new tests: apply-flow shape
# ---------------------------------------------------------------------------


def test_export_via_version_id(
    client: TestClient,
    auth_headers,
    user_with_credits,
    resume_version,
    mock_pdf_render,
    mock_supabase_upload,
    mock_signed_url,
):
    """POST /exports with resume_version_id + template_id 'us-swe' returns 201."""
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_version_id": resume_version.id,
            "template_id": "us-swe",
            "filename": "tailored-resume.pdf",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "export_id" in body
    assert body["download_url"].startswith("https://")
    assert body["country"] == "US"
    assert body["role_template"] == "swe"
    assert body["filename"] == "tailored-resume.pdf"


def test_export_rejects_invalid_template_id(
    client: TestClient,
    auth_headers,
    user_with_credits,
    resume_version,
):
    """POST /exports with an invalid template_id returns 422."""
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_version_id": resume_version.id,
            "template_id": "xx-yy",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422, resp.text


def test_export_via_version_id_slash_format_also_accepted(
    client: TestClient,
    auth_headers,
    user_with_credits,
    resume_version,
    mock_pdf_render,
    mock_supabase_upload,
    mock_signed_url,
):
    """POST /exports with slash-format template_id 'us/swe' is also accepted."""
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_version_id": resume_version.id,
            "template_id": "us/swe",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["country"] == "US"
    assert body["role_template"] == "swe"


def test_export_via_version_id_uses_version_template_id_as_fallback(
    client: TestClient,
    auth_headers,
    user_with_credits,
    resume_version,
    mock_pdf_render,
    mock_supabase_upload,
    mock_signed_url,
):
    """When template_id is omitted, the version's stored template_id is used."""
    # resume_version fixture has template_id="us-swe"
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_version_id": resume_version.id,
            # no template_id provided
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["country"] == "US"
    assert body["role_template"] == "swe"


def test_export_missing_both_shapes_returns_422(
    client: TestClient,
    auth_headers,
    user_with_credits,
):
    """POST /exports with neither resume_version_id nor resume_document_id+country+role returns 422."""
    resp = client.post(
        "/api/v1/exports",
        json={"filename": "resume.pdf"},
        headers=auth_headers,
    )
    assert resp.status_code == 422, resp.text
