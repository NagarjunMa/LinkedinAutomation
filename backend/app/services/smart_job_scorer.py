import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import or_, desc

from app.db.session import SessionLocal
from app.models.job import JobListing, UserProfile

logger = logging.getLogger(__name__)

class SmartJobScoringService:
    """
    Simplified job scoring service without background tasks:
    1. Resume-based pre-scoring (disabled - no background tasks)
    2. Dynamic preference filtering (fast, real-time)
    3. Incremental scoring for new jobs (disabled - no background tasks)
    """

    def __init__(self):
        self.min_score_threshold = 60.0
        self.cache_duration_hours = 24

    # =====================================================
    # MAIN SCORING WORKFLOWS (DISABLED - NO BACKGROUND TASKS)
    # =====================================================

    def trigger_full_scoring_for_new_user(self, user_id: str) -> dict:
        """
        DISABLED: Background task functionality removed
        Returns immediate response instead of queuing
        """
        logger.info(f"Full job scoring disabled - no background tasks available for user: {user_id}")

        return {
            "message": "Full job scoring disabled - background tasks not available",
            "user_id": user_id,
            "status": "disabled",
            "reason": "Background task system removed during cleanup"
        }

    def trigger_scoring_for_new_job(self, job_id: int) -> dict:
        """
        DISABLED: Background task functionality removed
        Returns immediate response instead of queuing
        """
        logger.info(f"New job scoring disabled - no background tasks available for job: {job_id}")

        return {
            "message": "New job scoring disabled - background tasks not available",
            "job_id": job_id,
            "status": "disabled",
            "reason": "Background task system removed during cleanup"
        }

    def trigger_profile_update_scoring(self, user_id: str, days_back: int = 7) -> dict:
        """
        DISABLED: Background task functionality removed
        Returns immediate response instead of queuing
        """
        logger.info(f"Profile update scoring disabled - no background tasks available for user: {user_id}")

        return {
            "message": "Profile update scoring disabled - background tasks not available",
            "user_id": user_id,
            "status": "disabled",
            "reason": "Background task system removed during cleanup"
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
                JobListing.is_active.is_(True)
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
            total_jobs = db.query(JobListing).filter(JobListing.is_active.is_(True)).count()

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

    def calculate_job_relevance(self, job: JobListing) -> float:
        """
        Calculate basic job relevance score for contact discovery
        Simplified scoring without user-specific preferences
        """
        try:
            # Basic relevance scoring based on job attributes
            score = 50.0  # Base score

            # Boost for software engineering roles
            if any(keyword in job.title.lower() for keyword in ['software', 'engineer', 'developer', 'programmer']):
                score += 20

            # Boost for senior positions
            if any(keyword in job.title.lower() for keyword in ['senior', 'staff', 'principal', 'lead']):
                score += 15

            # Boost for full-time positions
            if job.job_type and 'full' in job.job_type.lower():
                score += 10

            # Boost for remote positions
            if job.location and 'remote' in job.location.lower():
                score += 5

            # Cap at 100
            return min(score, 100.0)

        except Exception as e:
            logger.error(f"Error calculating job relevance for job {job.id}: {e}")
            return 50.0  # Default score

# Create singleton instance
smart_job_scorer = SmartJobScoringService()
