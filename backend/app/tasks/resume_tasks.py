"""
Celery tasks for AI-powered resume evaluation and processing.
Optimized for heavy AI workloads with proper error handling and progress tracking.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from celery import current_task
from celery.exceptions import Retry

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.consolidated_resume_evaluator import ConsolidatedResumeEvaluator
from app.core.ai_service import get_ai_service
from app.models.resume import Resume, ResumeEvaluation
from app.models.user import User

logger = logging.getLogger(__name__)


def _convert_ats_score_to_category(value):
    """Convert ATS compatibility score/value to categorical rating"""
    if isinstance(value, (int, float)):
        if value >= 8:
            return "excellent"
        elif value >= 6:
            return "good"
        elif value >= 4:
            return "fair"
        else:
            return "poor"
    elif isinstance(value, str):
        try:
            score = float(value)
            if score >= 8:
                return "excellent"
            elif score >= 6:
                return "good"
            elif score >= 4:
                return "fair"
            else:
                return "poor"
        except ValueError:
            if value.lower() in ["excellent", "good", "fair", "poor"]:
                return value.lower()
            return "fair"
    return "fair"


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    name='app.tasks.resume_tasks.evaluate_resume_task'
)
def evaluate_resume_task(
    self,
    resume_id: str,
    file_path: str,
    file_type: str,
    target_role: Optional[str] = None,
    target_seniority: Optional[str] = None,
    process_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Celery task for AI-powered resume evaluation using consolidated evaluator.

    This task replaces the FastAPI BackgroundTasks implementation with a proper
    Celery task that can handle heavy AI workloads, provides progress tracking,
    and includes comprehensive error handling.

    Args:
        resume_id: Unique resume identifier
        file_path: Path to resume file for text extraction
        file_type: MIME type of resume file
        target_role: Optional target role for evaluation context
        target_seniority: Optional target seniority for evaluation context
        process_id: Optional process identifier for lock management

    Returns:
        Dict containing evaluation results and status

    Raises:
        Retry: If evaluation fails and can be retried
        Exception: For fatal errors that should not be retried
    """

    # Update task progress - Starting evaluation
    current_task.update_state(
        state='PROGRESS',
        meta={'progress': 0, 'stage': 'initializing', 'resume_id': resume_id}
    )

    # Create new database session for background task
    db = SessionLocal()

    try:
        # Initialize AI service for background task
        try:
            ai_service = get_ai_service()
            logger.info(f"AI service initialized for resume {resume_id}")
        except Exception as ai_init_error:
            logger.error(f"Failed to initialize AI service for resume {resume_id}: {ai_init_error}")
            # Mark resume as failed immediately if AI service can't be initialized
            _update_resume_status(db, resume_id, "failed", process_id, release_lock=True)
            raise Exception(f"AI service initialization failed: {ai_init_error}")

        # Update task progress - AI service ready
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'stage': 'ai_service_ready', 'resume_id': resume_id}
        )

        # Get resume record with current lock info
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            logger.error(f"Resume {resume_id} not found during background evaluation")
            raise Exception(f"Resume {resume_id} not found")

        # Verify this process owns the lock (if process_id provided)
        if process_id and resume.locked_by != process_id:
            logger.error(f"Process {process_id} does not own lock for resume {resume_id}")
            raise Exception(f"Lock ownership verification failed")

        # Check if lock has expired (if applicable)
        if hasattr(resume, 'is_lock_expired') and resume.is_lock_expired():
            logger.error(f"Lock expired for resume {resume_id} during evaluation")
            _update_resume_status(db, resume_id, "failed", process_id, release_lock=True)
            raise Exception(f"Lock expired for resume {resume_id}")

        logger.info(f"Starting Celery evaluation for resume {resume_id}")

        # Update task progress - Starting text extraction
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 20, 'stage': 'extracting_text', 'resume_id': resume_id}
        )

        # Initialize consolidated evaluator service
        evaluator = ConsolidatedResumeEvaluator(ai_service)

        # Extract text from resume using the evaluator instance
        try:
            resume_text = await evaluator.extract_resume_text(file_path, file_type)
            if not resume_text or not resume_text.strip():
                logger.error(f"Failed to extract text from resume {resume_id} at {file_path}")
                raise ValueError("Resume text extraction failed - empty or no content extracted")

            logger.info(f"Successfully extracted {len(resume_text)} characters from resume {resume_id}")
        except Exception as text_error:
            logger.error(f"Resume text extraction failed for {resume_id}: {text_error}")
            _update_resume_status(db, resume_id, "failed", process_id, release_lock=True)
            raise Exception(f"Could not extract text from resume file: {text_error}")

        # Update task progress - Text extracted, starting AI evaluation
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 40, 'stage': 'ai_evaluation', 'resume_id': resume_id}
        )

        # Get user_id from resume record
        user_id = resume.user_id

        # Evaluate resume using consolidated single-prompt approach
        try:
            evaluation_result = await evaluator.evaluate_resume(
                resume_text, user_id, resume_id, db, target_role, target_seniority
            )
            logger.info(f"AI evaluation completed for resume {resume_id}")
        except Exception as eval_error:
            logger.error(f"Resume evaluation failed for {resume_id}: {eval_error}")
            _update_resume_status(db, resume_id, "failed", process_id, release_lock=True)
            raise Exception(f"AI evaluation failed: {eval_error}")

        # Update task progress - Processing evaluation results
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 80, 'stage': 'processing_results', 'resume_id': resume_id}
        )

        # Extract scores from consolidated result
        overall_score = evaluation_result.get("ai_score", 0)
        ats_compatibility = _convert_ats_score_to_category(
            evaluation_result.get("ats_compatibility", "fair")
        )

        # Create evaluation record
        evaluation = ResumeEvaluation(
            id=f"eval_{resume_id}_{int(datetime.now().timestamp())}",
            resume_id=resume_id,
            overall_score=overall_score,
            ats_compatibility=ats_compatibility,
            improvement_suggestions=evaluation_result.get("improvement_suggestions", []),
            keyword_analysis=evaluation_result.get("keyword_analysis", {}),
            strengths=evaluation_result.get("strengths", []),
            weaknesses=evaluation_result.get("weaknesses", []),
            evaluation_data=evaluation_result,
            created_at=datetime.now(timezone.utc)
        )

        # Save evaluation and update resume status
        try:
            db.add(evaluation)
            resume.evaluation_status = "completed"
            resume.last_evaluated_at = datetime.now(timezone.utc)

            # Release lock if process_id provided
            if process_id and hasattr(resume, 'release_lock'):
                resume.release_lock()

            db.commit()
            logger.info(f"Evaluation saved successfully for resume {resume_id}")
        except Exception as save_error:
            logger.error(f"Failed to save evaluation for {resume_id}: {save_error}")
            db.rollback()
            raise Exception(f"Failed to save evaluation results: {save_error}")

        # Update task progress - Completed
        current_task.update_state(
            state='SUCCESS',
            meta={
                'progress': 100,
                'stage': 'completed',
                'resume_id': resume_id,
                'overall_score': overall_score,
                'ats_compatibility': ats_compatibility
            }
        )

        return {
            'status': 'completed',
            'resume_id': resume_id,
            'overall_score': overall_score,
            'ats_compatibility': ats_compatibility,
            'evaluation_id': evaluation.id
        }

    except Exception as e:
        logger.error(f"Celery task failed for resume {resume_id}: {e}")

        # Update task state to FAILURE with error info
        current_task.update_state(
            state='FAILURE',
            meta={
                'progress': 0,
                'stage': 'failed',
                'resume_id': resume_id,
                'error': str(e)
            }
        )

        # Update resume status in database
        try:
            _update_resume_status(db, resume_id, "failed", process_id, release_lock=True)
        except:
            logger.error(f"Failed to update resume status to failed for {resume_id}")

        # Re-raise for Celery retry mechanism
        raise e

    finally:
        db.close()


