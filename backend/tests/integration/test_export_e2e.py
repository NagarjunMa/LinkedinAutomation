# backend/tests/integration/test_export_e2e.py
from pathlib import Path

FIXTURE = Path(__file__).parent.parent / "fixtures/resumes/simple.pdf"


def test_export_e2e_after_upload_and_version(
    client, auth_headers, user_with_credits,
    mock_supabase_upload, mock_signed_url,
):
    # 1. Upload
    with FIXTURE.open("rb") as f:
        up = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("simple.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert up.status_code == 201, up.text
    doc_id = up.json()["resume_document_id"]

    # 2. Apply an empty version (smoke; full diff covered by Phase 1 e2e)
    v = client.post(
        f"/api/v1/resumes/{doc_id}/versions",
        json={"change_set": []},
        headers=auth_headers,
    )
    assert v.status_code == 201
    version_id = v.json()["version_id"]

    # 3. Export — real renderer so we exercise Playwright + templates end-to-end
    starting_bal = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    resp = client.post(
        "/api/v1/exports",
        json={
            "resume_document_id": doc_id,
            "resume_version_id": version_id,
            "country": "US",
            "role_template": "swe",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload["download_url"].startswith("https://")
    assert payload["country"] == "US"

    # 4. Credit debited
    after_bal = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    assert after_bal == starting_bal - 1

    # 5. GET returns a fresh signed URL without re-debiting
    re_get = client.get(f"/api/v1/exports/{payload['export_id']}", headers=auth_headers)
    assert re_get.status_code == 200
    after_get_bal = client.get("/api/v1/credits/balance", headers=auth_headers).json()["balance"]
    assert after_get_bal == after_bal
