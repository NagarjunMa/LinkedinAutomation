"""Exercise preferences writes through fake persistence, with no database connection."""

from datetime import datetime, timezone
from unittest.mock import Mock, call, patch

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from app.api.dependencies import get_profile_application_service
from app.api.v1.api import api_router
from app.application.errors import ResourceConflictError
from app.application.profile_service import ProfileApplicationService
from app.core.auth import get_current_user_id
from app.models.job import UserProfile
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import (
    JobPreferencesUpdate,
    UserProfileResponse,
    UserProfileUpdate,
    UserSettingsCreate,
)


def service_for(profile):
    service = ProfileApplicationService(Mock(spec=Session))
    service.profiles = Mock()
    service.profiles.get_profile.return_value = profile
    return service


def test_first_save_creates_preferences_without_copying_contact_details():
    service = service_for(None)

    result = service.save_preferences(
        "owner-1", JobPreferencesUpdate(desired_roles=["QA Engineer"])
    )

    service.profiles.get_profile.assert_called_once_with("owner-1", lock=True)
    row = service.profiles.add.call_args.args[0]
    assert row.user_id == "owner-1"
    assert row.full_name is None and row.email is None
    assert row.salary_range_min is None
    assert result.desired_roles == ["QA Engineer"]
    service.session.commit.assert_called_once()
    service.session.refresh.assert_called_once_with(row)


def test_owner_profile_query_locks_only_for_writes():
    session = Mock(spec=Session)
    session.query.return_value = Query([UserProfile])
    repository = ProfileRepository(session)

    with patch.object(Query, "first", autospec=True) as first:
        repository.get_profile("owner-1")
        repository.get_profile("owner-1", lock=True)

    read, write = (
        query_call.args[0].statement.compile(dialect=postgresql.dialect())
        for query_call in first.call_args_list
    )
    assert "FOR UPDATE" not in str(read)
    assert "FOR UPDATE" in str(write)
    assert tuple(write.params.values()) == ("owner-1",)


def test_existing_profile_save_preserves_omitted_fields():
    profile = UserProfile(
        user_id="owner-1",
        email="owner@example.com",
        desired_roles=["Before"],
        salary_range_min=83500,
        salary_range_max=127500,
    )
    service = service_for(profile)

    result = service.save_preferences(
        "owner-1", JobPreferencesUpdate(desired_roles=[])
    )

    assert result.desired_roles == []
    assert result.salary_range_min == 83500
    assert result.salary_range_max == 127500
    assert profile.email == "owner@example.com"
    change = service.profiles.add.call_args.args[0]
    assert change.user_id == "owner-1" and change.field_changed == "desired_roles"


def test_account_routes_require_owner_before_calling_persistence():
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    service = Mock(spec=ProfileApplicationService)
    app.dependency_overrides[get_profile_application_service] = lambda: service
    base = "/api/v1/user-profiles/owner-2"
    requests = [
        ("GET", base, None),
        ("GET", f"{base}/settings", None),
        ("PUT", f"{base}/preferences", {"desired_roles": ["QA Engineer"]}),
        ("PUT", f"{base}/settings/privacy", {"analytics_enabled": "disabled"}),
        ("POST", f"{base}/settings", {"analytics_enabled": "disabled"}),
    ]
    with TestClient(app) as client:
        for method, path, body in requests:
            assert client.request(method, path, json=body).status_code == 401

        app.dependency_overrides[get_current_user_id] = lambda: "owner-1"
        for method, path, body in requests:
            assert client.request(method, path, json=body).status_code == 403

        assert service.mock_calls == []

        app.dependency_overrides[get_current_user_id] = lambda: "owner-2"
        service.save_preferences.return_value = JobPreferencesUpdate(desired_roles=["QA Engineer"])
        response = client.put(f"{base}/preferences", json={"desired_roles": ["QA Engineer"]})
        assert response.status_code == 200
        assert response.json()["desired_roles"] == ["QA Engineer"]
        service.save_preferences.assert_called_once_with(
            "owner-2", JobPreferencesUpdate(desired_roles=["QA Engineer"])
        )


