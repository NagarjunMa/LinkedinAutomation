import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
from app.schemas.resume import (
    ResumeUploadResponse, ResumeListResponse, ResumeDeleteResponse,
    ResumeWithEvaluation, ResumeStorageInfo, ResumeEvaluationRequest
)
from app.services.resume_evaluator import ResumeEvaluatorService
from app.services.agentic_resume_evaluator import AgenticResumeEvaluatorService
from app.core.ai_service import get_ai_service
from app.core.auth import get_authenticated_user_id
from app.models.resume import Resume, ResumeEvaluation
from app.models.agent_models import ResumeEvaluationSession, ResumeAgentResult
from app.models.user import User
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

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
        evaluator = AgenticResumeEvaluatorService(ai_service)
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
        evaluator = AgenticResumeEvaluatorService(ai_service)
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
        evaluator = AgenticResumeEvaluatorService(ai_service)
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
        # First try to get detailed evaluation from ResumeEvaluationSession (agentic results)
        evaluation_session = db.query(ResumeEvaluationSession).filter(
            ResumeEvaluationSession.resume_id == resume_id
        ).order_by(ResumeEvaluationSession.created_at.desc()).first()

        if evaluation_session and evaluation_session.evaluation_data:
            # Use detailed agentic evaluation data
            eval_data = evaluation_session.evaluation_data
            evaluation = {
                "overall_score": evaluation_session.overall_score or eval_data.get('overall_score', 0),
                "ats_compliance_score": eval_data.get('ats_compliance_score', 0),
                "content_quality_score": eval_data.get('content_quality_score', 0),
                "experience_points_score": eval_data.get('experience_points_score', 0),
                "job_relevance_score": eval_data.get('job_relevance_score', 0),
                "quality_checks_score": eval_data.get('quality_checks_score', 0),
                "strengths": eval_data.get('strengths', []),
                "improvements": eval_data.get('improvements', []),
                "detailed_feedback": eval_data.get('detailed_feedback', ''),
                "ats_compatibility": eval_data.get('ats_compatibility', 'fair'),
                "keyword_analysis": eval_data.get('keyword_analysis', {}),
                "evaluated_at": evaluation_session.created_at,
                "ai_model_version": eval_data.get('ai_model_version', ''),
                "processing_time": evaluation_session.processing_time_seconds,
                # Add detailed agent results
                "agent_results": eval_data.get('agent_results', {}),
                "critical_issues": eval_data.get('critical_issues', {}),
                "market_positioning": eval_data.get('market_positioning', {}),
                "evaluation_metadata": {
                    "processing_time_seconds": evaluation_session.processing_time_seconds,
                    "successful_agents": evaluation_session.successful_agents,
                    "total_agents": evaluation_session.total_agents,
                    "confidence_percentage": evaluation_session.confidence_percentage,
                    "evaluation_type": 'agentic'
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
        # Delete agent results first (they reference evaluation sessions)
        db.query(ResumeAgentResult).filter(
            ResumeAgentResult.evaluation_id.in_(
                db.query(ResumeEvaluationSession.id).filter(
                    ResumeEvaluationSession.resume_id == resume_id
                )
            )
        ).delete(synchronize_session=False)
        
        # Delete evaluation sessions
        db.query(ResumeEvaluationSession).filter(
            ResumeEvaluationSession.resume_id == resume_id
        ).delete()
        
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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    ai_service = Depends(get_ai_service),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Manually trigger resume evaluation with status locking"""

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

        # Start evaluation in background
        background_tasks.add_task(
            evaluate_resume_background,
            resume_id,
            resume.file_path,
            resume.file_type,
            evaluation_request.target_role,
            evaluation_request.target_seniority,
            process_id
        )

        return {
            "message": "Resume evaluation started",
            "process_id": process_id,
            "status": "evaluating"
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
    """Background task for resume evaluation using agentic workflow with proper locking"""

    # Create new database session for background task
    db = next(get_db())
    ai_service = get_ai_service()

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

        # Initialize agentic evaluator service
        evaluator = AgenticResumeEvaluatorService(ai_service)

        # Extract text from resume
        resume_text = await evaluator.extract_resume_text(file_path, file_type)

        # Get user_id from resume record
        user_id = resume.user_id

        # Evaluate resume using agentic workflow
        evaluation_result = await evaluator.evaluate_resume(
            resume_text, user_id, resume_id, target_role, target_seniority
        )

        # Save evaluation to database (legacy format for compatibility)
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
            evaluation_prompt="Agentic multi-agent evaluation workflow"  # Store the evaluation type
        )

        db.add(evaluation_record)

        # Update resume status and release lock atomically
        resume.update_evaluation_status("completed", release_lock=True)
        resume.ai_model_version = evaluation_result.ai_model_version
        resume.processing_time = evaluation_result.processing_time

        db.commit()

        logger.info(f"Agentic resume evaluation completed for {resume_id} with score {evaluation_result.overall_score} by process {process_id}")

    except Exception as e:
        logger.error(f"Background evaluation failed for resume {resume_id}: {e}")
        db.rollback()

        try:
            # Get fresh resume record and mark as failed, release lock
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if resume and resume.locked_by == process_id:
                resume.update_evaluation_status("failed", release_lock=True)
                db.commit()
                logger.info(f"Marked resume {resume_id} as failed and released lock")

        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup after evaluation error for resume {resume_id}: {cleanup_error}")
            db.rollback()

    finally:
        db.close()
