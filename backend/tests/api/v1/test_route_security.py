"""Route security regression tests for freemium production hardening."""

from fastapi.testclient import TestClient


def _seed_job_application(db_session, user_id: str, title: str = "Engineer"):
    from app.models.job import JobApplication, JobListing

    job = JobListing(title=title, company="Acme", location="Remote", source="test")
    db_session.add(job)
    db_session.flush()
    application = JobApplication(
        user_id=user_id,
        job_id=job.id,
        application_status="interested",
        application_source="test",
    )
    db_session.add(application)
    db_session.commit()
    return job, application


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


def test_jobs_list_only_returns_authenticated_users_jobs(client: TestClient, db_session):
    own_job, _ = _seed_job_application(db_session, "test-user-1", title="Own job")
    _seed_job_application(db_session, "other-user", title="Other job")

    response = client.get("/api/v1/jobs/")

    assert response.status_code == 200
    payload = response.json()
    assert [job["id"] for job in payload] == [own_job.id]
    assert payload[0]["title"] == "Own job"


def test_jobs_detail_rejects_other_users_job(client: TestClient, db_session):
    other_job, _ = _seed_job_application(db_session, "other-user", title="Other job")

    response = client.get(f"/api/v1/jobs/{other_job.id}")

    assert response.status_code == 404


def test_jobs_applications_path_user_mismatch_is_rejected(client: TestClient):
    response = client.get("/api/v1/jobs/applications/other-user")

    assert response.status_code == 403
    assert response.json()["detail"] == "User mismatch"


def test_update_application_status_rejects_other_users_application(client: TestClient, db_session):
    _, application = _seed_job_application(db_session, "other-user", title="Other job")

    response = client.put(
        f"/api/v1/jobs/applications/{application.id}/status",
        data={"status": "applied"},
    )

    assert response.status_code == 404


def test_oversized_request_rejected_before_endpoint_processing(client: TestClient):
    response = client.post(
        "/api/v1/resumes/upload",
        content=b"",
        headers={"Content-Length": str(51 * 1024 * 1024)},
    )

    assert response.status_code == 413
