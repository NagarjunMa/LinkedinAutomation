from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.job import UserProfile
from app.models import JobApplication
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.resume_evaluation_v2 import ResumeEvaluationV2
from app.schemas.profile import (
    UserProfileCreate, UserProfileUpdate
)


class ProfileService:
    @staticmethod
    def get_profile_with_stats(db: Session, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile with statistics, deriving missing fields from resume v2 data."""
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        latest_resume = (
            db.query(ResumeDocument)
            .filter(ResumeDocument.user_id == user_id)
            .order_by(ResumeDocument.created_at.desc())
            .first()
        )
        if not profile and not latest_resume:
            return None

        # Calculate statistics
        total_applications = db.query(JobApplication).filter(JobApplication.user_id == user_id).count()
        total_resumes = db.query(ResumeDocument).filter(ResumeDocument.user_id == user_id).count()
        total_resume_versions = (
            db.query(ResumeVersion)
            .join(ResumeDocument, ResumeVersion.resume_document_id == ResumeDocument.id)
            .filter(ResumeDocument.user_id == user_id)
            .count()
        )
        total_resume_evaluations = (
            db.query(ResumeEvaluationV2)
            .filter(ResumeEvaluationV2.user_id == user_id)
            .count()
        )
        derived = ProfileService._derive_from_resume(latest_resume) if latest_resume else {}

        # Calculate profile completion percentage
        completion_fields = [
            ProfileService._pick(profile.full_name if profile else None, derived.get("full_name")),
            ProfileService._pick(profile.email if profile else None, derived.get("email")),
            ProfileService._pick(profile.programming_languages if profile else None, derived.get("programming_languages")),
            profile.preferred_locations if profile else None,
            profile.salary_range_min if profile else None,
            ProfileService._pick(profile.career_level if profile else None, derived.get("career_level")),
            ProfileService._pick(profile.degrees if profile else None, derived.get("degrees")),
            ProfileService._pick(profile.institutions if profile else None, derived.get("institutions")),
            ProfileService._pick(profile.professional_summary if profile else None, derived.get("professional_summary")),
            profile.desired_roles if profile else None,
            ProfileService._pick(profile.job_titles if profile else None, derived.get("job_titles")),
            ProfileService._pick(profile.companies if profile else None, derived.get("companies")),
        ]
        completed_fields = sum(1 for field in completion_fields if field is not None and field != [])
        profile_completion = int((completed_fields / len(completion_fields)) * 100)

        # Convert to dict and add stats
        profile_dict = {
            "user_id": user_id,
            "full_name": ProfileService._pick(profile.full_name if profile else None, derived.get("full_name"), ""),
            "email": ProfileService._pick(profile.email if profile else None, derived.get("email"), ""),
            "phone": ProfileService._pick(profile.phone if profile else None, derived.get("phone")),
            "location": ProfileService._pick(profile.location if profile else None, derived.get("location")),
            "work_authorization": profile.work_authorization if profile else None,
            "years_of_experience": profile.years_of_experience if profile else None,
            "career_level": ProfileService._pick(profile.career_level if profile else None, derived.get("career_level")),
            "professional_summary": ProfileService._pick(profile.professional_summary if profile else None, derived.get("professional_summary")),
            "programming_languages": ProfileService._pick(profile.programming_languages if profile else None, derived.get("programming_languages"), []),
            "frameworks_libraries": ProfileService._pick(profile.frameworks_libraries if profile else None, derived.get("frameworks_libraries"), []),
            "tools_platforms": ProfileService._pick(profile.tools_platforms if profile else None, derived.get("tools_platforms"), []),
            "soft_skills": profile.soft_skills if profile else [],
            "job_titles": ProfileService._pick(profile.job_titles if profile else None, derived.get("job_titles"), []),
            "companies": ProfileService._pick(profile.companies if profile else None, derived.get("companies"), []),
            "industries": profile.industries if profile else [],
            "experience_descriptions": ProfileService._pick(profile.experience_descriptions if profile else None, derived.get("experience_descriptions"), []),
            "work_experiences": derived.get("work_experiences", []),
            "degrees": ProfileService._pick(profile.degrees if profile else None, derived.get("degrees"), []),
            "institutions": ProfileService._pick(profile.institutions if profile else None, derived.get("institutions"), []),
            "graduation_years": ProfileService._pick(profile.graduation_years if profile else None, derived.get("graduation_years"), []),
            "education_history": derived.get("education_history", []),
            "relevant_coursework": profile.relevant_coursework if profile else [],
            "desired_roles": profile.desired_roles if profile else [],
            "preferred_locations": profile.preferred_locations if profile else [],
            "salary_range_min": profile.salary_range_min if profile else None,
            "salary_range_max": profile.salary_range_max if profile else None,
            "job_types": profile.job_types if profile else [],
            "company_size_preference": profile.company_size_preference if profile else [],
            "ai_profile_summary": profile.ai_profile_summary if profile else None,
            "ai_strengths": profile.ai_strengths if profile else [],
            "ai_improvement_areas": profile.ai_improvement_areas if profile else [],
            "ai_career_advice": profile.ai_career_advice if profile else None,
            "created_at": profile.created_at if profile else latest_resume.created_at,
            "updated_at": profile.updated_at if profile else latest_resume.created_at,
            "last_resume_upload": profile.last_resume_upload if profile else latest_resume.created_at,
            "total_applications": total_applications,
            "total_resumes": total_resumes,
            "total_resume_versions": total_resume_versions,
            "total_resume_evaluations": total_resume_evaluations,
            "profile_completion": profile_completion
        }

        return profile_dict

    @staticmethod
    def _pick(*values):
        for value in values:
            if value is not None and value != "" and value != []:
                return value
        return None

    @staticmethod
    def _derive_from_resume(resume: ResumeDocument | None) -> Dict[str, Any]:
        if not resume:
            return {}
        parsed = resume.parsed_json or {}
        contact = parsed.get("contact") or {}
        skills = parsed.get("skills") or {}
        experience = parsed.get("experience") or []
        education = parsed.get("education") or []
        hard_skills = skills.get("hard") or []

        work_experiences = [
            {
                "job_title": item.get("role") or "",
                "company": item.get("company") or "",
                "location": item.get("location") or "",
                "start_date": item.get("dates") or "",
                "end_date": None,
            }
            for item in experience
        ]
        education_history = [
            {
                "university": item.get("school") or "",
                "degree": item.get("degree") or "",
                "field_of_study": "",
                "location": item.get("location") or "",
                "start_date": item.get("dates") or "",
                "end_date": None,
            }
            for item in education
        ]

        return {
            "full_name": contact.get("name"),
            "email": contact.get("email"),
            "phone": contact.get("phone"),
            "location": ProfileService._infer_location(contact, experience, education),
            "career_level": "Professional" if experience else None,
            "professional_summary": parsed.get("summary"),
            "programming_languages": hard_skills,
            "frameworks_libraries": [],
            "tools_platforms": [],
            "job_titles": [item.get("role") for item in experience if item.get("role")],
            "companies": [item.get("company") for item in experience if item.get("company")],
            "experience_descriptions": [
                " ".join(b.get("text", "") for b in item.get("bullets", []) if b.get("text"))
                for item in experience
            ],
            "work_experiences": work_experiences,
            "degrees": [item.get("degree") for item in education if item.get("degree")],
            "institutions": [item.get("school") for item in education if item.get("school")],
            "graduation_years": [item.get("dates") for item in education if item.get("dates")],
            "education_history": education_history,
        }

    @staticmethod
    def _infer_location(contact: Dict[str, Any], experience: list[dict], education: list[dict]) -> Optional[str]:
        if contact.get("location"):
            return contact["location"]
        for item in experience + education:
            if item.get("location"):
                return item["location"]
        return None

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
