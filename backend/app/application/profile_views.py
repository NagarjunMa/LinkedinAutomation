"""Stable API projections for user profile data."""

from typing import Any

from app.models.job import UserProfile
from app.models.resume_document import ResumeDocument


def empty_profile_response(user_id: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
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
        "total_resume_versions": 0,
        "total_resume_evaluations": 0,
        "profile_completion": 0,
        "exists": False,
    }


def profile_response(
    user_id: str,
    profile: UserProfile | None,
    latest_resume: ResumeDocument | None,
    stats: dict[str, int],
) -> dict[str, Any]:
    derived = _derive_from_resume(latest_resume)
    completion_fields = [
        _pick(profile.full_name if profile else None, derived.get("full_name")),
        _pick(profile.email if profile else None, derived.get("email")),
        _pick(
            profile.programming_languages if profile else None,
            derived.get("programming_languages"),
        ),
        profile.preferred_locations if profile else None,
        profile.salary_range_min if profile else None,
        _pick(profile.career_level if profile else None, derived.get("career_level")),
        _pick(profile.degrees if profile else None, derived.get("degrees")),
        _pick(profile.institutions if profile else None, derived.get("institutions")),
        _pick(
            profile.professional_summary if profile else None,
            derived.get("professional_summary"),
        ),
        profile.desired_roles if profile else None,
        _pick(profile.job_titles if profile else None, derived.get("job_titles")),
        _pick(profile.companies if profile else None, derived.get("companies")),
    ]
    completed = sum(
        1 for field in completion_fields if field is not None and field != []
    )
    if profile:
        created_at = profile.created_at
        updated_at = profile.updated_at
    elif latest_resume:
        created_at = latest_resume.created_at
        updated_at = latest_resume.created_at
    else:
        raise ValueError("A profile or resume is required to build a profile response")
    return {
        "user_id": user_id,
        "full_name": _pick(
            profile.full_name if profile else None,
            derived.get("full_name"),
            "",
        ),
        "email": _pick(
            profile.email if profile else None,
            derived.get("email"),
            "",
        ),
        "phone": _pick(profile.phone if profile else None, derived.get("phone")),
        "location": _pick(
            profile.location if profile else None,
            derived.get("location"),
        ),
        "work_authorization": profile.work_authorization if profile else None,
        "years_of_experience": profile.years_of_experience if profile else None,
        "career_level": _pick(
            profile.career_level if profile else None,
            derived.get("career_level"),
        ),
        "professional_summary": _pick(
            profile.professional_summary if profile else None,
            derived.get("professional_summary"),
        ),
        "programming_languages": _pick(
            profile.programming_languages if profile else None,
            derived.get("programming_languages"),
            [],
        ),
        "frameworks_libraries": _pick(
            profile.frameworks_libraries if profile else None,
            derived.get("frameworks_libraries"),
            [],
        ),
        "tools_platforms": _pick(
            profile.tools_platforms if profile else None,
            derived.get("tools_platforms"),
            [],
        ),
        "soft_skills": profile.soft_skills if profile else [],
        "job_titles": _pick(
            profile.job_titles if profile else None,
            derived.get("job_titles"),
            [],
        ),
        "companies": _pick(
            profile.companies if profile else None,
            derived.get("companies"),
            [],
        ),
        "industries": profile.industries if profile else [],
        "experience_descriptions": _pick(
            profile.experience_descriptions if profile else None,
            derived.get("experience_descriptions"),
            [],
        ),
        "work_experiences": derived.get("work_experiences", []),
        "degrees": _pick(
            profile.degrees if profile else None,
            derived.get("degrees"),
            [],
        ),
        "institutions": _pick(
            profile.institutions if profile else None,
            derived.get("institutions"),
            [],
        ),
        "graduation_years": _pick(
            profile.graduation_years if profile else None,
            derived.get("graduation_years"),
            [],
        ),
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
        "created_at": created_at,
        "updated_at": updated_at,
        "last_resume_upload": (
            profile.last_resume_upload if profile else latest_resume.created_at
        ),
        **stats,
        "profile_completion": int(completed / len(completion_fields) * 100),
        "exists": profile is not None,
    }


def _pick(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "" and value != []:
            return value
    return None


def _derive_from_resume(resume: ResumeDocument | None) -> dict[str, Any]:
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
        "location": _infer_location(contact, experience, education),
        "career_level": "Professional" if experience else None,
        "professional_summary": parsed.get("summary"),
        "programming_languages": hard_skills,
        "frameworks_libraries": [],
        "tools_platforms": [],
        "job_titles": [item.get("role") for item in experience if item.get("role")],
        "companies": [
            item.get("company") for item in experience if item.get("company")
        ],
        "experience_descriptions": [
            " ".join(
                bullet.get("text", "")
                for bullet in item.get("bullets", [])
                if bullet.get("text")
            )
            for item in experience
        ],
        "work_experiences": work_experiences,
        "degrees": [item.get("degree") for item in education if item.get("degree")],
        "institutions": [
            item.get("school") for item in education if item.get("school")
        ],
        "graduation_years": [
            item.get("dates") for item in education if item.get("dates")
        ],
        "education_history": education_history,
    }


def _infer_location(
    contact: dict[str, Any],
    experience: list[dict[str, Any]],
    education: list[dict[str, Any]],
) -> str | None:
    if contact.get("location"):
        return contact["location"]
    for item in experience + education:
        if item.get("location"):
            return item["location"]
    return None
