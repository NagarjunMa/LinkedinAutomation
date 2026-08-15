"""HTTP adapters for authenticated profile and settings operations."""

from typing import Any

from fastapi import APIRouter, Depends, Path, Query

from app.api.dependencies import get_profile_application_service
from app.api.error_mapping import to_http_exception
from app.application.errors import ApplicationError
from app.application.profile_service import ProfileApplicationService
from app.schemas.profile import (
    EmailTrackingSettingsUpdate,
    NotificationSettingsUpdate,
    PrivacySettingsUpdate,
    ProfileChangeHistoryResponse,
    UserProfileCreate,
    UserProfileResponse,
    UserProfileUpdate,
    UserSettingsCreate,
    UserSettingsResponse,
    UserSettingsUpdate,
)


router = APIRouter()


@router.get("/{user_id}")
def get_profile(
    user_id: str = Path(min_length=1, max_length=100),
    service: ProfileApplicationService = Depends(get_profile_application_service),
) -> dict[str, Any]:
    return service.get_profile(user_id)


@router.post("/{user_id}", response_model=UserProfileResponse)
def create_profile(
    profile_data: UserProfileCreate,
    user_id: str = Path(min_length=1, max_length=100),
    service: ProfileApplicationService = Depends(get_profile_application_service),
):
    try:
        return service.create_profile(user_id, profile_data)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.put("/{user_id}", response_model=UserProfileResponse)
def update_profile(
    profile_data: UserProfileUpdate,
    user_id: str = Path(min_length=1, max_length=100),
    service: ProfileApplicationService = Depends(get_profile_application_service),
):
    try:
        return service.update_profile(user_id, profile_data)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.get("/{user_id}/settings", response_model=UserSettingsResponse)
def get_settings(
    user_id: str = Path(min_length=1, max_length=100),
    service: ProfileApplicationService = Depends(get_profile_application_service),
):
    try:
        return service.get_settings(user_id)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.post("/{user_id}/settings", response_model=UserSettingsResponse)
def create_settings(
    settings_data: UserSettingsCreate,
    user_id: str = Path(min_length=1, max_length=100),
    service: ProfileApplicationService = Depends(get_profile_application_service),
):
    try:
        return service.create_settings(user_id, settings_data)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.put("/{user_id}/settings", response_model=UserSettingsResponse)
def update_settings(
    settings_data: UserSettingsUpdate,
    user_id: str = Path(min_length=1, max_length=100),
    service: ProfileApplicationService = Depends(get_profile_application_service),
):
    try:
        return service.update_settings(user_id, settings_data)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.put("/{user_id}/settings/notifications", response_model=UserSettingsResponse)
def update_notification_settings(
    notification_data: NotificationSettingsUpdate,
    user_id: str = Path(min_length=1, max_length=100),
    service: ProfileApplicationService = Depends(get_profile_application_service),
):
    try:
        return service.update_notifications(user_id, notification_data)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.put("/{user_id}/settings/email-tracking", response_model=UserSettingsResponse)
def update_email_tracking_settings(
    tracking_data: EmailTrackingSettingsUpdate,
    user_id: str = Path(min_length=1, max_length=100),
    service: ProfileApplicationService = Depends(get_profile_application_service),
):
    try:
        return service.update_email_tracking(user_id, tracking_data)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.put("/{user_id}/settings/privacy", response_model=UserSettingsResponse)
def update_privacy_settings(
    privacy_data: PrivacySettingsUpdate,
    user_id: str = Path(min_length=1, max_length=100),
    service: ProfileApplicationService = Depends(get_profile_application_service),
):
    try:
        return service.update_privacy(user_id, privacy_data)
    except ApplicationError as exc:
        raise to_http_exception(exc) from exc


@router.get(
    "/{user_id}/change-history",
    response_model=list[ProfileChangeHistoryResponse],
)
def get_profile_change_history(
    user_id: str = Path(min_length=1, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    service: ProfileApplicationService = Depends(get_profile_application_service),
):
    return service.change_history(user_id, limit=limit)
