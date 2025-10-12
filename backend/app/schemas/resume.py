from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ResumeUploadRequest(BaseModel):
    """Request schema for resume upload"""
    pass  # File will be sent as multipart/form-data


class ResumeUploadResponse(BaseModel):
    """Response schema for resume upload"""
    id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    uploaded_at: datetime
    evaluation_status: str
    message: str


class ResumeEvaluationRequest(BaseModel):
    """Request schema for resume evaluation"""
    resume_id: Optional[str] = None  # Optional since it's provided in URL path
    target_role: Optional[str] = None
    target_seniority: Optional[str] = None


class ResumeEvaluationResult(BaseModel):
    """Schema for AI evaluation results"""
    overall_score: int = Field(..., ge=0, le=100)
    ats_compliance_score: int = Field(..., ge=0, le=100)
    content_quality_score: int = Field(..., ge=0, le=100)
    experience_points_score: int = Field(..., ge=0, le=100)
    job_relevance_score: int = Field(..., ge=0, le=100)
    quality_checks_score: int = Field(..., ge=0, le=100)
    
    strengths: List[str]
    improvements: List[str]
    detailed_feedback: str
    
    ats_compatibility: str = Field(..., pattern="^(excellent|good|fair|poor)$")
    
    keyword_analysis: Dict[str, Any] = Field(..., description="Keyword analysis results")
    
    # New fields for enhanced evaluation
    critical_issues: Optional[Dict[str, List[str]]] = Field(None, description="Critical issues breakdown")
    market_positioning: Optional[Dict[str, Any]] = Field(None, description="Market positioning analysis")
    
    # Metadata
    evaluated_at: datetime
    ai_model_version: Optional[str] = None
    processing_time: Optional[int] = None


class ResumeInfo(BaseModel):
    """Basic resume information"""
    id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    uploaded_at: datetime
    evaluation_status: str
    evaluated_at: Optional[datetime] = None


class ResumeWithEvaluation(BaseModel):
    """Resume with full evaluation results"""
    resume: ResumeInfo
    evaluation: Optional[ResumeEvaluationResult] = None


class ResumeListResponse(BaseModel):
    """Response schema for listing resumes"""
    resumes: List[ResumeInfo]
    total_count: int
    storage_used: int
    storage_limit: int = 5


class ResumeDeleteResponse(BaseModel):
    """Response schema for resume deletion"""
    message: str
    deleted_resume_id: str


class ResumeStorageInfo(BaseModel):
    """Storage information for user's resumes"""
    total_count: int
    storage_used_mb: float
    storage_limit_mb: float = 50.0  # 50MB total limit
    remaining_slots: int
    remaining_storage_mb: float


class AIEvaluationPrompt(BaseModel):
    """Schema for AI evaluation prompt customization"""
    target_role: Optional[str] = None
    target_seniority: Optional[str] = None
    experience_level: Optional[str] = None  # fresher, mid-level, senior
    focus_areas: Optional[List[str]] = None  # specific areas to focus on
    custom_instructions: Optional[str] = None


class ResumeEvaluationStatus(BaseModel):
    """Status update for resume evaluation"""
    resume_id: str
    status: str  # pending, evaluating, completed, failed
    progress: Optional[int] = Field(None, ge=0, le=100)
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
