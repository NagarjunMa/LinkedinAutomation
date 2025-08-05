import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.db.session import SessionLocal
from app.models.job import JobListing, UserProfile
from app.tasks.scoring_tasks import (
    score_all_jobs_for_new_user,
    score_new_job_for_all_users,
    update_user_job_scores
)

logger = logging.getLogger(__name__)

class SmartJobScoringService:
    """
    Scalable job scoring service implementing the efficient architecture:
    1. Resume-based pre-scoring (expensive, one-time)
    2. Dynamic preference filtering (fast, real-time)  
    3. Incremental scoring for new jobs (background queue)
    """
    
    def __init__(self):
        self.min_score_threshold = 60.0
        self.cache_duration_hours = 24
    
    # =====================================================
    # MAIN SCORING WORKFLOWS
    # =====================================================
    
    def trigger_full_scoring_for_new_user(self, user_id: str) -> dict:
        """
        EXPENSIVE: Score all existing jobs against new user's resume
        Runs in background via Celery
        """
        logger.info(f"Triggering full job scoring for new user: {user_id}")
        
        # Queue the expensive operation
        task = score_all_jobs_for_new_user.delay(user_id)
        
        return {
            "message": "Full job scoring initiated",
            "task_id": task.id,
            "user_id": user_id,
            "status": "queued",
            "estimated_time_minutes": "5-15"
        }
    
    def trigger_scoring_for_new_job(self, job_id: int) -> dict:
        """
        Score a new job against all existing users
        Runs in background via Celery
        """
        logger.info(f"Triggering scoring for new job: {job_id}")
        
        # Queue the scoring operation  
        task = score_new_job_for_all_users.delay(job_id)
        
        return {
            "message": "New job scoring initiated",
            "task_id": task.id, 
            "job_id": job_id,
            "status": "queued",
            "estimated_time_minutes": "2-5"
        }
    
    def trigger_profile_update_scoring(self, user_id: str, days_back: int = 7) -> dict:
        """
        Update scores for recent jobs when user profile changes
        Less expensive than full re-scoring
        """
        logger.info(f"Triggering profile update scoring for user: {user_id}")
        
        # Queue the update operation
        task = update_user_job_scores.delay(user_id, days_back)
        
        return {
            "message": "Profile update scoring initiated",
            "task_id": task.id,
            "user_id": user_id,
            "status": "queued",
            "estimated_time_minutes": "1-3"
        }
    
    # =====================================================
    # FAST PREFERENCE-BASED FILTERING
    # =====================================================
    
    def get_filtered_job_matches(
        self, 
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        min_score: float = 70.0
    ) -> List[Dict[str, Any]]:
        """
        Get filtered job matches - JobScore functionality disabled
        Returns basic job listings with simple scoring
        """
        db = SessionLocal()
        try:
            # Get user profile for preferences
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                return []
            
            # Use provided preferences or fall back to profile preferences
            if not preferences:
                preferences = {
                    'preferred_locations': profile.preferred_locations or [],
                    'salary_range_min': profile.salary_range_min or 0,
                    'salary_range_max': profile.salary_range_max or 999999,
                    'job_types': profile.job_types or [],
                    'desired_roles': profile.desired_roles or []
                }
            
            # Simple query without JobScore - just get active jobs
            query = db.query(JobListing).filter(
                JobListing.is_active == True
            )
            
            # Apply basic filters
            query = self._apply_basic_filters(query, preferences)
            
            # Get jobs ordered by extracted date (newest first)
            jobs = query.order_by(desc(JobListing.extracted_date)).limit(limit).all()
            
            # Format results with simple scoring
            results = []
            for job_listing in jobs:
                # Calculate simple score based on preferences
                simple_score = self._calculate_simple_score(job_listing, preferences)
                
                results.append({
                    "job_id": job_listing.id,
                    "title": job_listing.title,
                    "company": job_listing.company,
                    "location": job_listing.location,
                    "salary_range": job_listing.salary_range,
                    "application_url": job_listing.application_url,
                    "posted_date": job_listing.posted_date,
                    "compatibility_score": simple_score,
                    "base_score": simple_score,
                    "preference_bonus": 0.0,
                    "ai_reasoning": "Simple scoring - JobScore functionality disabled",
                    "match_factors": ["basic_filtering"],
                    "skills_match": 50.0,
                    "experience_match": 50.0,
                    "location_match": 50.0,
                    "last_scored": job_listing.extracted_date
                })
            
            return results
            
        finally:
            db.close()
    
    def _apply_basic_filters(self, query, preferences: Dict[str, Any]):
        """Apply basic user preferences as database filters"""
        
        # Location filtering
        preferred_locations = preferences.get('preferred_locations', [])
        if preferred_locations:
            location_filters = []
            for location in preferred_locations:
                if location.lower() in ['remote', 'work from home']:
                    location_filters.append(JobListing.location.ilike('%remote%'))
                    location_filters.append(JobListing.location.ilike('%work from home%'))
                else:
                    location_filters.append(JobListing.location.ilike(f'%{location}%'))
            
            if location_filters:
                query = query.filter(or_(*location_filters))
        
        # Salary filtering (using string matching since salary_range is a string field)
        salary_min = preferences.get('salary_range_min', 0)
        salary_max = preferences.get('salary_range_max', 999999)
        
        # Basic salary filtering using string matching
        if salary_min > 50000:  # Only filter if minimum is significant
            # Look for salary ranges that might include our minimum
            salary_filters = []
            for threshold in [salary_min // 1000 * 1000, (salary_min + 10000) // 1000 * 1000]:
                salary_filters.append(JobListing.salary_range.ilike(f'%{threshold//1000}k%'))
                salary_filters.append(JobListing.salary_range.ilike(f'%{threshold:,}%'))
            
            # Include jobs without salary info
            salary_filters.append(JobListing.salary_range.is_(None))
            salary_filters.append(JobListing.salary_range == '')
            
            if salary_filters:
                query = query.filter(or_(*salary_filters))
        
        # Job type filtering
        job_types = preferences.get('job_types', [])
        if job_types:
            type_filters = []
            for job_type in job_types:
                if job_type.lower() == 'remote':
                    type_filters.append(JobListing.location.ilike('%remote%'))
                elif job_type.lower() == 'full-time':
                    type_filters.append(JobListing.title.ilike('%full%time%'))
                elif job_type.lower() == 'part-time':
                    type_filters.append(JobListing.title.ilike('%part%time%'))
                elif job_type.lower() == 'contract':
                    type_filters.append(JobListing.title.ilike('%contract%'))
            
            if type_filters:
                query = query.filter(or_(*type_filters))
        
        # Role filtering
        desired_roles = preferences.get('desired_roles', [])
        if desired_roles:
            role_filters = []
            for role in desired_roles:
                role_filters.append(JobListing.title.ilike(f'%{role}%'))
            
            if role_filters:
                query = query.filter(or_(*role_filters))
        
        return query
    
    def _calculate_simple_score(self, job: JobListing, preferences: Dict[str, Any]) -> float:
        """Calculate simple compatibility score based on preferences"""
        score = 50.0  # Base score
        
        # Location bonus
        preferred_locations = preferences.get('preferred_locations', [])
        if preferred_locations:
            for location in preferred_locations:
                if location.lower() in ['remote', 'work from home']:
                    if 'remote' in (job.location or '').lower():
                        score += 20.0
                elif location.lower() in (job.location or '').lower():
                    score += 15.0
        
        # Job type bonus
        job_types = preferences.get('job_types', [])
        if job_types:
            for job_type in job_types:
                if job_type.lower() in (job.title or '').lower():
                    score += 10.0
        
        return min(100.0, score)

    def _calculate_preference_bonus(self, job: JobListing, preferences: Dict[str, Any]) -> float:
        """Calculate bonus score based on preference matches"""
        bonus = 0.0
        
        # Location bonus
        preferred_locations = preferences.get('preferred_locations', [])
        if preferred_locations:
            for location in preferred_locations:
                if location.lower() in job.location.lower():
                    bonus += 2.0
                    break
        
        # Role title bonus
        desired_roles = preferences.get('desired_roles', [])
        if desired_roles:
            for role in desired_roles:
                if role.lower() in job.title.lower():
                    bonus += 3.0
                    break
        
        # Remote work bonus
        job_types = preferences.get('job_types', [])
        if 'remote' in [jt.lower() for jt in job_types]:
            if 'remote' in job.location.lower() or 'work from home' in job.location.lower():
                bonus += 5.0
        
        return min(bonus, 10.0)  # Cap bonus at 10 points
    
    # =====================================================
    # SCORING STATUS AND CACHE MANAGEMENT
    # =====================================================
    
    def get_user_scoring_status(self, user_id: str) -> Dict[str, Any]:
        """Get status of job scoring for a user - JobScore functionality disabled"""
        db = SessionLocal()
        try:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                return {"status": "no_profile", "message": "User profile not found"}
            
            # Count total jobs
            total_jobs = db.query(JobListing).filter(JobListing.is_active == True).count()
            
            # Check for recent jobs
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_jobs = db.query(JobListing).filter(
                JobListing.extracted_date >= recent_cutoff
            ).count()
            
            return {
                "status": "basic_scoring",
                "message": "Using basic job filtering - JobScore functionality disabled",
                "total_jobs": total_jobs,
                "scored_jobs": total_jobs,  # All jobs are "scored" with basic filtering
                "recent_scores": recent_jobs,
                "last_scored": profile.updated_at,
                "note": "JobScore functionality disabled - using basic job counts"
            }
            
        finally:
            db.close()
    
    def clear_user_scores(self, user_id: str) -> Dict[str, Any]:
        """Clear all scores for a user - JobScore functionality disabled"""
        return {
            "deleted_scores": 0, 
            "user_id": user_id,
            "note": "JobScore functionality disabled - no scores to clear"
        }

# Create singleton instance
smart_job_scorer = SmartJobScoringService() 