@celery_app.task(
    bind=True,
    name='app.tasks.resume_tasks.extract_resume_text_task'
)
def extract_resume_text_task(self, file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Celery task for extracting text from resume files.
    Useful for preprocessing or independent text extraction operations.

    Args:
        file_path: Path to resume file
        file_type: MIME type of file

    Returns:
        Dict containing extracted text and metadata
    """

    current_task.update_state(
        state='PROGRESS',
        meta={'progress': 10, 'stage': 'initializing_extractor'}
    )

    try:
        # Initialize AI service
        ai_service = get_ai_service()
        evaluator = ConsolidatedResumeEvaluator(ai_service)

        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 50, 'stage': 'extracting_text'}
        )

        # Extract text
        resume_text = await evaluator.extract_resume_text(file_path, file_type)

        if not resume_text or not resume_text.strip():
            raise ValueError("Text extraction failed - empty or no content")

        current_task.update_state(
            state='SUCCESS',
            meta={'progress': 100, 'stage': 'completed'}
        )

        return {
            'status': 'completed',
            'text': resume_text,
            'length': len(resume_text),
            'file_path': file_path
        }

    except Exception as e:
        logger.error(f"Text extraction failed for {file_path}: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'file_path': file_path}
        )
        raise e


def _update_resume_status(
    db: SessionLocal,
    resume_id: str,
    status: str,
    process_id: Optional[str] = None,
    release_lock: bool = False
):
    """
    Helper function to update resume status in database.

    Args:
        db: Database session
        resume_id: Resume identifier
        status: New status to set
        process_id: Process identifier for lock verification
        release_lock: Whether to release the lock
    """
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.evaluation_status = status

            if release_lock and hasattr(resume, 'release_lock'):
                resume.release_lock()

            db.commit()
            logger.info(f"Updated resume {resume_id} status to {status}")
    except Exception as e:
        logger.error(f"Failed to update resume {resume_id} status: {e}")
        db.rollback()