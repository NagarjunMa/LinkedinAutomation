import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.ai_service import ai_service
from app.models.job import UserProfile, JobListing, JobScore
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

class JobScoringService:
    """
    AI-powered job scoring service that matches users with relevant jobs
    """
    
    def __init__(self):
        self.ai_service = ai_service
        self.min_score_threshold = 60.0  # Only store scores >= 60%
        self.max_concurrent_scoring = 5  # Limit concurrent AI calls
    
    async def score_jobs_for_user(
        self, 
        user_id: str, 
        job_limit: int = 50,
        days_back: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Score recent jobs for a specific user
        
        Args:
            user_id: User identifier
            job_limit: Maximum number of jobs to score
            days_back: How many days back to look for new jobs
            
        Returns:
            List of scored jobs with compatibility scores
        """
        db = SessionLocal()
        try:
            # Get user profile
            user_profile = db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not user_profile:
                logger.warning(f"No profile found for user {user_id}")
                return []
            
            # Get recent jobs that haven't been scored for this user
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Find jobs not yet scored for this user
            scored_job_ids = db.query(JobScore.job_id).filter(
                JobScore.user_id == user_id
            )
            
            recent_jobs = db.query(JobListing).filter(
                JobListing.extracted_date >= cutoff_date,
                JobListing.is_active == True,
                ~JobListing.id.in_(scored_job_ids)
            ).limit(job_limit).all()
            
            if not recent_jobs:
                logger.info(f"No new jobs to score for user {user_id}")
                return []
            
            logger.info(f"Scoring {len(recent_jobs)} jobs for user {user_id}")
            
            # Convert user profile to dict for AI
            user_profile_dict = self._user_profile_to_dict(user_profile)
            
            # Score jobs in batches to avoid rate limits
            scored_jobs = []
            for i in range(0, len(recent_jobs), self.max_concurrent_scoring):
                batch = recent_jobs[i:i + self.max_concurrent_scoring]
                batch_scores = await self._score_job_batch(user_profile_dict, batch, user_id, db)
                scored_jobs.extend(batch_scores)
                
                # Small delay between batches
                if i + self.max_concurrent_scoring < len(recent_jobs):
                    await asyncio.sleep(1)
            
            # Sort by compatibility score
            scored_jobs.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            logger.info(f"Successfully scored {len(scored_jobs)} jobs for user {user_id}")
            return scored_jobs
            
        except Exception as e:
            logger.error(f"Error scoring jobs for user {user_id}: {e}")
            return []
        finally:
            db.close()
    
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
        Get top job matches for a user based on stored scores
        """
        db = SessionLocal()
        try:
            # Get top scored jobs for user
            top_scores = db.query(JobScore, JobListing).join(
                JobListing, JobScore.job_id == JobListing.id
            ).filter(
                JobScore.user_id == user_id,
                JobScore.compatibility_score >= min_score,
                JobListing.is_active == True
            ).order_by(
                JobScore.compatibility_score.desc()
            ).limit(limit).all()
            
            results = []
            for job_score, job_listing in top_scores:
                results.append({
                    "job_id": job_listing.id,
                    "title": job_listing.title,
                    "company": job_listing.company,
                    "location": job_listing.location,
                    "salary_range": job_listing.salary_range,
                    "application_url": job_listing.application_url,
                    "posted_date": job_listing.posted_date,
                    "compatibility_score": job_score.compatibility_score,
                    "ai_reasoning": job_score.ai_reasoning,
                    "match_factors": job_score.match_factors,
                    "skills_match": job_score.skills_match_score,
                    "experience_match": job_score.experience_match_score,
                    "location_match": job_score.location_match_score
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting top matches for user {user_id}: {e}")
            return []
        finally:
            db.close()
    
    async def _score_job_batch(
        self, 
        user_profile_dict: Dict[str, Any], 
        jobs: List[JobListing],
        user_id: str,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Score a batch of jobs concurrently
        """
        # Create scoring tasks
        tasks = []
        for job in jobs:
            task = self._score_single_job(user_profile_dict, job)
            tasks.append(task)
        
        # Execute tasks concurrently
        scoring_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and save to database
        scored_jobs = []
        for i, result in enumerate(scoring_results):
            if isinstance(result, Exception):
                logger.error(f"Error scoring job {jobs[i].id}: {result}")
                continue
            
            if not result or result.get('compatibility_score', 0) < self.min_score_threshold:
                continue  # Skip low scores
            
            # Save to database
            job_score = JobScore(
                user_id=user_id,
                job_id=jobs[i].id,
                compatibility_score=result['compatibility_score'],
                confidence_score=result.get('confidence_score', 0.0),
                ai_reasoning=result.get('reasoning', ''),
                match_factors=result.get('match_factors', []),
                mismatch_factors=result.get('mismatch_factors', []),
                skills_match_score=result.get('skills_match_score', 0.0),
                location_match_score=result.get('location_match_score', 0.0),
                experience_match_score=result.get('experience_match_score', 0.0),
                salary_match_score=result.get('salary_match_score', 0.0),
                culture_match_score=result.get('culture_match_score', 0.0)
            )
            
            db.add(job_score)
            
            # Add job info to result
            result.update({
                "job_id": jobs[i].id,
                "title": jobs[i].title,
                "company": jobs[i].company,
                "location": jobs[i].location
            })
            
            scored_jobs.append(result)
        
        # Commit all scores for this batch
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error saving job scores to database: {e}")
            db.rollback()
        
        return scored_jobs
    
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