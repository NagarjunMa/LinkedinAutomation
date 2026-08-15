"""Transaction behavior for profile application orchestration."""

from unittest.mock import Mock

import pytest

from app.application.errors import ApplicationError
from app.application.profile_service import ProfileApplicationService
from app.models.job import UserProfile
from app.schemas.profile import UserProfileUpdate


def test_profile_write_failure_rolls_back_without_leaking_database_error(db_session):
    profile = UserProfile(
        user_id="profile-failure-user",
        full_name="Before",
        email="before@example.com",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.commit = Mock(side_effect=RuntimeError("database password leaked"))
    db_session.rollback = Mock()
    service = ProfileApplicationService(db_session)

    with pytest.raises(ApplicationError, match="Unable to update profile data") as error:
        service.update_profile(
            "profile-failure-user",
            UserProfileUpdate(full_name="After"),
        )

    assert "password" not in str(error.value)
    db_session.rollback.assert_called_once()
