from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from app.db.session import get_db
from app.services.profile_service import ProfileService
from app.schemas.profile import (
    UserProfileResponse, UserProfileCreate, UserProfileUpdate,
    UserSettingsResponse, UserSettingsCreate, UserSettingsUpdate,
    ProfileChangeHistoryResponse,
    NotificationSettingsUpdate, EmailTrackingSettingsUpdate, PrivacySettingsUpdate
)

router = APIRouter()

_EMPTY_PROFILE_DEFAULTS: Dict[str, Any] = {
    "full_name": "",
    "email": "",
    "phone": None,
    "location": None,
    "years_of_experience": None,
    "career_level": None,
    "professional_summary": None,
    "programming_languages": [],
    "frameworks_libraries": [],
    "tools_platforms": [],
    "desired_roles": [],
    "preferred_locations": [],
    "salary_range_min": None,
    "salary_range_max": None,
    "job_types": [],
    "degrees": [],
    "institutions": [],
    "graduation_years": [],
    "total_applications": 0,
    "total_resumes": 0,
    "profile_completion": 0,
    "exists": False,
}


@router.get("/{user_id}")
def get_profile(
    user_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user profile with statistics.

    Returns an empty profile with ``exists=False`` for new users who have not
    yet configured their profile, instead of raising 404.
    """
    profile_data = ProfileService.get_profile_with_stats(db, user_id)
    if not profile_data:
        return {"user_id": user_id, **_EMPTY_PROFILE_DEFAULTS}
    profile_data["exists"] = True
    return profile_data


@router.post("/{user_id}", response_model=UserProfileResponse)
def create_profile(
    user_id: str,
    profile_data: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new user profile"""
    try:
        ProfileService.create_profile(db, user_id, profile_data)
        # Return with stats
        return ProfileService.get_profile_with_stats(db, user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create profile: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserProfileResponse)
def update_profile(
    user_id: str,
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update user profile"""
    profile = ProfileService.update_profile(db, user_id, profile_data)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Return updated profile with stats
    return ProfileService.get_profile_with_stats(db, user_id)


@router.get("/{user_id}/settings", response_model=UserSettingsResponse)
def get_settings(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user settings"""
    settings = ProfileService.get_settings(db, user_id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found"
        )
    return settings


@router.post("/{user_id}/settings", response_model=UserSettingsResponse)
def create_settings(
    user_id: str,
    settings_data: UserSettingsCreate,
    db: Session = Depends(get_db)
):
    """Create user settings"""
    try:
        settings = ProfileService.create_settings(db, user_id, settings_data)
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create settings: {str(e)}"
        )


@router.put("/{user_id}/settings", response_model=UserSettingsResponse)
def update_settings(
    user_id: str,
    settings_data: UserSettingsUpdate,
    db: Session = Depends(get_db)
):
    """Update user settings"""
    settings = ProfileService.update_settings(db, user_id, settings_data)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found"
        )
    return settings


@router.put("/{user_id}/settings/notifications", response_model=UserSettingsResponse)
def update_notification_settings(
    user_id: str,
    notification_data: NotificationSettingsUpdate,
    db: Session = Depends(get_db)
):
    """Update notification preferences"""
    settings = ProfileService.update_notification_settings(db, user_id, notification_data)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found"
        )
    return settings


@router.put("/{user_id}/settings/email-tracking", response_model=UserSettingsResponse)
def update_email_tracking_settings(
    user_id: str,
    tracking_data: EmailTrackingSettingsUpdate,
    db: Session = Depends(get_db)
):
    """Update email tracking settings"""
    settings = ProfileService.update_email_tracking_settings(db, user_id, tracking_data)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found"
        )
    return settings


@router.put("/{user_id}/settings/privacy", response_model=UserSettingsResponse)
def update_privacy_settings(
    user_id: str,
    privacy_data: PrivacySettingsUpdate,
    db: Session = Depends(get_db)
):
    """Update privacy settings"""
    settings = ProfileService.update_privacy_settings(db, user_id, privacy_data)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found"
        )
    return settings


@router.get("/{user_id}/change-history", response_model=List[ProfileChangeHistoryResponse])
def get_profile_change_history(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get profile change history for audit purposes"""
    changes = ProfileService.get_profile_change_history(db, user_id, limit)
    return changes
