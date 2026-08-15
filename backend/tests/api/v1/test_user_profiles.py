"""Profile and settings API behavior behind authenticated ownership boundaries."""


def _profile_payload(**overrides):
    payload = {
        "full_name": "Test Candidate",
        "email": "candidate@example.com",
        "programming_languages": ["Python"],
        "desired_roles": ["Backend Engineer"],
        "preferred_locations": ["Remote"],
        "job_types": ["Full-time"],
    }
    payload.update(overrides)
    return payload


def test_profile_create_update_and_history(client, test_user_id):
    created = client.post(
        f"/api/v1/user-profiles/{test_user_id}",
        json=_profile_payload(),
    )

    assert created.status_code == 200, created.text
    assert created.json()["full_name"] == "Test Candidate"

    updated = client.put(
        f"/api/v1/user-profiles/{test_user_id}",
        json={
            "location": "New York, NY",
            "desired_roles": ["Platform Engineer"],
        },
    )

    assert updated.status_code == 200, updated.text
    assert updated.json()["location"] == "New York, NY"
    assert updated.json()["desired_roles"] == ["Platform Engineer"]

    history = client.get(
        f"/api/v1/user-profiles/{test_user_id}/change-history"
    )
    assert history.status_code == 200
    fields = {item["field_changed"] for item in history.json()}
    assert {"location", "desired_roles"}.issubset(fields)


def test_profile_update_missing_returns_stable_404(client, test_user_id):
    response = client.put(
        f"/api/v1/user-profiles/{test_user_id}",
        json={"location": "Remote"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found"


def test_settings_create_get_and_update_are_persistent(client, test_user_id):
    created = client.post(
        f"/api/v1/user-profiles/{test_user_id}/settings",
        json={
            "notification_frequency": "daily",
            "data_retention_days": 180,
            "analytics_enabled": "disabled",
        },
    )

    assert created.status_code == 200, created.text
    assert created.json()["notification_frequency"] == "daily"
    assert created.json()["data_retention_days"] == 180

    notifications = client.put(
        f"/api/v1/user-profiles/{test_user_id}/settings/notifications",
        json={"weekly_digest": False},
    )
    assert notifications.status_code == 200, notifications.text
    assert notifications.json()["email_notifications"]["weekly_digest"] is False
    assert notifications.json()["email_notifications"]["application_updates"] is True

    privacy = client.put(
        f"/api/v1/user-profiles/{test_user_id}/settings/privacy",
        json={"data_retention_days": 90, "analytics_enabled": "enabled"},
    )
    assert privacy.status_code == 200, privacy.text
    assert privacy.json()["data_retention_days"] == 90
    assert privacy.json()["analytics_enabled"] == "enabled"

    fetched = client.get(
        f"/api/v1/user-profiles/{test_user_id}/settings"
    )
    assert fetched.status_code == 200
    assert fetched.json()["data_retention_days"] == 90

    history = client.get(
        f"/api/v1/user-profiles/{test_user_id}/change-history"
    )
    fields = {item["field_changed"] for item in history.json()}
    assert "settings.email_notifications" in fields
    assert "settings.data_retention_days" in fields
    assert "settings.analytics_enabled" in fields


def test_settings_create_conflict_and_missing_update_are_stable(client, test_user_id):
    missing = client.put(
        f"/api/v1/user-profiles/{test_user_id}/settings/privacy",
        json={"data_retention_days": 90},
    )
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Settings not found"

    first = client.post(
        f"/api/v1/user-profiles/{test_user_id}/settings",
        json={},
    )
    assert first.status_code == 200

    duplicate = client.post(
        f"/api/v1/user-profiles/{test_user_id}/settings",
        json={},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Settings already exist"


def test_settings_routes_reject_another_user(client):
    response = client.get("/api/v1/user-profiles/another-user/settings")

    assert response.status_code == 403
    assert response.json()["detail"] == "User mismatch"
