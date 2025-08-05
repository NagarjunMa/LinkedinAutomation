import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import current_task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.job import JobListing, UserProfile
from app.services.job_scorer import job_scorer
from app.core.ai_service import ai_service

logger = logging.getLogger(__name__)

# =====================================================
# BACKGROUND JOB SCORING TASKS
# =====================================================

@celery_app.task(bind=True, name="score_all_jobs_for_new_user")
def score_all_jobs_for_new_user(self, user_id: str):
    """
    EXPENSIVE OPERATION: Score all existing jobs against a new user's resume
    This runs when user uploads resume for the first time
    """
    try:
        logger.info(f"Starting complete job scoring for new user: {user_id}")
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Initializing...', 'progress': 0})
        
        # Run the async scoring
        result = asyncio.run(_score_all_jobs_for_user_async(user_id, self))
        
        logger.info(f"Completed job scoring for user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error scoring jobs for user {user_id}: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(bind=True, name="score_new_job_for_all_users")
def score_new_job_for_all_users(self, job_id: int):
    """
    Score a single new job against all existing user profiles
    This runs when a new job is added to the system
    """
    try:
        logger.info(f"Starting scoring for new job {job_id} against all users")
        
        self.update_state(state='PROGRESS', meta={'status': 'Loading job and users...', 'progress': 0})
        
        result = asyncio.run(_score_job_for_all_users_async(job_id, self))
        
        logger.info(f"Completed scoring job {job_id} for all users: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error scoring job {job_id} for all users: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(bind=True, name="update_user_job_scores")
def update_user_job_scores(self, user_id: str, days_back: int = 7):
    """
    Update scores for recent jobs when user profile changes
    Less expensive than full re-scoring
    """
    try:
        logger.info(f"Updating recent job scores for user: {user_id}")
        
        self.update_state(state='PROGRESS', meta={'status': 'Finding recent jobs...', 'progress': 0})
        
        result = asyncio.run(_update_recent_scores_async(user_id, days_back, self))
        
        logger.info(f"Updated recent scores for user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error updating scores for user {user_id}: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(name="cleanup_old_job_scores")
def cleanup_old_job_scores():
    """
    Clean up old job scores to maintain database performance - JobScore functionality disabled
    """
    logger.info("Job score cleanup disabled - JobScore model removed")
    return {"deleted_scores": 0, "note": "JobScore functionality disabled"}

# =====================================================
# ASYNC HELPER FUNCTIONS
# =====================================================

async def _score_all_jobs_for_user_async(user_id: str, task=None):
    """Score all jobs for a single user (expensive operation)"""
    db = SessionLocal()
    try:
        # Get user profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise ValueError(f"User profile not found: {user_id}")
        
        # Get all active jobs
        jobs = db.query(JobListing).filter(JobListing.is_active == True).all()
        
        if task:
            task.update_state(
                state='PROGRESS', 
                meta={'status': f'Found {len(jobs)} jobs to score', 'progress': 5}
            )
        
        # Convert profile to dict for AI service
        profile_dict = {
            'skills': {
                'programming_languages': profile.programming_languages or [],
                'frameworks_libraries': profile.frameworks_libraries or [],
                'tools_platforms': profile.tools_platforms or [],
                'soft_skills': profile.soft_skills or []
            },
            'professional_summary': {
                'years_of_experience': profile.years_of_experience or 0,
                'career_level': profile.career_level or 'entry'
            },
            'personal_info': {
                'location': profile.location or '',
                'work_authorization': profile.work_authorization or ''
            },
            'preferences': {
                'desired_roles': profile.desired_roles or [],
                'preferred_locations': profile.preferred_locations or [],
                'salary_range_min': profile.salary_range_min or 0,
                'salary_range_max': profile.salary_range_max or 0,
                'job_types': profile.job_types or []
            }
        }
        
        # Score jobs in batches for better performance
        batch_size = 10
        total_scored = 0
        successful_scores = 0
        
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i+batch_size]
            
            if task:
                progress = int((i / len(jobs)) * 90) + 5  # 5-95% range
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Scoring batch {i//batch_size + 1}/{(len(jobs)//batch_size) + 1}',
                        'progress': progress,
                        'scored': total_scored,
                        'total': len(jobs)
                    }
                )
            
            # Score batch concurrently
            batch_tasks = []
            for job in batch:
                batch_tasks.append(_score_single_job_async(profile_dict, job, user_id, db))
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                total_scored += 1
                if not isinstance(result, Exception):
                    successful_scores += 1
                    
        if task:
            task.update_state(
                state='PROGRESS',
                meta={
                    'status': 'Finalizing...',
                    'progress': 100,
                    'scored': successful_scores,
                    'total': len(jobs)
                }
            )
        
        return {
            'user_id': user_id,
            'total_jobs': len(jobs),
            'successfully_scored': successful_scores,
            'failed_scores': total_scored - successful_scores
        }
        
    finally:
        db.close()

async def _score_job_for_all_users_async(job_id: int, task=None):
    """Score a single job for all users"""
    db = SessionLocal()
    try:
        # Get the job
        job = db.query(JobListing).filter(JobListing.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Get all users with profiles
        users = db.query(UserProfile).all()
        
        if task:
            task.update_state(
                state='PROGRESS',
                meta={'status': f'Found {len(users)} users to score against', 'progress': 10}
            )
        
        successful_scores = 0
        
        for i, profile in enumerate(users):
            try:
                if task:
                    progress = int((i / len(users)) * 80) + 10  # 10-90% range
                    task.update_state(
                        state='PROGRESS',
                        meta={
                            'status': f'Scoring for user {i+1}/{len(users)}',
                            'progress': progress
                        }
                    )
                
                # Convert profile to dict
                profile_dict = {
                    'skills': {
                        'programming_languages': profile.programming_languages or [],
                        'frameworks_libraries': profile.frameworks_libraries or [],
                    },
                    'professional_summary': {
                        'years_of_experience': profile.years_of_experience or 0,
                        'career_level': profile.career_level or 'entry'
                    },
                    'personal_info': {
                        'location': profile.location or ''
                    }
                }
                
                # Score the job
                await _score_single_job_async(profile_dict, job, profile.user_id, db)
                successful_scores += 1
                
            except Exception as e:
                logger.warning(f"Failed to score job {job_id} for user {profile.user_id}: {e}")
        
        return {
            'job_id': job_id,
            'total_users': len(users),
            'successfully_scored': successful_scores
        }
        
    finally:
        db.close()

async def _update_recent_scores_async(user_id: str, days_back: int, task=None):
    """Update scores for recent jobs only"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get recent jobs that need re-scoring
        recent_jobs = db.query(JobListing).filter(
            JobListing.extracted_date >= cutoff_date,
            JobListing.is_active == True
        ).all()
        
        if task:
            task.update_state(
                state='PROGRESS',
                meta={'status': f'Found {len(recent_jobs)} recent jobs', 'progress': 20}
            )
        
        # Use existing job scoring service
        result = await job_scorer.score_jobs_for_user(user_id, job_limit=len(recent_jobs), days_back=days_back)
        
        return {
            'user_id': user_id,
            'recent_jobs_scored': len(result),
            'days_back': days_back
        }
        
    finally:
        db.close()

async def _score_single_job_async(profile_dict: Dict[str, Any], job: JobListing, user_id: str, db: Session):
    """Score a single job against a user profile - JobScore functionality disabled"""
    logger.info(f"Job scoring disabled for job {job.id} - JobScore model removed")
    return None 