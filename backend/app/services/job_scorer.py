import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.ai_service import ai_service
from app.models.job import UserProfile, JobListing
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

class JobScoringService:
    """
    AI-powered job scoring service that matches users with relevant jobs - JobScore functionality disabled
    """
    
    def __init__(self):
        self.ai_service = ai_service
        self.min_score_threshold = 60.0  # Only store scores >= 60%
        self.max_concurrent_scoring = 5  # Limit concurrent AI calls
        logger.info("JobScoringService initialized - JobScore functionality disabled")
    
    async def score_jobs_for_user(
        self, 
        user_id: str, 
        job_limit: int = 50,
        days_back: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Score recent jobs for a specific user - JobScore functionality disabled
        
        Args:
            user_id: User identifier
            job_limit: Maximum number of jobs to score
            days_back: How many days back to look for new jobs
            
        Returns:
            Empty list - JobScore functionality disabled
        """
        logger.info(f"Job scoring disabled for user {user_id} - JobScore model removed")
        return []
    
    async def score_all_users_daily(self) -> Dict[str, int]:
        """
        Daily batch job to score new jobs for all active users
        """
        db = SessionLocal()
        try:
            # Get all users with profiles
            active_users = db.query(UserProfile.user_id).all()
            
            results = {
                "users_processed": 0,
                "total_scores_generated": 0,
                "errors": 0
            }
            
            for (user_id,) in active_users:
                try:
                    user_scores = await self.score_jobs_for_user(user_id, job_limit=100, days_back=1)
                    results["users_processed"] += 1
                    results["total_scores_generated"] += len(user_scores)
                    
                    # Small delay between users
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error scoring jobs for user {user_id}: {e}")
                    results["errors"] += 1
            
            logger.info(f"Daily scoring complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in daily scoring batch: {e}")
            return {"users_processed": 0, "total_scores_generated": 0, "errors": 1}
        finally:
            db.close()
    
    async def get_top_matches_for_user(
        self, 
        user_id: str, 
        limit: int = 10,
        min_score: float = 70.0
    ) -> List[Dict[str, Any]]:
        """
        Get top job matches for a user - JobScore functionality disabled
        """
        logger.info(f"Top matches disabled for user {user_id} - JobScore model removed")
        return []
    
    async def _score_job_batch(
        self, 
        user_profile_dict: Dict[str, Any], 
        jobs: List[JobListing],
        user_id: str,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Score a batch of jobs concurrently - JobScore functionality disabled
        """
        logger.info(f"Job batch scoring disabled - JobScore model removed")
        return []
    
    async def _score_single_job(
        self, 
        user_profile_dict: Dict[str, Any], 
        job: JobListing
    ) -> Optional[Dict[str, Any]]:
        """
        Score a single job using AI
        """
        try:
            result = await self.ai_service.score_job_compatibility(
                user_profile=user_profile_dict,
                job_description=job.description or '',
                job_title=job.title,
                job_requirements=job.requirements or ''
            )
            return result
        except Exception as e:
            logger.error(f"Error scoring job {job.id}: {e}")
            return None
    
    def _user_profile_to_dict(self, profile: UserProfile) -> Dict[str, Any]:
        """
        Convert UserProfile model to dictionary for AI processing
        """
        return {
            "personal_info": {
                "full_name": profile.full_name,
                "location": profile.location,
                "work_authorization": profile.work_authorization
            },
            "professional_summary": {
                "years_of_experience": profile.years_of_experience,
                "career_level": profile.career_level,
                "summary": profile.professional_summary
            },
            "skills": {
                "programming_languages": profile.programming_languages or [],
                "frameworks_libraries": profile.frameworks_libraries or [],
                "tools_platforms": profile.tools_platforms or [],
                "soft_skills": profile.soft_skills or []
            },
            "experience": {
                "job_titles": profile.job_titles or [],
                "companies": profile.companies or [],
                "industries": profile.industries or [],
                "descriptions": profile.experience_descriptions or []
            },
            "education": {
                "degrees": profile.degrees or [],
                "institutions": profile.institutions or [],
                "graduation_years": profile.graduation_years or [],
                "coursework": profile.relevant_coursework or []
            },
            "preferences": {
                "desired_roles": profile.desired_roles or [],
                "preferred_locations": profile.preferred_locations or [],
                "salary_range_min": profile.salary_range_min,
                "salary_range_max": profile.salary_range_max,
                "job_types": profile.job_types or []
            }
        }

# Global job scoring service instance
job_scorer = JobScoringService() 