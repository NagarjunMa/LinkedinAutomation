"""Behavior and ownership regressions for the job tracking API."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.models.job import JobApplication, JobListing


def _shared_job(db_session):
    job = JobListing(title="Platform Engineer", company="Acme", source="test")
    db_session.add(job)
    db_session.flush()
    current = JobApplication(
        user_id="test-user-1",
        job_id=job.id,
        application_status="interested",
        application_source="test",
    )
    other = JobApplication(
        user_id="other-user",
        job_id=job.id,
        application_status="rejected",
        application_source="test",
    )
    db_session.add_all([current, other])
    db_session.commit()
    return job, current, other


def test_list_projects_application_status_per_user(client: TestClient, db_session):
    job, _, _ = _shared_job(db_session)

    response = client.get("/api/v1/jobs/")

    assert response.status_code == 200
    payload = response.json()[0]
    assert payload["id"] == job.id
    assert payload["applied"] is False
    assert payload["application_status"] == "interested"


def test_counts_use_current_users_application_status(client: TestClient, db_session):
    job, _, _ = _shared_job(db_session)

    before = client.get("/api/v1/jobs/counts")
    updated = client.put(f"/api/v1/jobs/{job.id}/status", json={"applied": True})
    after = client.get("/api/v1/jobs/counts")

    assert before.json()["applied_count"] == 0
    assert updated.status_code == 200
    assert after.json()["applied_count"] == 1
    assert after.json()["total_jobs"] == 1


def test_create_job_creates_owned_tracking_record(client: TestClient, db_session):
    response = client.post(
        "/api/v1/jobs/",
        json={"title": "Backend Engineer", "company": "Prism", "applied": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["applied"] is True
    assert payload["application_status"] == "applied"
    application = db_session.query(JobApplication).filter_by(job_id=payload["id"]).one()
    assert application.user_id == "test-user-1"


def test_job_filters_and_applied_projection(client: TestClient, db_session):
    first = client.post(
        "/api/v1/jobs/",
        json={
            "title": "Backend Engineer",
            "company": "Prism",
            "location": "Remote",
            "job_type": "full_time",
            "experience_level": "senior",
            "applied": True,
        },
    ).json()
    client.post(
        "/api/v1/jobs/",
        json={"title": "Product Manager", "company": "Elsewhere", "applied": False},
    )

    response = client.get(
        "/api/v1/jobs/",
        params={
            "title": "backend",
            "company": "pris",
            "location": "remote",
            "job_type": "full_time",
            "experience_level": "senior",
            "applied": "true",
            "sort_by": "oldest",
        },
    )

    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [first["id"]]


def test_stats_and_recent_use_owned_application_state(client: TestClient, db_session):
    now = datetime.now(timezone.utc)
    job = JobListing(
        title="Recent Engineer",
        company="Prism",
        source="test",
        extracted_date=now - timedelta(days=1),
    )
    db_session.add(job)
    db_session.flush()
    db_session.add(
        JobApplication(
            user_id="test-user-1",
            job_id=job.id,
            application_status="applied",
            application_source="manual",
            application_date=now,
        )
    )
    db_session.commit()

    stats = client.get("/api/v1/jobs/stats", params={"custom_days": 7})
    recent = client.get("/api/v1/jobs/recent-applications", params={"limit": 1})

    assert stats.status_code == 200
    assert stats.json()["total_applied"] == 1
    assert stats.json()["period_applied"] == 1
    assert stats.json()["daily_stats"][0]["jobs_applied"] == 1
    assert recent.status_code == 200
    assert recent.json()[0]["id"] == job.id
    assert recent.json()[0]["status"] == "Applied"


def test_unshared_job_can_be_updated_and_deleted(client: TestClient, db_session):
    created = client.post(
        "/api/v1/jobs/",
        json={"title": "Engineer", "company": "Original"},
    ).json()

    updated = client.put(
        f"/api/v1/jobs/{created['id']}",
        json={"company": "Updated", "applied": True},
    )
    deleted = client.delete(f"/api/v1/jobs/{created['id']}")

    assert updated.status_code == 200
    assert updated.json()["company"] == "Updated"
    assert updated.json()["applied"] is True
    assert deleted.status_code == 200
    assert db_session.get(JobListing, created["id"]) is None


def test_apply_contract_is_idempotent_and_rejects_user_mismatch(client: TestClient, db_session):
    job, current, _ = _shared_job(db_session)

    mismatch = client.post(
        f"/api/v1/jobs/applications/{job.id}/apply",
        data={"user_id": "other-user"},
    )
    first = client.post(
        f"/api/v1/jobs/applications/{job.id}/apply",
        data={"user_id": "test-user-1", "application_source": "direct", "notes": "Applied"},
    )
    second = client.post(
        f"/api/v1/jobs/applications/{job.id}/apply",
        data={"user_id": "test-user-1"},
    )

    assert mismatch.status_code == 403
    assert mismatch.json()["detail"] == "User mismatch"
    assert first.status_code == 200
    assert first.json()["status"] == "applied"
    assert second.status_code == 200
    assert second.json()["message"] == "Already applied to this job"
    db_session.expire_all()
    assert db_session.get(JobApplication, current.id).user_notes == "Applied"


def test_application_form_update_tracks_follow_up_and_response(client: TestClient, db_session):
    _, current, _ = _shared_job(db_session)

    response = client.put(
        f"/api/v1/jobs/applications/{current.id}/status",
        data={"status": "interview_scheduled", "notes": "Recruiter call", "follow_up_date": "2026-09-01"},
    )

    assert response.status_code == 200
    db_session.expire_all()
    updated = db_session.get(JobApplication, current.id)
    assert updated.application_status == "interview_scheduled"
    assert updated.follow_up_date.isoformat() == "2026-09-01"
    assert updated.company_response is True


def test_application_form_update_has_stable_invalid_date_error(client: TestClient, db_session):
    _, current, _ = _shared_job(db_session)
    original_status = current.application_status

    response = client.put(
        f"/api/v1/jobs/applications/{current.id}/status",
        data={"status": "applied", "follow_up_date": "09/01/2026"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "follow_up_date must use YYYY-MM-DD"
    assert db_session.get(JobApplication, current.id).application_status == original_status


def test_status_update_does_not_change_other_users_application(client: TestClient, db_session):
    job, current, other = _shared_job(db_session)

    response = client.put(f"/api/v1/jobs/{job.id}/status", json={"applied": True})

    assert response.status_code == 200
    assert response.json()["applied"] is True
    db_session.expire_all()
    assert db_session.get(JobApplication, current.id).application_status == "applied"
    assert db_session.get(JobApplication, other.id).application_status == "rejected"


def test_deleting_shared_job_only_removes_current_users_tracking(client: TestClient, db_session):
    job, current, other = _shared_job(db_session)
    job_id, current_id, other_id = job.id, current.id, other.id

    response = client.delete(f"/api/v1/jobs/{job.id}")

    assert response.status_code == 200
    db_session.expire_all()
    assert db_session.get(JobListing, job_id) is not None
    assert db_session.get(JobApplication, current_id) is None
    assert db_session.get(JobApplication, other_id) is not None


def test_shared_job_details_cannot_be_mutated(client: TestClient, db_session):
    job, _, _ = _shared_job(db_session)

    response = client.put(f"/api/v1/jobs/{job.id}", json={"company": "Changed"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Shared job details cannot be edited"
    db_session.expire_all()
    assert db_session.get(JobListing, job.id).company == "Acme"


def test_application_status_rejects_invalid_date(client: TestClient, db_session):
    job, _, _ = _shared_job(db_session)

    response = client.put(
        f"/api/v1/jobs/{job.id}/application-status",
        json={"status": "applied", "date": "not-a-date"},
    )

    assert response.status_code == 422


def test_application_status_rejects_unknown_state(client: TestClient, db_session):
    job, _, _ = _shared_job(db_session)

    response = client.put(
        f"/api/v1/jobs/{job.id}/application-status",
        json={"status": "made_up_state"},
    )

    assert response.status_code == 422


def test_application_context_is_stored_on_owned_tracking_record(client: TestClient, db_session):
    job, current, other = _shared_job(db_session)
    job.application_context = "legacy shared value"
    other.extraction_metadata = {"application_context": "other user's context"}
    db_session.commit()

    response = client.put(
        f"/api/v1/jobs/{job.id}/application-status",
        json={"status": "want_to_apply", "context": "Strong platform match"},
    )

    assert response.status_code == 200
    detail = client.get(f"/api/v1/jobs/{job.id}")
    assert detail.json()["application_context"] == "Strong platform match"
    db_session.expire_all()
    assert db_session.get(JobListing, job.id).application_context == "legacy shared value"
    assert db_session.get(JobApplication, current.id).extraction_metadata["application_context"] == "Strong platform match"
    assert db_session.get(JobApplication, other.id).extraction_metadata["application_context"] == "other user's context"


def test_application_list_path_uses_authenticated_owner(client: TestClient, db_session):
    job, current, _ = _shared_job(db_session)

    response = client.get("/api/v1/jobs/applications/test-user-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["applications"][0]["id"] == current.id
    assert payload["applications"][0]["job_listing"]["id"] == job.id
