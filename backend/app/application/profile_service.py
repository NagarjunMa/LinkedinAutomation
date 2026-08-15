"""Application orchestration for user-owned profile and settings data."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.errors import (
    ApplicationError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.application.profile_views import (
    empty_profile_response,
    profile_response,
)
from app.models import ProfileChangeHistory, UserSettings
from app.models.job import UserProfile
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import (
    EmailTrackingSettingsUpdate,
    NotificationSettingsUpdate,
    PrivacySettingsUpdate,
    UserProfileCreate,
    UserProfileUpdate,
    UserSettingsCreate,
    UserSettingsUpdate,
)


logger = logging.getLogger(__name__)

PROFILE_LIST_FIELDS = {
    "programming_languages",
    "frameworks_libraries",
    "tools_platforms",
    "desired_roles",
    "preferred_locations",
    "job_types",
    "degrees",
    "institutions",
    "graduation_years",
}


class ProfileApplicationService:
    def __init__(self, session: Session):
        self.session = session
        self.profiles = ProfileRepository(session)

    def get_profile(self, user_id: str) -> dict[str, Any]:
        profile = self.profiles.get_profile(user_id)
        latest_resume = self.profiles.latest_ready_resume(user_id)
        if not profile and not latest_resume:
            return empty_profile_response(user_id)
        return profile_response(
            user_id,
            profile,
            latest_resume,
            self.profiles.profile_stats(user_id),
        )

    def create_profile(
        self,
        user_id: str,
        request: UserProfileCreate,
    ) -> dict[str, Any]:
        profile = self.profiles.get_profile(user_id)
        if profile:
            self._apply_updates(profile, request, user_id=user_id)
        else:
            values = self._normalized_values(request)
            profile = UserProfile(user_id=user_id, **values)
            self.profiles.add(profile)
        self._commit("create profile")
        self.session.refresh(profile)
        latest_resume = self.profiles.latest_ready_resume(user_id)
        return profile_response(
            user_id,
            profile,
            latest_resume,
            self.profiles.profile_stats(user_id),
        )

    def update_profile(
        self,
        user_id: str,
        request: UserProfileUpdate,
    ) -> dict[str, Any]:
        profile = self.profiles.get_profile(user_id)
        if not profile:
            raise ResourceNotFoundError("Profile not found")
        self._apply_updates(profile, request, user_id=user_id)
        self._commit("update profile")
        self.session.refresh(profile)
        latest_resume = self.profiles.latest_ready_resume(user_id)
        return profile_response(
            user_id,
            profile,
            latest_resume,
            self.profiles.profile_stats(user_id),
        )

    def get_settings(self, user_id: str) -> UserSettings:
        settings = self.profiles.get_settings(user_id)
        if not settings:
            raise ResourceNotFoundError("Settings not found")
        return settings

    def create_settings(
        self,
        user_id: str,
        request: UserSettingsCreate,
    ) -> UserSettings:
        if self.profiles.get_settings(user_id):
            raise ResourceConflictError("Settings already exist")
        settings = UserSettings(
            user_id=user_id,
            **request.model_dump(exclude_none=True),
        )
        self.profiles.add(settings)
        self._commit("create settings")
        self.session.refresh(settings)
        return settings

    def update_settings(
        self,
        user_id: str,
        request: UserSettingsUpdate,
    ) -> UserSettings:
        return self._update_settings(user_id, request, operation="update settings")

    def update_notifications(
        self,
        user_id: str,
        request: NotificationSettingsUpdate,
    ) -> UserSettings:
        settings = self.get_settings(user_id)
        old_value = dict(settings.email_notifications or {})
        new_value = dict(old_value)
        new_value.update(request.model_dump(exclude_none=True))
        if new_value != old_value:
            settings.email_notifications = new_value
            self._record_change(
                user_id,
                "settings.email_notifications",
                old_value,
                new_value,
            )
        settings.updated_at = datetime.now(timezone.utc)
        self._commit("update notification settings")
        self.session.refresh(settings)
        return settings

    def update_email_tracking(
        self,
        user_id: str,
        request: EmailTrackingSettingsUpdate,
    ) -> UserSettings:
        return self._update_settings(
            user_id,
            request,
            operation="update email tracking settings",
        )

    def update_privacy(
        self,
        user_id: str,
        request: PrivacySettingsUpdate,
    ) -> UserSettings:
        return self._update_settings(
            user_id,
            request,
            operation="update privacy settings",
        )

    def change_history(
        self,
        user_id: str,
        *,
        limit: int,
    ) -> list[ProfileChangeHistory]:
        return self.profiles.change_history(user_id, limit=limit)

    def _update_settings(
        self,
        user_id: str,
        request: BaseModel,
        *,
        operation: str,
    ) -> UserSettings:
        settings = self.get_settings(user_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            if value is None:
                continue
            old_value = getattr(settings, field)
            if old_value == value:
                continue
            setattr(settings, field, value)
            self._record_change(user_id, f"settings.{field}", old_value, value)
        settings.updated_at = datetime.now(timezone.utc)
        self._commit(operation)
        self.session.refresh(settings)
        return settings

    def _apply_updates(
        self,
        profile: UserProfile,
        request: BaseModel,
        *,
        user_id: str,
    ) -> None:
        for field, value in self._normalized_values(request, exclude_unset=True).items():
            old_value = getattr(profile, field)
            if old_value == value:
                continue
            setattr(profile, field, value)
            self._record_change(user_id, field, old_value, value)
        profile.updated_at = datetime.now(timezone.utc)

    def _record_change(
        self,
        user_id: str,
        field: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        self.profiles.add(
            ProfileChangeHistory(
                user_id=user_id,
                field_changed=field,
                old_value=_serialized_value(old_value),
                new_value=_serialized_value(new_value),
            )
        )

    def _commit(self, operation: str) -> None:
        try:
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            logger.error(
                "Profile operation failed: %s",
                type(exc).__name__,
                extra={"operation": operation},
            )
            raise ApplicationError("Unable to update profile data") from exc

    @staticmethod
    def _normalized_values(
        request: BaseModel,
        *,
        exclude_unset: bool = False,
    ) -> dict[str, Any]:
        values = request.model_dump(exclude_unset=exclude_unset)
        for field in PROFILE_LIST_FIELDS:
            if field in values and values[field] is None:
                values[field] = []
        return values


def _serialized_value(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, default=str, sort_keys=True)
