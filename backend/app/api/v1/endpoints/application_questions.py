"""
API endpoints for application question answering
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.services.question_answer_service import QuestionAnswerService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def get_current_user_mock(db: Session = Depends(get_db)) -> User:
    """
    Temporary mock for user authentication
    Replace with your actual authentication dependency
    """
    # For now, get the first user in the database
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    return user


class BatchQuestionRequest(BaseModel):
    """Request schema for batch question answering"""
    job_id: str
    questions_text: str  # Questions separated by newlines
    job_description: Optional[str] = None  # Optional job description for better context


class GeneratedAnswer(BaseModel):
    """Response schema for generated answers"""
    question: str
    answer: str
    word_count: int
    char_count: int


class BatchAnswerResponse(BaseModel):
    """Response schema for batch question answering"""
    answers: List[GeneratedAnswer]
    total_generated: int


@router.post("/generate-answers", response_model=BatchAnswerResponse)
async def generate_application_answers(
    request: BatchQuestionRequest,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """Generate answers for batch of questions - STATELESS"""

    try:
        service = QuestionAnswerService(db)

        # Parse questions (split by newline)
        questions = [q.strip() for q in request.questions_text.split('\n') if q.strip()]

        if not questions:
            raise HTTPException(status_code=400, detail="No questions provided")

        if len(questions) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 questions per batch")

        # Generate answers
        results = await service.generate_answers_batch(
            user_id=current_user.user_id,
            job_id=request.job_id,
            questions=questions,
            job_description=request.job_description
        )

        # Log usage for analytics (don't store answers)
        await log_feature_usage(
            user_id=current_user.user_id,
            feature='questions_generated',
            count=len(questions),
            job_id=request.job_id,
            metadata={'question_count': len(questions), 'job_id': request.job_id}
        )

        return BatchAnswerResponse(
            answers=results,
            total_generated=len(results)
        )

    except Exception as e:
        logger.error(f"Error generating application answers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate answers: {str(e)}")


async def log_feature_usage(user_id: str, feature: str, count: int = 1, job_id: str = None, metadata: dict = None):
    """Log feature usage for analytics"""
    try:
        from app.models.analytics import FeatureUsageLog
        from app.db.session import get_db

        # Create a database session (not ideal but works for now)
        db = next(get_db())

        usage_log = FeatureUsageLog(
            user_id=user_id,
            feature_name=feature,
            usage_count=count,
            job_id=job_id,
            usage_metadata=metadata
        )

        db.add(usage_log)
        db.commit()

        logger.info(f"Feature usage logged: user={user_id}, feature={feature}, count={count}")
    except Exception as e:
        logger.error(f"Error logging feature usage: {e}")
        # Still log to console as fallback
        logger.info(f"Feature usage (fallback): user={user_id}, feature={feature}, count={count}")


@router.get("/usage-stats")
async def get_question_generation_stats(
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """Get usage stats for analytics dashboard"""

    try:
        from app.models.analytics import FeatureUsageLog
        from sqlalchemy import func, distinct
        from datetime import datetime, timedelta

        # Get total questions generated
        total_questions = db.query(func.sum(FeatureUsageLog.usage_count)).filter(
            FeatureUsageLog.user_id == current_user.user_id,
            FeatureUsageLog.feature_name == 'questions_generated'
        ).scalar() or 0

        # Get number of unique days used (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        days_used = db.query(func.count(distinct(func.date(FeatureUsageLog.created_at)))).filter(
            FeatureUsageLog.user_id == current_user.user_id,
            FeatureUsageLog.feature_name == 'questions_generated',
            FeatureUsageLog.created_at >= thirty_days_ago
        ).scalar() or 0

        # Get most recent usage
        most_recent = db.query(FeatureUsageLog.created_at).filter(
            FeatureUsageLog.user_id == current_user.user_id,
            FeatureUsageLog.feature_name == 'questions_generated'
        ).order_by(FeatureUsageLog.created_at.desc()).first()

        most_recent_usage = most_recent[0].strftime('%Y-%m-%d') if most_recent else None

        return {
            'total_questions_answered': int(total_questions),
            'days_used': int(days_used),
            'most_recent_usage': most_recent_usage
        }
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        return {
            'total_questions_answered': 0,
            'days_used': 0,
            'most_recent_usage': None
        }