import uuid
import pytest


def test_export_404_on_unknown_resume(client, auth_headers, user_with_credits):
    resp = client.post(
        "/api/v1/exports",
        json={"resume_document_id": str(uuid.uuid4()), "country": "US", "role_template": "swe"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_export_happy_path_debits_one_credit(
    client, auth_headers, user_with_credits, uploaded_resume_doc,
    mock_pdf_render, mock_supabase_upload, mock_signed_url,
):
    starting = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_document_id": uploaded_resume_doc.id,
            "country": "US",
            "role_template": "swe",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["download_url"].startswith("https://")
    assert body["country"] == "US"
    assert body["role_template"] == "swe"
    after = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    assert after == starting - 1


def test_export_refunds_credit_on_render_timeout(
    client, auth_headers, user_with_credits, uploaded_resume_doc,
    mock_pdf_render_timeout,
):
    starting = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_document_id": uploaded_resume_doc.id,
            "country": "US",
            "role_template": "swe",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 500
    after = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    assert after == starting, "credit must be refunded on hard render failure"


def test_get_export_returns_fresh_signed_url(
    client, auth_headers, user_with_credits, uploaded_resume_doc,
    mock_pdf_render, mock_supabase_upload, mock_signed_url,
):
    created = client.post(
        "/api/v1/exports",
        json={"resume_document_id": uploaded_resume_doc.id, "country": "US", "role_template": "swe"},
        headers=auth_headers,
    )
    export_id = created.json()["export_id"]
    resp = client.get(f"/api/v1/exports/{export_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["export_id"] == export_id
    assert resp.json()["download_url"].startswith("https://")


def test_get_export_404_for_missing_id(client, auth_headers, user_with_credits):
    resp = client.get("/api/v1/exports/does-not-exist", headers=auth_headers)
    assert resp.status_code == 404


def test_export_with_custom_filename(
    client, auth_headers, user_with_credits, uploaded_resume_doc,
    mock_pdf_render, mock_supabase_upload, mock_signed_url,
):
    """Client-supplied filename is echoed back in the response."""
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_document_id": uploaded_resume_doc.id,
            "country": "US",
            "role_template": "swe",
            "filename": "my-resume.pdf",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["filename"] == "my-resume.pdf"
    assert body["download_url"].startswith("https://")


def test_export_sanitizes_filename(
    client, auth_headers, user_with_credits, uploaded_resume_doc,
    mock_pdf_render, mock_supabase_upload, mock_signed_url,
):
    """Path-traversal and control chars are stripped; .pdf suffix is enforced."""
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_document_id": uploaded_resume_doc.id,
            "country": "US",
            "role_template": "swe",
            "filename": "../../etc/passwd\x00evil",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # Should NOT contain path separators, null bytes, or bare "passwd"
    fn = body["filename"]
    assert "/" not in fn
    assert "\\" not in fn
    assert "\x00" not in fn
    assert fn.endswith(".pdf")
