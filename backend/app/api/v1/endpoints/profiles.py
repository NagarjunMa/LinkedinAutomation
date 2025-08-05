from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.job import UserProfile
from app.services.resume_parser import resume_parser
from app.services.job_scorer import job_scorer
from app.services.smart_job_scorer import smart_job_scorer
from app.core.ai_service import ai_service
from datetime import datetime

router = APIRouter()

@router.post("/upload-resume/{user_id}")
async def upload_resume(
    user_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and parse resume for a user
    Creates or updates user profile with AI-extracted information
    """
    try:
        # Parse resume file using AI
        parsed_data = await resume_parser.parse_resume_file(file)
        
        # Check if user profile already exists
        existing_profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if existing_profile:
            # Update existing profile
            _update_profile_from_parsed_data(existing_profile, parsed_data)
            existing_profile.updated_at = datetime.utcnow()
            existing_profile.last_resume_upload = datetime.utcnow()
            db.commit()
            db.refresh(existing_profile)
            profile = existing_profile
        else:
            # Create new profile
            profile = _create_profile_from_parsed_data(user_id, parsed_data)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        return {
            "success": True,
            "message": "Resume uploaded and parsed successfully",
            "profile_id": profile.id,
            "user_id": user_id,
            "parsing_summary": {
                "name": profile.full_name,
                "experience_years": profile.years_of_experience,
                "career_level": profile.career_level,
                "skills_count": len(profile.programming_languages or []) + len(profile.frameworks_libraries or []),
                "education_count": len(profile.degrees or []),
                "ai_summary": profile.ai_profile_summary
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@router.get("/profile/{user_id}")
async def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user profile information
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    return {
        "user_id": profile.user_id,
        "personal_info": {
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.location,
            "work_authorization": profile.work_authorization
        },
        "professional_summary": {
            "years_of_experience": profile.years_of_experience,
            "career_level": profile.career_level,
            "summary": profile.professional_summary
        },
        "skills": {
            "programming_languages": profile.programming_languages,
            "frameworks_libraries": profile.frameworks_libraries,
            "tools_platforms": profile.tools_platforms,
            "soft_skills": profile.soft_skills
        },
        "experience": {
            "job_titles": profile.job_titles,
            "companies": profile.companies,
            "industries": profile.industries,
            "descriptions": profile.experience_descriptions
        },
        "education": {
            "degrees": profile.degrees,
            "institutions": profile.institutions,
            "graduation_years": profile.graduation_years,
            "coursework": profile.relevant_coursework
        },
        "preferences": {
            "desired_roles": profile.desired_roles,
            "preferred_locations": profile.preferred_locations,
            "salary_range": {
                "min": profile.salary_range_min,
                "max": profile.salary_range_max
            },
            "job_types": profile.job_types,
            "company_size_preference": profile.company_size_preference
        },
        "ai_insights": {
            "profile_summary": profile.ai_profile_summary,
            "strengths": profile.ai_strengths,
            "improvement_areas": profile.ai_improvement_areas,
            "career_advice": profile.ai_career_advice
        },
        "metadata": {
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
            "last_resume_upload": profile.last_resume_upload
        }
    }

@router.put("/profile/{user_id}")
async def update_user_profile(
    user_id: str,
    profile_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update user profile information
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Update fields that are provided
    if "personal_info" in profile_data:
        personal = profile_data["personal_info"]
        if "full_name" in personal:
            profile.full_name = personal["full_name"]
        if "email" in personal:
            profile.email = personal["email"]
        if "phone" in personal:
            profile.phone = personal["phone"]
        if "location" in personal:
            profile.location = personal["location"]
        if "work_authorization" in personal:
            profile.work_authorization = personal["work_authorization"]
    
    if "preferences" in profile_data:
        prefs = profile_data["preferences"]
        if "desired_roles" in prefs:
            profile.desired_roles = prefs["desired_roles"]
        if "preferred_locations" in prefs:
            profile.preferred_locations = prefs["preferred_locations"]
        if "salary_range" in prefs:
            salary = prefs["salary_range"]
            if "min" in salary:
                profile.salary_range_min = salary["min"]
            if "max" in salary:
                profile.salary_range_max = salary["max"]
        if "job_types" in prefs:
            profile.job_types = prefs["job_types"]
        if "company_size_preference" in prefs:
            profile.company_size_preference = prefs["company_size_preference"]
    
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    
    return {"success": True, "message": "Profile updated successfully"}

@router.get("/matches/{user_id}")
async def get_job_matches(
    user_id: str,
    limit: int = 10,
    min_score: float = 70.0,
    db: Session = Depends(get_db)
):
    """
    Get top job matches for a user based on AI scoring
    """
    # Check if user profile exists
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Get top matches using smart job scorer for better performance
    matches = smart_job_scorer.get_filtered_job_matches(
        user_id=user_id,
        limit=limit,
        min_score=min_score
    )
    
    return {
        "user_id": user_id,
        "total_matches": len(matches),
        "min_score_threshold": min_score,
        "matches": matches,
        "scoring_method": "smart_filtered"
    }

@router.post("/score-jobs/{user_id}")
async def score_new_jobs(
    user_id: str,
    job_limit: int = 50,
    days_back: int = 1,
    db: Session = Depends(get_db)
):
    """
    Score new jobs for a user (manual trigger)
    """
    # Check if user profile exists
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Score jobs using job scorer service
    scored_jobs = await job_scorer.score_jobs_for_user(user_id, job_limit, days_back)
    
    return {
        "user_id": user_id,
        "jobs_scored": len(scored_jobs),
        "high_scores": len([j for j in scored_jobs if j['compatibility_score'] >= 80]),
        "medium_scores": len([j for j in scored_jobs if 60 <= j['compatibility_score'] < 80]),
        "top_matches": scored_jobs[:5]  # Return top 5 matches
    }

@router.post("/parse-text/{user_id}")
async def parse_resume_text(
    user_id: str,
    resume_text: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Parse resume from text input (for testing or direct text input)
    """
    try:
        # Parse resume text using AI
        parsed_data = await resume_parser.update_profile_from_text(resume_text)
        
        # Check if user profile already exists
        existing_profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if existing_profile:
            # Update existing profile
            _update_profile_from_parsed_data(existing_profile, parsed_data)
            existing_profile.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_profile)
            profile = existing_profile
        else:
            # Create new profile
            profile = _create_profile_from_parsed_data(user_id, parsed_data)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        return {
            "success": True,
            "message": "Resume text parsed successfully",
            "profile_summary": {
                "name": profile.full_name,
                "experience_years": profile.years_of_experience,
                "skills": profile.programming_languages,
                "ai_summary": profile.ai_profile_summary
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing resume text: {str(e)}")

@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all users with profiles (for admin/testing)
    """
    profiles = db.query(UserProfile).offset(skip).limit(limit).all()
    
    return {
        "users": [
            {
                "user_id": p.user_id,
                "full_name": p.full_name,
                "career_level": p.career_level,
                "years_of_experience": p.years_of_experience,
                "created_at": p.created_at,
                "last_resume_upload": p.last_resume_upload
            }
            for p in profiles
        ],
        "total": len(profiles)
    }

# Helper functions
def _create_profile_from_parsed_data(user_id: str, parsed_data: dict) -> UserProfile:
    """
    Create new UserProfile from parsed resume data
    """
    personal = parsed_data.get("personal_info", {})
    professional = parsed_data.get("professional_summary", {})
    skills = parsed_data.get("skills", {})
    experience = parsed_data.get("experience", {})
    education = parsed_data.get("education", {})
    preferences = parsed_data.get("preferences", {})
    ai_insights = parsed_data.get("ai_insights", {})
    
    profile = UserProfile(
        user_id=user_id,
        # Personal info
        full_name=personal.get("full_name", ""),
        email=personal.get("email", ""),
        phone=personal.get("phone", ""),
        location=personal.get("location", ""),
        work_authorization=personal.get("work_authorization", ""),
        
        # Professional summary
        years_of_experience=professional.get("years_of_experience", 0.0),
        career_level=professional.get("career_level", "entry"),
        professional_summary=professional.get("summary", ""),
        
        # Skills
        programming_languages=skills.get("programming_languages", []),
        frameworks_libraries=skills.get("frameworks_libraries", []),
        tools_platforms=skills.get("tools_platforms", []),
        soft_skills=skills.get("soft_skills", []),
        
        # Experience
        job_titles=experience.get("job_titles", []),
        companies=experience.get("companies", []),
        industries=experience.get("industries", []),
        experience_descriptions=experience.get("descriptions", []),
        
        # Education
        degrees=education.get("degrees", []),
        institutions=education.get("institutions", []),
        graduation_years=education.get("graduation_years", []),
        relevant_coursework=education.get("coursework", []),
        
        # Preferences
        desired_roles=preferences.get("desired_roles", []),
        preferred_locations=preferences.get("preferred_locations", []),
        salary_range_min=preferences.get("salary_range_min", 0),
        salary_range_max=preferences.get("salary_range_max", 0),
        job_types=preferences.get("job_types", ["Full-time"]),
        
        # AI insights
        ai_profile_summary=ai_insights.get("profile_summary", ""),
        ai_strengths=ai_insights.get("strengths", []),
        ai_improvement_areas=ai_insights.get("improvement_areas", []),
        ai_career_advice=ai_insights.get("career_advice", ""),
        
        last_resume_upload=datetime.utcnow()
    )
    
    return profile

def _update_profile_from_parsed_data(profile: UserProfile, parsed_data: dict) -> None:
    """
    Update existing UserProfile with new parsed data
    """
    personal = parsed_data.get("personal_info", {})
    professional = parsed_data.get("professional_summary", {})
    skills = parsed_data.get("skills", {})
    experience = parsed_data.get("experience", {})
    education = parsed_data.get("education", {})
    preferences = parsed_data.get("preferences", {})
    ai_insights = parsed_data.get("ai_insights", {})
    
    # Update fields (keep existing if new data is empty)
    if personal.get("full_name"):
        profile.full_name = personal["full_name"]
    if personal.get("email"):
        profile.email = personal["email"]
    if personal.get("phone"):
        profile.phone = personal["phone"]
    if personal.get("location"):
        profile.location = personal["location"]
    if personal.get("work_authorization"):
        profile.work_authorization = personal["work_authorization"]
    
    # Professional info
    if professional.get("years_of_experience"):
        profile.years_of_experience = professional["years_of_experience"]
    if professional.get("career_level"):
        profile.career_level = professional["career_level"]
    if professional.get("summary"):
        profile.professional_summary = professional["summary"]
    
    # Skills (merge with existing)
    if skills.get("programming_languages"):
        profile.programming_languages = list(set(
            (profile.programming_languages or []) + skills["programming_languages"]
        ))
    if skills.get("frameworks_libraries"):
        profile.frameworks_libraries = list(set(
            (profile.frameworks_libraries or []) + skills["frameworks_libraries"]
        ))
    if skills.get("tools_platforms"):
        profile.tools_platforms = list(set(
            (profile.tools_platforms or []) + skills["tools_platforms"]
        ))
    if skills.get("soft_skills"):
        profile.soft_skills = list(set(
            (profile.soft_skills or []) + skills["soft_skills"]
        ))
    
    # Update AI insights
    if ai_insights.get("profile_summary"):
        profile.ai_profile_summary = ai_insights["profile_summary"]
    if ai_insights.get("strengths"):
        profile.ai_strengths = ai_insights["strengths"]
    if ai_insights.get("improvement_areas"):
        profile.ai_improvement_areas = ai_insights["improvement_areas"]
    if ai_insights.get("career_advice"):
        profile.ai_career_advice = ai_insights["career_advice"]

@router.put("/preferences/{user_id}")
async def update_user_preferences(user_id: str, preferences: dict, db: Session = Depends(get_db)):
    """
    Update user job preferences for better AI matching
    """
    try:
        # Find existing profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Update preferences
        if "desired_roles" in preferences:
            profile.desired_roles = preferences["desired_roles"]
        if "preferred_locations" in preferences:
            profile.preferred_locations = preferences["preferred_locations"]
        if "salary_range_min" in preferences:
            profile.salary_range_min = preferences["salary_range_min"]
        if "salary_range_max" in preferences:
            profile.salary_range_max = preferences["salary_range_max"]
        if "job_types" in preferences:
            profile.job_types = preferences["job_types"]
        if "company_size_preference" in preferences:
            profile.company_size_preference = preferences["company_size_preference"]
        if "work_authorization" in preferences:
            profile.work_authorization = preferences["work_authorization"]
        
        # Set updated timestamp
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        
        return {
            "message": "Preferences updated successfully",
            "user_id": user_id,
            "preferences_updated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences for user {user_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error updating preferences")

# =====================================================
# SMART SCORING ENDPOINTS
# =====================================================

@router.post("/trigger-scoring/{user_id}")
async def trigger_user_scoring(user_id: str, db: Session = Depends(get_db)):
    """
    Trigger background scoring for all jobs against user's resume
    Use after resume upload or major profile changes
    """
    try:
        # Check if user profile exists
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Trigger background scoring
        result = smart_job_scorer.trigger_full_scoring_for_new_user(user_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering scoring for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error triggering job scoring")

@router.get("/scoring-status/{user_id}")
async def get_scoring_status(user_id: str, db: Session = Depends(get_db)):
    """
    Get the status of job scoring for a user
    """
    try:
        status = smart_job_scorer.get_user_scoring_status(user_id)
        return status
        
    except Exception as e:
        logger.error(f"Error getting scoring status for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching scoring status")

@router.post("/clear-scores/{user_id}")
async def clear_user_scores(user_id: str, db: Session = Depends(get_db)):
    """
    Clear all job scores for a user (for fresh re-scoring)
    """
    try:
        # Check if user profile exists
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        result = smart_job_scorer.clear_user_scores(user_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing scores for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error clearing job scores")

@router.post("/score-new-job/{job_id}")
async def trigger_job_scoring(job_id: int, db: Session = Depends(get_db)):
    """
    Trigger scoring of a new job against all existing users
    Use when adding new jobs to the system
    """
    try:
        # Check if job exists
        job = db.query(JobListing).filter(JobListing.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        result = smart_job_scorer.trigger_scoring_for_new_job(job_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering scoring for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Error triggering job scoring") 