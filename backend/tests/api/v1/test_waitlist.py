import logging

from sqlalchemy.exc import OperationalError

from app.models.waitlist_entry import WaitlistEntry


def _payload(**overrides):
    return {
        "email": "Candidate@Example.com",
        "career_stage": "experienced_ic",
        "target_role": "Staff Engineer",
        "communication_challenge": "Explaining the impact of platform work",
        "consent": True,
        "company_website": "",
        **overrides,
    }


def test_valid_waitlist_submission_persists_without_creating_an_account(
    client, db_session
):
    response = client.post("/api/v1/waitlist", json=_payload())

    assert response.status_code == 202
    assert response.json() == {
        "message": "You're on the list. We'll be in touch when there is a useful next step."
    }
    assert "no-store" in response.headers["cache-control"]

    entry = db_session.query(WaitlistEntry).one()
    assert entry.normalized_email == "candidate@example.com"
    assert entry.consent_granted is True
    assert entry.consent_version
    assert entry.retention_expires_at > entry.consented_at


def test_duplicate_submission_is_idempotent_and_does_not_reveal_membership(
    client, db_session
):
    first = client.post("/api/v1/waitlist", json=_payload())
    duplicate = client.post(
        "/api/v1/waitlist",
        json=_payload(email="candidate@example.com", target_role="Different role"),
    )

    assert first.status_code == duplicate.status_code == 202
    assert first.json() == duplicate.json()
    assert db_session.query(WaitlistEntry).count() == 1


def test_honeypot_submission_returns_success_without_persistence(client, db_session):
    response = client.post(
        "/api/v1/waitlist",
        json=_payload(company_website="https://bot.example"),
    )

    assert response.status_code == 202
    assert db_session.query(WaitlistEntry).count() == 0


def test_missing_consent_and_invalid_email_are_rejected(client):
    no_consent = client.post(
        "/api/v1/waitlist", json=_payload(consent=False)
    )
    invalid_email = client.post(
        "/api/v1/waitlist", json=_payload(email="invalid")
    )

    assert no_consent.status_code == 422
    assert invalid_email.status_code == 422


def test_database_failure_does_not_log_submitted_email(
    client, db_session, monkeypatch, caplog
):
    private_email = "private-candidate@example.com"
    database_error = OperationalError(
        "INSERT INTO waitlist_entries (normalized_email) VALUES (:normalized_email)",
        {"normalized_email": private_email},
        Exception("database unavailable"),
    )

    def fail_commit():
        raise database_error

    monkeypatch.setattr(db_session, "commit", fail_commit)

    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/waitlist",
            json=_payload(email=private_email),
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "The waitlist is temporarily unavailable. Please try again later."
    }
    assert private_email not in caplog.text
