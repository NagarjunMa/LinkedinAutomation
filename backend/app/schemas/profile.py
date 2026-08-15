from datetime import datetime, date
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class WorkExperience(BaseModel):
    job_title: str
    company: str
    location: str
    start_date: date
    end_date: Optional[date] = None  # None means current job

    model_config = ConfigDict(from_attributes=True)


class Education(BaseModel):
    university: str
    degree: str
    field_of_study: str
    location: str
    start_date: date
    end_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileBase(BaseModel):
    # Personal Information
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None

    # Professional Information
    years_of_experience: Optional[float] = None
    career_level: Optional[str] = None
    professional_summary: Optional[str] = None

    # Skills & Technologies
    programming_languages: Optional[List[str]] = None
    frameworks_libraries: Optional[List[str]] = None
    tools_platforms: Optional[List[str]] = None

    # Job Preferences
    desired_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    salary_range_min: Optional[int] = None
    salary_range_max: Optional[int] = None
    job_types: Optional[List[str]] = None

    # Education
    degrees: Optional[List[str]] = None
    institutions: Optional[List[str]] = None
    graduation_years: Optional[List[str]] = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    # Personal Information
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None

    # Professional Information
    years_of_experience: Optional[float] = None
    career_level: Optional[str] = None
    professional_summary: Optional[str] = None

    # Skills & Technologies
    programming_languages: Optional[List[str]] = None
    frameworks_libraries: Optional[List[str]] = None
    tools_platforms: Optional[List[str]] = None

    # Job Preferences
    desired_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    salary_range_min: Optional[int] = None
    salary_range_max: Optional[int] = None
    job_types: Optional[List[str]] = None

    # Education
    degrees: Optional[List[str]] = None
    institutions: Optional[List[str]] = None
    graduation_years: Optional[List[str]] = None


class UserProfileResponse(UserProfileBase):
    user_id: str
    created_at: datetime
    updated_at: datetime

    # Profile statistics
    total_applications: int = 0
    total_resumes: int = 0
    profile_completion: int = 0

    model_config = ConfigDict(from_attributes=True)


class UserSettingsBase(BaseModel):
    email_notifications: Optional[Dict[str, bool]] = Field(
        default_factory=lambda: {
            "application_updates": True,
            "interview_reminders": True,
            "weekly_digest": True,
            "referral_responses": True,
        }
    )
    notification_frequency: Optional[str] = "realtime"
    email_forwarding_enabled: Optional[str] = "inactive"
    forwarding_address: Optional[str] = None
    data_retention_days: Optional[int] = 365
    analytics_enabled: Optional[str] = "enabled"


class UserSettingsCreate(UserSettingsBase):
    pass


class UserSettingsUpdate(BaseModel):
    email_notifications: Optional[Dict[str, bool]] = None
    notification_frequency: Optional[str] = None
    email_forwarding_enabled: Optional[str] = None
    forwarding_address: Optional[str] = None
    data_retention_days: Optional[int] = None
    analytics_enabled: Optional[str] = None


class UserSettingsResponse(UserSettingsBase):
    user_id: str
    last_email_check: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileChangeHistoryResponse(BaseModel):
    id: str
    user_id: str
    field_changed: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationSettingsUpdate(BaseModel):
    application_updates: Optional[bool] = None
    interview_reminders: Optional[bool] = None
    weekly_digest: Optional[bool] = None
    referral_responses: Optional[bool] = None


class EmailTrackingSettingsUpdate(BaseModel):
    email_forwarding_enabled: Optional[str] = None
    forwarding_address: Optional[str] = None
    notification_frequency: Optional[str] = None


class PrivacySettingsUpdate(BaseModel):
    data_retention_days: Optional[int] = None
    analytics_enabled: Optional[str] = None