def duplicate_insert_error():
    return IntegrityError("insert", {}, RuntimeError("duplicate owner"))


def test_salary_validation_rejects_bad_ranges_before_persistence():
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    service = Mock(spec=ProfileApplicationService)
    service.save_preferences.return_value = JobPreferencesUpdate()
    app.dependency_overrides[get_profile_application_service] = lambda: service
    app.dependency_overrides[get_current_user_id] = lambda: "owner-1"
    bad_ranges = (
        {"salary_range_min": 120_000, "salary_range_max": 80_000},
        {"salary_range_min": -1, "salary_range_max": 80_000},
        {"salary_range_min": 100_000, "salary_range_max": 2_147_483_648},
        {"salary_range_min": 80_000},
        {"salary_range_min": None, "salary_range_max": 80_000},
    )
    with TestClient(app) as client:
        for payload in bad_ranges:
            response = client.put("/api/v1/user-profiles/owner-1/preferences", json=payload)
            assert response.status_code == 422, payload

    assert service.mock_calls == []


def test_role_update_can_round_trip_an_untouched_legacy_salary_range():
    profile = UserProfile(user_id="owner-1", salary_range_min=120_000, salary_range_max=80_000)
    service = service_for(profile)

    result = service.save_preferences("owner-1", JobPreferencesUpdate(desired_roles=["QA Engineer"]))

    assert result.desired_roles == ["QA Engineer"]
    assert (result.salary_range_min, result.salary_range_max) == (120_000, 80_000)


@pytest.mark.parametrize("minimum, maximum", [(0, 2_147_483_647), (None, None)])
def test_salary_preferences_save_and_clear_both_amounts(minimum, maximum):
    profile = UserProfile(user_id="owner-1", salary_range_min=80_000, salary_range_max=120_000)
    service = service_for(profile)

    result = service.save_preferences(
        "owner-1", JobPreferencesUpdate(salary_range_min=minimum, salary_range_max=maximum)
    )

    assert (result.salary_range_min, result.salary_range_max) == (minimum, maximum)
    service.profiles.get_profile.assert_called_once_with("owner-1", lock=True)
    service.session.commit.assert_called_once()


def test_concurrent_first_preference_save_reuses_winning_row():
    profile = UserProfile(user_id="owner-1", preferred_locations=["Remote"])
    service = service_for(None)
    service.profiles.get_profile.side_effect = [None, profile]
    service.session.commit.side_effect = [duplicate_insert_error(), None]

    result = service.save_preferences(
        "owner-1", JobPreferencesUpdate(desired_roles=["QA Engineer"])
    )

    assert result.desired_roles == ["QA Engineer"]
    assert result.preferred_locations == ["Remote"]
    assert service.profiles.get_profile.call_args_list == [call("owner-1", lock=True)] * 2
    assert service.session.commit.call_count == 2
    service.session.rollback.assert_called_once()


def test_concurrent_settings_creation_reports_existing_owner_conflict():
    service = service_for(None)
    service.profiles.get_settings.side_effect = [None, object()]
    service.session.commit.side_effect = duplicate_insert_error()

    with pytest.raises(ResourceConflictError, match="^Settings already exist$"):
        service.create_settings("owner-1", UserSettingsCreate(analytics_enabled="disabled"))

    service.session.rollback.assert_called_once()


def test_regular_profile_update_still_serializes_a_preferences_only_row():
    now = datetime.now(timezone.utc)
    profile = UserProfile(
        user_id="owner-1", desired_roles=["QA Engineer"], created_at=now, updated_at=now
    )
    service = service_for(profile)
    service.profiles.latest_ready_resume.return_value = None
    service.profiles.profile_stats.return_value = {}

    updated = UserProfileResponse.model_validate(
        service.update_profile("owner-1", UserProfileUpdate(location="Remote"))
    )

    assert updated.location == "Remote"
    assert updated.desired_roles == ["QA Engineer"]
    assert updated.full_name == updated.email == ""
    service.profiles.get_profile.assert_called_once_with("owner-1", lock=True)
