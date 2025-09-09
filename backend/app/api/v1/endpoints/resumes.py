import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.resume import (
    ResumeUploadResponse, ResumeListResponse, ResumeDeleteResponse,
    ResumeWithEvaluation, ResumeStorageInfo, ResumeEvaluationRequest
)
from app.services.resume_evaluator import ResumeEvaluatorService
from app.core.ai_service import get_ai_service
from app.models.resume import Resume, ResumeEvaluation
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
    target_industry: str = Form(None),
    db: Session = Depends(get_db),
    ai_service = Depends(get_ai_service)
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
    
    # TODO: Get actual user_id from authentication
    user_id = "demo_user"  # Replace with actual user authentication
    
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
        
        # Start background evaluation
        background_tasks.add_task(
            evaluate_resume_background,
            file_id,
            file_path,
            file.content_type or file_ext,
            target_role,
            target_industry,
            db,
            ai_service
        )
        
        return ResumeUploadResponse(
            id=resume.id,
            filename=resume.filename,
            original_filename=resume.original_filename,
            file_size=resume.file_size,
            file_type=resume.file_type,
            uploaded_at=resume.uploaded_at,
            evaluation_status=resume.evaluation_status,
            message="Resume uploaded successfully. AI evaluation started."
        )
        
    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        # Clean up file if it was created
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Failed to upload resume")


@router.get("/list", response_model=ResumeListResponse)
async def list_resumes(
    db: Session = Depends(get_db)
):
    """List all resumes for the current user"""
    
    # TODO: Get actual user_id from authentication
    user_id = "demo_user"  # Replace with actual user authentication
    
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
    db: Session = Depends(get_db)
):
    """Get storage information for the current user"""
    
    # TODO: Get actual user_id from authentication
    user_id = "demo_user"  # Replace with actual user authentication
    
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


@router.get("/{resume_id}", response_model=ResumeWithEvaluation)
async def get_resume(
    resume_id: str,
    db: Session = Depends(get_db)
):
    """Get resume details and evaluation results"""
    
    # TODO: Get actual user_id from authentication
    user_id = "demo_user"  # Replace with actual user authentication
    
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Get evaluation if completed
    evaluation = None
    if resume.evaluation_status == "completed":
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
                "processing_time": resume.processing_time
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
    db: Session = Depends(get_db)
):
    """Delete a resume and its evaluation results"""
    
    # TODO: Get actual user_id from authentication
    user_id = "demo_user"  # Replace with actual user authentication
    
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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    ai_service = Depends(get_ai_service)
):
    """Manually trigger resume evaluation"""
    
    # TODO: Get actual user_id from authentication
    user_id = "demo_user"  # Replace with actual user authentication
    
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.evaluation_status == "evaluating":
        raise HTTPException(status_code=400, detail="Resume is already being evaluated")
    
    try:
        # Update status to evaluating
        resume.evaluation_status = "evaluating"
        db.commit()
        
        # Start evaluation in background
        background_tasks.add_task(
            evaluate_resume_background,
            resume_id,
            resume.file_path,
            resume.file_type,
            evaluation_request.target_role,
            evaluation_request.target_industry,
            db,
            ai_service
        )
        
        return {"message": "Resume evaluation started"}
        
    except Exception as e:
        logger.error(f"Failed to start evaluation: {e}")
        resume.evaluation_status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to start evaluation")


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    db: Session = Depends(get_db)
):
    """Download a resume file"""
    
    # TODO: Get actual user_id from authentication
    user_id = "demo_user"  # Replace with actual user authentication
    
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
    target_industry: str,
    db: Session,
    ai_service
):
    """Background task for resume evaluation"""
    
    try:
        # Update status to evaluating
        db.query(Resume).filter(Resume.id == resume_id).update({
            "evaluation_status": "evaluating"
        })
        db.commit()
        
        # Initialize evaluator service
        evaluator = ResumeEvaluatorService(ai_service)
        
        # Extract text from resume
        resume_text = await evaluator.extract_resume_text(file_path, file_type)
        
        # Evaluate resume
        evaluation_result = await evaluator.evaluate_resume(
            resume_text, target_role, target_industry
        )
        
        # Save evaluation to database
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
            evaluation_prompt="Senior hiring manager evaluation prompt"  # Store the prompt used
        )
        
        db.add(evaluation_record)
        
        # Update resume status
        db.query(Resume).filter(Resume.id == resume_id).update({
            "evaluation_status": "completed",
            "evaluated_at": evaluation_result.evaluated_at,
            "ai_model_version": evaluation_result.ai_model_version,
            "processing_time": evaluation_result.processing_time
        })
        
        db.commit()
        
        logger.info(f"Resume {resume_id} evaluated successfully with score {evaluation_result.overall_score}")
        
    except Exception as e:
        logger.error(f"Resume evaluation failed for {resume_id}: {e}")
        
        # Update status to failed
        db.query(Resume).filter(Resume.id == resume_id).update({
            "evaluation_status": "failed"
        })
        db.commit()
        
        # Re-raise to ensure the error is logged
        raise
