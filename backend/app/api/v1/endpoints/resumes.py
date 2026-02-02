import os
import uuid
import shutil
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from celery.result import AsyncResult
from app.db.session import get_db, SessionLocal
from app.schemas.resume import (
    ResumeUploadResponse, ResumeListResponse, ResumeDeleteResponse,
    ResumeWithEvaluation, ResumeStorageInfo, ResumeEvaluationRequest
)

from app.services.consolidated_resume_evaluator import ConsolidatedResumeEvaluator
from app.core.ai_service import get_ai_service
from app.core.auth import get_authenticated_user_id
from app.core.rate_limiter import check_ai_rate_limit
from app.models.resume import Resume, ResumeEvaluation
from app.models.user import User
from app.core.config import settings
from app.tasks.resume_tasks import evaluate_resume_task
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


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

# Configure resume storage
RESUME_UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "resumes")
os.makedirs(RESUME_UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx'}
MAX_RESUMES_PER_USER = 5


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_role: str = Form(None),
    target_seniority: str = Form(None),
    db: Session = Depends(get_db),
    ai_service = Depends(get_ai_service),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Upload a resume file for AI evaluation"""
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Check storage limit
    current_count = db.query(Resume).filter(Resume.user_id == user_id).count()
    if current_count >= MAX_RESUMES_PER_USER:
        raise HTTPException(
            status_code=400, 
            detail=f"Storage limit reached. Maximum {MAX_RESUMES_PER_USER} resumes allowed."
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        file_path = os.path.join(RESUME_UPLOAD_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create resume record
        resume = Resume(
            id=file_id,
            user_id=user_id,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            file_type=file.content_type or file_ext,
            evaluation_status="pending"
        )
        
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        return ResumeUploadResponse(
            id=resume.id,
            filename=resume.filename,
            original_filename=resume.original_filename,
            file_size=resume.file_size,
            file_type=resume.file_type,
            uploaded_at=resume.uploaded_at,
            evaluation_status=resume.evaluation_status,
            message="Resume uploaded successfully. Ready for evaluation."
        )
        
    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        # Clean up file if it was created
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Failed to upload resume")


@router.get("/list", response_model=ResumeListResponse)
async def list_resumes(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """List all resumes for the current user"""
    
    resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    
    resume_list = []
    total_size = 0
    
    for resume in resumes:
        resume_list.append({
            "id": resume.id,
            "filename": resume.filename,
            "original_filename": resume.original_filename,
            "file_size": resume.file_size,
            "file_type": resume.file_type,
            "uploaded_at": resume.uploaded_at,
            "evaluation_status": resume.evaluation_status,
            "evaluated_at": resume.evaluated_at
        })
        total_size += resume.file_size
    
    return ResumeListResponse(
        resumes=resume_list,
        total_count=len(resumes),
        storage_used=total_size,
        storage_limit=MAX_RESUMES_PER_USER
    )


@router.get("/storage-info", response_model=ResumeStorageInfo)
async def get_storage_info(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get storage information for the current user"""
    
    resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    
    total_count = len(resumes)
    storage_used_mb = sum(r.file_size for r in resumes) / (1024 * 1024)
    storage_limit_mb = 50.0  # 50MB total limit
    remaining_slots = MAX_RESUMES_PER_USER - total_count
    remaining_storage_mb = storage_limit_mb - storage_used_mb
    
    return ResumeStorageInfo(
        total_count=total_count,
        storage_used_mb=round(storage_used_mb, 2),
        storage_limit_mb=storage_limit_mb,
        remaining_slots=remaining_slots,
        remaining_storage_mb=round(remaining_storage_mb, 2)
    )


@router.get("/agent-metrics")
async def get_agent_metrics(
    ai_service = Depends(get_ai_service)
):
    """Get performance metrics for all evaluation agents"""
    try:
        evaluator = ConsolidatedResumeEvaluator(ai_service)
        metrics = await evaluator.get_agent_performance_metrics()
        return {"agent_metrics": metrics}
    except Exception as e:
        logger.error(f"Failed to get agent metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent metrics")


@router.get("/evaluation-history")
async def get_evaluation_history(
    limit: int = 10,
    ai_service = Depends(get_ai_service),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get evaluation history for the current user"""
    try:
        evaluator = ConsolidatedResumeEvaluator(ai_service)
        history = await evaluator.get_evaluation_history(user_id, limit)
        return {"evaluation_history": history}
    except Exception as e:
        logger.error(f"Failed to get evaluation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get evaluation history")


@router.get("/agent-status")
async def get_agent_status(
    ai_service = Depends(get_ai_service)
):
    """Get status and capabilities of all evaluation agents"""
    try:
        evaluator = ConsolidatedResumeEvaluator(ai_service)
        status = evaluator.orchestrator.get_agent_status()
        return {"agent_status": status}
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent status")


@router.get("/{resume_id}/evaluation-progress")
async def get_evaluation_progress(
    resume_id: str,
    db: Session = Depends(get_db),
    ai_service = Depends(get_ai_service)
):
    """Get real-time evaluation progress for a resume."""
    try:
        # Get the resume to verify it exists
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Get progress from shared orchestrator
        from app.services.orchestrator_manager import orchestrator_manager
        orchestrator = orchestrator_manager.get_orchestrator(ai_service)
        progress = orchestrator.get_evaluation_progress(resume_id)

        return {
            "resume_id": resume_id,
            "evaluation_status": resume.evaluation_status,
            "progress": progress
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get evaluation progress for resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get evaluation progress")


@router.get("/{resume_id}", response_model=ResumeWithEvaluation)
async def get_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get resume details and evaluation results"""
    
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Get evaluation if completed
    evaluation = None
    if resume.evaluation_status == "completed":
        # Get consolidated evaluation from ResumeEvaluation table
        resume_evaluation = db.query(ResumeEvaluation).filter(
            ResumeEvaluation.resume_id == resume_id
        ).order_by(ResumeEvaluation.evaluated_at.desc()).first()

        if resume_evaluation:
            # Use consolidated evaluation data
            evaluation = {
                "overall_score": resume_evaluation.overall_score,
                "ats_compliance_score": resume_evaluation.ats_compliance_score,
                
                # Use aliases/mapping for new frontend schema
                "ai_score": resume_evaluation.overall_score,
                "ats_score": resume_evaluation.ats_compliance_score,
                "optical_strengths": resume_evaluation.strengths or [],
                "strategic_improvements": resume_evaluation.improvements or [],
                
                "content_quality_score": resume_evaluation.content_quality_score,
                "experience_points_score": resume_evaluation.experience_points_score,
                "job_relevance_score": resume_evaluation.job_relevance_score,
                "quality_checks_score": resume_evaluation.quality_checks_score,
                "strengths": resume_evaluation.strengths or [],
                "improvements": resume_evaluation.improvements or [],
                "detailed_feedback": resume_evaluation.detailed_feedback or '',
                "ats_compatibility": resume_evaluation.ats_compatibility or 'fair',
                
                # Parse detail object if stored in keyword_analysis
                "ats_compatibility_details": {
                    "status": resume_evaluation.ats_compatibility or 'fair',
                    "analysis": resume_evaluation.keyword_analysis.get("analysis", "") if resume_evaluation.keyword_analysis else "",
                    "missing_keywords": resume_evaluation.keyword_analysis.get("missing_keywords", []) if resume_evaluation.keyword_analysis else []
                },
                
                "keyword_analysis": resume_evaluation.keyword_analysis or {},
                "evaluated_at": resume_evaluation.evaluated_at,
                "ai_model_version": resume_evaluation.ai_model_version or '',
                "critical_issues": resume_evaluation.critical_issues or {},
                "market_positioning": resume_evaluation.market_positioning or {},
                "wording_suggestions": resume_evaluation.wording_suggestions or [],
                "evaluation_metadata": {
                    "evaluation_type": 'consolidated'
                }
            }
        else:
            # Fallback to legacy ResumeEvaluation table
            evaluation_record = db.query(ResumeEvaluation).filter(
                ResumeEvaluation.resume_id == resume_id
            ).first()

            if evaluation_record:
                evaluation = {
                    "overall_score": evaluation_record.overall_score,
                    "ats_compliance_score": evaluation_record.ats_compliance_score,
                    "content_quality_score": evaluation_record.content_quality_score,
                    "experience_points_score": evaluation_record.experience_points_score,
                    "job_relevance_score": evaluation_record.job_relevance_score,
                    "quality_checks_score": evaluation_record.quality_checks_score,
                    "strengths": evaluation_record.strengths or [],
                    "improvements": evaluation_record.improvements or [],
                    "detailed_feedback": evaluation_record.detailed_feedback or "",
                    "ats_compatibility": evaluation_record.ats_compatibility,
                    "keyword_analysis": evaluation_record.keyword_analysis or {},
                    "evaluated_at": evaluation_record.evaluated_at,
                    "ai_model_version": evaluation_record.ai_model_version,
                    "processing_time": resume.processing_time,
                    "wording_suggestions": getattr(evaluation_record, 'wording_suggestions', None) or [],
                    "evaluation_metadata": {
                        "evaluation_type": 'legacy'
                    }
                }
    
    return ResumeWithEvaluation(
        resume={
            "id": resume.id,
            "filename": resume.filename,
            "original_filename": resume.original_filename,
            "file_size": resume.file_size,
            "file_type": resume.file_type,
            "uploaded_at": resume.uploaded_at,
            "evaluation_status": resume.evaluation_status,
            "evaluated_at": resume.evaluated_at
        },
        evaluation=evaluation
    )


@router.delete("/{resume_id}", response_model=ResumeDeleteResponse)
async def delete_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Delete a resume and its evaluation results"""
    
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    try:
        # Delete evaluation records
        db.query(ResumeEvaluation).filter(
            ResumeEvaluation.resume_id == resume_id
        ).delete()

        # Delete resume record
        db.delete(resume)
        db.commit()
        
        # Delete file from storage
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
        
        return ResumeDeleteResponse(
            message="Resume deleted successfully",
            deleted_resume_id=resume_id
        )
        
    except Exception as e:
        logger.error(f"Resume deletion failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete resume")


@router.post("/{resume_id}/evaluate")
async def evaluate_resume(
    resume_id: str,
    evaluation_request: ResumeEvaluationRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Trigger resume evaluation using optimized Celery background task"""

    # Check rate limit for resume evaluation
    check_ai_rate_limit(user_id, "resume_evaluation")

    # Generate unique process identifier for this evaluation
    process_id = f"eval_{uuid.uuid4().hex[:8]}"

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Check if resume can be evaluated (not locked or lock expired)
    if not resume.can_evaluate():
        raise HTTPException(
            status_code=409,
            detail=f"Resume is currently being evaluated by another process. Locked by: {resume.locked_by}"
        )

    try:
        # Acquire lock for evaluation process
        if not resume.acquire_lock(process_id, lock_duration_minutes=15):
            raise HTTPException(
                status_code=409,
                detail="Failed to acquire evaluation lock. Another process may be evaluating this resume."
            )

        # Update status to evaluating (lock prevents race conditions)
        resume.update_evaluation_status("evaluating", release_lock=False)
        db.commit()

        logger.info(f"Evaluation lock acquired for resume {resume_id} by process {process_id}")

        # Start evaluation with Celery background task
        task = evaluate_resume_task.delay(
            resume_id,
            resume.file_path,
            resume.file_type,
            evaluation_request.target_role,
            evaluation_request.target_seniority,
            process_id
        )

        logger.info(f"Started Celery task {task.id} for resume {resume_id}")

        return {
            "message": "Resume evaluation started",
            "task_id": task.id,
            "process_id": process_id,
            "status": "evaluating",
            "status_endpoint": f"/api/v1/resumes/{resume_id}/evaluation-status"
        }

    except IntegrityError as e:
        logger.error(f"Database integrity error during evaluation start: {e}")
        db.rollback()
        # Try to release lock if it was acquired
        try:
            resume.release_lock()
            db.commit()
        except:
            pass
        raise HTTPException(status_code=409, detail="Resume evaluation already in progress")

    except Exception as e:
        logger.error(f"Failed to start evaluation: {e}")
        db.rollback()
        # Release lock and mark as failed
        try:
            resume.update_evaluation_status("failed", release_lock=True)
            db.commit()
        except:
            pass
        raise HTTPException(status_code=500, detail="Failed to start evaluation")


@router.get("/{resume_id}/evaluation-status")
async def get_evaluation_status(
    resume_id: str,
    task_id: str = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get the status of a resume evaluation task"""

    # Verify resume belongs to user
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # If task_id provided, check Celery task status
    if task_id:
        try:
            result = AsyncResult(task_id)

            if result.state == 'PENDING':
                response = {
                    'status': 'pending',
                    'progress': 0,
                    'stage': 'queued',
                    'message': 'Task is waiting to be processed'
                }
            elif result.state == 'PROGRESS':
                response = {
                    'status': 'in_progress',
                    'progress': result.info.get('progress', 0),
                    'stage': result.info.get('stage', 'processing'),
                    'message': f"Currently {result.info.get('stage', 'processing')}"
                }
            elif result.state == 'SUCCESS':
                response = {
                    'status': 'completed',
                    'progress': 100,
                    'stage': 'completed',
                    'message': 'Evaluation completed successfully',
                    'result': result.result
                }
            elif result.state == 'FAILURE':
                response = {
                    'status': 'failed',
                    'progress': 0,
                    'stage': 'failed',
                    'message': 'Evaluation failed',
                    'error': str(result.info)
                }
            else:
                response = {
                    'status': result.state.lower(),
                    'progress': result.info.get('progress', 0) if result.info else 0,
                    'stage': result.info.get('stage', 'unknown') if result.info else 'unknown',
                    'message': f"Task state: {result.state}"
                }

        except Exception as e:
            logger.error(f"Error checking task status {task_id}: {e}")
            response = {
                'status': 'error',
                'progress': 0,
                'stage': 'error',
                'message': 'Unable to check task status'
            }
    else:
        # Fallback to resume status from database
        response = {
            'status': resume.evaluation_status or 'unknown',
            'progress': 100 if resume.evaluation_status == 'completed' else 0,
            'stage': resume.evaluation_status or 'unknown',
            'message': f"Resume evaluation status: {resume.evaluation_status or 'unknown'}"
        }

    return response


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Download a resume file"""
    
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="Resume file not found")
    
    return FileResponse(
        resume.file_path,
        filename=resume.original_filename,
        media_type=resume.file_type
    )


async def evaluate_resume_background(
    resume_id: str,
    file_path: str,
    file_type: str,
    target_role: str,
    target_seniority: str,
    process_id: str
):
    """
    Background task for resume evaluation using consolidated evaluator.

    FIXED ISSUES:
    - Single ConsolidatedResumeEvaluator instance (was creating duplicate instances)
    - Proper extract_resume_text method call on correct instance
    - Comprehensive error handling with transparent user messaging
    - No mock data fallbacks - clear failure communication
    - Structured logging for production debugging

    Args:
        resume_id: Unique resume identifier
        file_path: Path to resume file for text extraction
        file_type: MIME type of resume file
        target_role: Optional target role for evaluation context
        target_seniority: Optional target seniority for evaluation context
        process_id: Unique process identifier for lock management
    """

    # Create new database session for background task
    db = SessionLocal()

    # Initialize AI service for background task
    try:
        ai_service = get_ai_service()
    except Exception as ai_init_error:
        logger.error(f"Failed to initialize AI service for resume {resume_id}: {ai_init_error}")
        # Mark resume as failed immediately if AI service can't be initialized
        try:
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if resume and resume.locked_by == process_id:
                resume.update_evaluation_status("failed", release_lock=True)
                db.commit()
        except:
            pass
        finally:
            db.close()
        return

    try:
        # Get resume record with current lock info
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            logger.error(f"Resume {resume_id} not found during background evaluation")
            return

        # Verify this process owns the lock
        if resume.locked_by != process_id:
            logger.error(f"Process {process_id} does not own lock for resume {resume_id}. Current lock owner: {resume.locked_by}")
            return

        # Check if lock has expired
        if resume.is_lock_expired():
            logger.error(f"Lock expired for resume {resume_id} during evaluation")
            resume.update_evaluation_status("failed", release_lock=True)
            db.commit()
            return

        logger.info(f"Starting background evaluation for resume {resume_id} by process {process_id}")

        # Use new consolidated evaluator (single AI call instead of 12 agents)
        use_consolidated = True  # Feature flag for gradual rollout

        if use_consolidated:
            # Initialize single consolidated evaluator service
            evaluator = ConsolidatedResumeEvaluator(ai_service)

            # Extract text from resume using the evaluator instance
            try:
                resume_text = await evaluator.extract_resume_text(file_path, file_type)
                if not resume_text or not resume_text.strip():
                    logger.error(f"Failed to extract text from resume {resume_id} at {file_path}")
                    raise ValueError("Resume text extraction failed - empty or no content extracted")
            except Exception as text_error:
                logger.error(f"Resume text extraction failed for {resume_id}: {text_error}")
                raise RuntimeError(f"Could not extract text from resume file. Please ensure the file is not corrupted and try uploading again.") from text_error

            # Get user_id from resume record
            user_id = resume.user_id

            # Evaluate resume using consolidated single-prompt approach
            try:
                evaluation_result = await evaluator.evaluate_resume(
                    resume_text, user_id, resume_id, db, target_role, target_seniority
                )
            except Exception as eval_error:
                logger.error(f"Resume evaluation failed for {resume_id}: {eval_error}")
                raise RuntimeError(f"AI evaluation failed. Please try again or contact support if the issue persists.") from eval_error

            # Extract scores from consolidated result
            overall_score = evaluation_result.get("ai_score", 0)
            ats_score = evaluation_result.get("ats_score", 0)
            
            # Extract ATS details
            ats_data = evaluation_result.get("ats_compatibility", {})
            ats_status = ats_data.get("status", "fair") if isinstance(ats_data, dict) else "fair"
            
            # Map consolidated scores to legacy format for compatibility
            evaluation_record = ResumeEvaluation(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                overall_score=overall_score,
                ats_compliance_score=ats_score,
                
                # Zero out separate category scores as they are removed in Precision Analysis
                content_quality_score=overall_score, # Mirror overall score
                experience_points_score=overall_score, 
                job_relevance_score=overall_score,
                quality_checks_score=overall_score,
                
                # Map lists
                strengths=evaluation_result.get("optical_strengths", []),
                improvements=evaluation_result.get("strategic_improvements", []),
                
                detailed_feedback=evaluation_result.get("executive_summary", ""),
                
                ats_compatibility=ats_status.lower(),
                
                # Store complex objects
                keyword_analysis={
                    "missing_keywords": ats_data.get("missing_keywords", []) if isinstance(ats_data, dict) else [],
                    "analysis": ats_data.get("analysis", "") if isinstance(ats_data, dict) else ""
                },
                
                critical_issues={}, # Deprecated in new model but kept for schema
                market_positioning={}, 
                
                wording_suggestions=evaluation_result.get("wording_suggestions", []),
                
                evaluated_at=datetime.now(timezone.utc),
                ai_model_version="gpt-4o-structured-precision",
                evaluation_prompt="Precision Analysis"
            )
        else:
            # Fallback to old agentic evaluator with proper error handling
            evaluator = ConsolidatedResumeEvaluator(ai_service)

            try:
                resume_text = await evaluator.extract_resume_text(file_path, file_type)
                if not resume_text or not resume_text.strip():
                    logger.error(f"Failed to extract text from resume {resume_id} at {file_path}")
                    raise ValueError("Resume text extraction failed - empty or no content extracted")
            except Exception as text_error:
                logger.error(f"Resume text extraction failed for {resume_id}: {text_error}")
                raise RuntimeError(f"Could not extract text from resume file. Please ensure the file is not corrupted and try uploading again.") from text_error

            user_id = resume.user_id

            try:
                evaluation_result = await evaluator.evaluate_resume(
                    resume_text, user_id, resume_id, db, target_role, target_seniority
                )
            except Exception as eval_error:
                logger.error(f"Resume evaluation failed for {resume_id}: {eval_error}")
                raise RuntimeError(f"AI evaluation failed. Please try again or contact support if the issue persists.") from eval_error

            evaluation_record = ResumeEvaluation(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                overall_score=evaluation_result.overall_score,
                ats_compliance_score=evaluation_result.ats_compliance_score,
                content_quality_score=evaluation_result.content_quality_score,
                experience_points_score=evaluation_result.experience_points_score,
                job_relevance_score=evaluation_result.job_relevance_score,
                quality_checks_score=evaluation_result.quality_checks_score,
                strengths=evaluation_result.strengths,
                improvements=evaluation_result.improvements,
                detailed_feedback=evaluation_result.detailed_feedback,
                ats_compatibility=evaluation_result.ats_compatibility,
                keyword_analysis=evaluation_result.keyword_analysis,
                critical_issues=evaluation_result.critical_issues,
                market_positioning=evaluation_result.market_positioning,
                evaluated_at=evaluation_result.evaluated_at,
                ai_model_version=evaluation_result.ai_model_version,
                evaluation_prompt="Agentic multi-agent evaluation workflow"
            )

        db.add(evaluation_record)

        # Update resume status and release lock atomically
        resume.update_evaluation_status("completed", release_lock=True)

        if use_consolidated:
            resume.ai_model_version = "gpt-4o-mini-consolidated"
            resume.processing_time = evaluation_result.get("processing_time_seconds", 0)
        else:
            resume.ai_model_version = evaluation_result.ai_model_version
            resume.processing_time = evaluation_result.processing_time

        db.commit()

        final_score = overall_score if use_consolidated else evaluation_result.overall_score
        logger.info(f"Resume evaluation completed for {resume_id} with score {final_score} by process {process_id} using {'consolidated' if use_consolidated else 'agentic'} evaluator")

    except Exception as e:
        error_message = str(e)
        error_type = type(e).__name__
        logger.error(
            f"Background evaluation failed for resume {resume_id}: {error_message}",
            extra={
                "resume_id": resume_id,
                "process_id": process_id,
                "error_type": error_type,
                "file_path": file_path,
                "file_type": file_type
            }
        )
        db.rollback()

        try:
            # Get fresh resume record and mark as failed with specific error details
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if resume and resume.locked_by == process_id:
                # Provide transparent error messaging based on error type
                if "text extraction failed" in error_message.lower():
                    failure_reason = "Failed to extract text from resume file. Please ensure the file is not corrupted and try uploading a new version."
                elif "ai evaluation failed" in error_message.lower():
                    failure_reason = "AI evaluation service encountered an error. Please try again in a few minutes."
                elif "connection" in error_message.lower() or "timeout" in error_message.lower():
                    failure_reason = "Network connectivity issue during evaluation. Please try again."
                elif "rate limit" in error_message.lower():
                    failure_reason = "AI service rate limit exceeded. Please wait a few minutes before trying again."
                else:
                    failure_reason = f"Evaluation failed: {error_message[:100]}{'...' if len(error_message) > 100 else ''}"

                # Update status to failed and release lock
                resume.update_evaluation_status("failed", release_lock=True)
                # TODO: Consider adding failure_reason field to Resume model for better user feedback

                db.commit()
                logger.info(
                    f"Marked resume {resume_id} as failed with reason: {failure_reason}",
                    extra={"process_id": process_id}
                )

        except Exception as cleanup_error:
            logger.error(
                f"Failed to cleanup after evaluation error for resume {resume_id}: {cleanup_error}",
                extra={"process_id": process_id, "original_error": error_message}
            )
            db.rollback()

    finally:
        db.close()
