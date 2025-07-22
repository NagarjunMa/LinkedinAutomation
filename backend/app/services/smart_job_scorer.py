import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.db.session import SessionLocal
from app.models.job import JobListing, UserProfile, JobScore
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
        FAST: Get job matches using pre-computed scores + dynamic filtering
        This is the main method for real-time job recommendations
        """
        db = SessionLocal()
        try:
            # Get user profile for fallback preferences
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
            
            # Start with base query using pre-computed scores
            query = db.query(JobScore, JobListing).join(
                JobListing, JobScore.job_id == JobListing.id
            ).filter(
                JobScore.user_id == user_id,
                JobScore.compatibility_score >= min_score,
                JobListing.is_active == True
            )
            
            # Apply dynamic filters based on preferences
            query = self._apply_preference_filters(query, preferences)
            
            # Get top matches
            scored_jobs = query.order_by(
                desc(JobScore.compatibility_score)
            ).limit(limit).all()
            
            # Format results
            results = []
            for job_score, job_listing in scored_jobs:
                # Calculate dynamic preference bonus
                preference_bonus = self._calculate_preference_bonus(job_listing, preferences)
                final_score = min(100.0, job_score.compatibility_score + preference_bonus)
                
                results.append({
                    "job_id": job_listing.id,
                    "title": job_listing.title,
                    "company": job_listing.company,
                    "location": job_listing.location,
                    "salary_range": job_listing.salary_range,
                    "application_url": job_listing.application_url,
                    "posted_date": job_listing.posted_date,
                    "compatibility_score": final_score,
                    "base_score": job_score.compatibility_score,
                    "preference_bonus": preference_bonus,
                    "ai_reasoning": job_score.ai_reasoning,
                    "match_factors": job_score.match_factors,
                    "skills_match": job_score.skills_match_score,
                    "experience_match": job_score.experience_match_score,
                    "location_match": job_score.location_match_score,
                    "last_scored": job_score.scored_at
                })
            
            return results
            
        finally:
            db.close()
    
    def _apply_preference_filters(self, query, preferences: Dict[str, Any]):
        """Apply user preferences as database filters"""
        
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
        """Get status of job scoring for a user"""
        db = SessionLocal()
        try:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                return {"status": "no_profile", "message": "User profile not found"}
            
            # Count total jobs and scored jobs
            total_jobs = db.query(JobListing).filter(JobListing.is_active == True).count()
            scored_jobs = db.query(JobScore).filter(JobScore.user_id == user_id).count()
            
            # Check for recent scores
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_scores = db.query(JobScore).filter(
                JobScore.user_id == user_id,
                JobScore.scored_at >= recent_cutoff
            ).count()
            
            # Determine status
            if scored_jobs == 0:
                status = "not_scored"
                message = "No jobs scored yet. Upload resume to start."
            elif scored_jobs < total_jobs * 0.1:
                status = "partial_scoring"
                message = f"Initial scoring in progress: {scored_jobs}/{total_jobs}"
            elif recent_scores > 0:
                status = "up_to_date"
                message = f"Scoring current: {scored_jobs} jobs scored"
            else:
                status = "needs_refresh"
                message = "Scores may be outdated. Consider refreshing."
            
            return {
                "status": status,
                "message": message,
                "total_jobs": total_jobs,
                "scored_jobs": scored_jobs,
                "recent_scores": recent_scores,
                "last_scored": profile.updated_at
            }
            
        finally:
            db.close()
    
    def clear_user_scores(self, user_id: str) -> Dict[str, Any]:
        """Clear all scores for a user (for fresh re-scoring)"""
        db = SessionLocal()
        try:
            deleted_count = db.query(JobScore).filter(JobScore.user_id == user_id).delete()
            db.commit()
            
            logger.info(f"Cleared {deleted_count} scores for user {user_id}")
            return {"deleted_scores": deleted_count, "user_id": user_id}
            
        finally:
            db.close()

# Create singleton instance
smart_job_scorer = SmartJobScoringService() 