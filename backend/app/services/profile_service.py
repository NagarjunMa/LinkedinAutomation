from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.job import UserProfile
from app.models import Resume, JobApplication
from app.schemas.profile import (
    UserProfileCreate, UserProfileUpdate
)


class ProfileService:
    @staticmethod
    def get_profile_with_stats(db: Session, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile with statistics"""
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return None

        # Calculate statistics
        total_applications = db.query(JobApplication).filter(JobApplication.user_id == user_id).count()
        total_resumes = db.query(Resume).filter(Resume.user_id == user_id).count()

        # Calculate profile completion percentage
        completion_fields = [
            profile.full_name, profile.email, profile.programming_languages,
            profile.preferred_locations, profile.salary_range_min, profile.career_level,
            profile.degrees, profile.institutions, profile.professional_summary,
            profile.desired_roles, profile.job_titles, profile.companies
        ]
        completed_fields = sum(1 for field in completion_fields if field is not None and field != [])
        profile_completion = int((completed_fields / len(completion_fields)) * 100)

        # Convert to dict and add stats
        profile_dict = {
            "user_id": profile.user_id,
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.location,
            "work_authorization": profile.work_authorization,
            "years_of_experience": profile.years_of_experience,
            "career_level": profile.career_level,
            "professional_summary": profile.professional_summary,
            "programming_languages": profile.programming_languages,
            "frameworks_libraries": profile.frameworks_libraries,
            "tools_platforms": profile.tools_platforms,
            "soft_skills": profile.soft_skills,
            "job_titles": profile.job_titles,
            "companies": profile.companies,
            "industries": profile.industries,
            "experience_descriptions": profile.experience_descriptions,
            "degrees": profile.degrees,
            "institutions": profile.institutions,
            "graduation_years": profile.graduation_years,
            "relevant_coursework": profile.relevant_coursework,
            "desired_roles": profile.desired_roles,
            "preferred_locations": profile.preferred_locations,
            "salary_range_min": profile.salary_range_min,
            "salary_range_max": profile.salary_range_max,
            "job_types": profile.job_types,
            "company_size_preference": profile.company_size_preference,
            "ai_profile_summary": profile.ai_profile_summary,
            "ai_strengths": profile.ai_strengths,
            "ai_improvement_areas": profile.ai_improvement_areas,
            "ai_career_advice": profile.ai_career_advice,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
            "last_resume_upload": profile.last_resume_upload,
            "total_applications": total_applications,
            "total_resumes": total_resumes,
            "profile_completion": profile_completion
        }

        return profile_dict

    @staticmethod
    def create_profile(db: Session, user_id: str, profile_data: UserProfileCreate) -> UserProfile:
        """Create a new user profile"""
        # Check if profile already exists
        existing_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if existing_profile:
            # Update existing profile instead
            return ProfileService.update_profile(db, user_id, profile_data)

        # Convert None arrays to empty lists and handle list fields properly
        profile_dict = profile_data.model_dump()

        # Handle list fields that might be None
        list_fields = [
            'programming_languages', 'frameworks_libraries', 'tools_platforms',
            'desired_roles', 'preferred_locations', 'job_types', 'degrees',
            'institutions', 'graduation_years'
        ]

        for field in list_fields:
            if field in profile_dict and profile_dict[field] is None:
                profile_dict[field] = []

        db_profile = UserProfile(
            user_id=user_id,
            **profile_dict
        )
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile

    @staticmethod
    def update_profile(db: Session, user_id: str, profile_data: UserProfileUpdate) -> Optional[UserProfile]:
        """Update user profile and log changes"""
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return None

        update_data = profile_data.model_dump(exclude_unset=True)

        # Handle list fields that might be None
        list_fields = [
            'programming_languages', 'frameworks_libraries', 'tools_platforms',
            'desired_roles', 'preferred_locations', 'job_types', 'degrees',
            'institutions', 'graduation_years'
        ]

        for field in list_fields:
            if field in update_data and update_data[field] is None:
                update_data[field] = []

        # Track changes for audit - simplified

        # Update profile
        for field, value in update_data.items():
            setattr(profile, field, value)

        profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_settings(db: Session, user_id: str):
        """Get user settings - placeholder implementation"""
        return None

    @staticmethod
    def create_settings(db: Session, user_id: str, settings_data):
        """Create user settings - placeholder implementation"""
        return None

    @staticmethod
    def update_settings(db: Session, user_id: str, settings_data):
        """Update user settings - placeholder implementation"""
        return None

    @staticmethod
    def update_notification_settings(db: Session, user_id: str, notification_data):
        """Update notification preferences - placeholder implementation"""
        return None

    @staticmethod
    def update_email_tracking_settings(db: Session, user_id: str, tracking_data):
        """Update email tracking settings - placeholder implementation"""
        return None

    @staticmethod
    def update_privacy_settings(db: Session, user_id: str, privacy_data):
        """Update privacy settings - placeholder implementation"""
        return None

    @staticmethod
    def get_profile_change_history(db: Session, user_id: str, limit: int = 50):
        """Get profile change history for audit - placeholder implementation"""
        return []

    @staticmethod
    def _log_profile_change(db: Session, user_id: str, field: str, old_value: str, new_value: str):
        """Log profile changes for audit purposes - placeholder implementation"""
        pass