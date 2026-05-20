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
