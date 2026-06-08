"""Route security regression tests for freemium production hardening."""

from fastapi.testclient import TestClient


def test_legacy_user_routes_reject_unauthenticated_requests(client: TestClient):
    from app.core.auth import get_authenticated_user_id, get_current_user_id

    app = client.app
    current_user_override = app.dependency_overrides.pop(get_current_user_id, None)
    authenticated_user_override = app.dependency_overrides.pop(get_authenticated_user_id, None)
    try:
        responses = [
            client.get("/api/v1/user-profiles/user-a"),
            client.get("/api/v1/profiles/profile/user-a"),
            client.post(
                "/api/v1/jobs/extract-from-url",
                json={"url": "https://example.com/job", "user_id": "user-a"},
            ),
            client.get("/api/v1/jobs/"),
        ]
    finally:
        if current_user_override is not None:
            app.dependency_overrides[get_current_user_id] = current_user_override
        if authenticated_user_override is not None:
            app.dependency_overrides[get_authenticated_user_id] = authenticated_user_override

    assert {response.status_code for response in responses} == {401}


def test_legacy_path_user_id_mismatch_is_rejected(client: TestClient):
    response = client.get("/api/v1/user-profiles/someone-else")

    assert response.status_code == 403
    assert response.json()["detail"] == "User mismatch"


def test_legacy_body_user_id_mismatch_is_rejected(client: TestClient):
    response = client.post(
        "/api/v1/jobs/extract-from-url",
        json={"url": "https://example.com/job", "user_id": "someone-else"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User mismatch"


def test_cleanup_all_rejects_non_admin(client: TestClient, monkeypatch):
    monkeypatch.setenv("ADMIN_USER_IDS", "admin-user")

    response = client.post("/api/v1/jobs/cleanup/execute-all")

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin only"


def test_stripe_webhook_route_hidden_when_billing_disabled(client: TestClient):
    response = client.post("/api/v1/webhooks/stripe", content=b"{}")

    assert response.status_code == 404
