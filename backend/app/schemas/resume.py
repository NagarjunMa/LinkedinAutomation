from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class WordingSuggestion(BaseModel):
    """Schema for wording improvement suggestions"""
    original: str = Field(..., description="Original text that needs improvement")
    suggested: str = Field(..., description="Improved version of the text")
    rationale: str = Field(..., description="Explanation of why the change improves the text")


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


class AtsCompatibilityDetails(BaseModel):
    """Detailed ATS compatibility analysis"""
    status: str = Field(..., description="Excellent/Good/Fair/Poor")
    analysis: str = Field(..., description="2-3 sentences on keyword density and parsing potential")
    missing_keywords: List[str] = Field(..., description="List of important keywords missing from the resume")


class ResumePrecisionAnalysis(BaseModel):
    """Structured output for Precision Analysis Resume Evaluation"""
    ai_score: int = Field(..., description="0-100 score for content quality and impact")
    ats_score: int = Field(..., description="0-100 score for technical parsability")
    executive_summary: str = Field(..., description="2-3 sentence overview of market positioning")
    optical_strengths: List[str] = Field(..., description="3-5 specific visual or branding wins")
    strategic_improvements: List[str] = Field(..., description="3-5 high-level architectural changes")
    wording_suggestions: List[WordingSuggestion] = Field(..., description="List of specific bullet point rewrites")
    ats_compatibility: AtsCompatibilityDetails = Field(..., description="Technical parsing analysis")


class ResumeEvaluationResult(BaseModel):
    """Schema for AI evaluation results - Updated for Precision Analysis"""
    # Precision Analysis Fields (New)
    ai_score: int = Field(..., ge=0, le=100)
    ats_score: int = Field(..., ge=0, le=100)
    optical_strengths: List[str]
    strategic_improvements: List[str]
    
    # Legacy/Mapped Fields (Kept for compatibility/DB mapping)
    overall_score: int = Field(..., ge=0, le=100)
    ats_compliance_score: int = Field(..., ge=0, le=100)
    content_quality_score: int = Field(0, ge=0, le=100)
    experience_points_score: int = Field(0, ge=0, le=100)
    job_relevance_score: int = Field(0, ge=0, le=100)
    quality_checks_score: int = Field(0, ge=0, le=100)
    
    strengths: List[str] = []
    improvements: List[str] = []
    detailed_feedback: str
    
    ats_compatibility: str = Field(..., pattern="^(excellent|good|fair|poor)$")
    ats_compatibility_details: Optional[AtsCompatibilityDetails] = None

    @field_validator('ats_compatibility', mode='before')
    @classmethod
    def validate_ats_compatibility(cls, v):
        """Convert numeric scores to categorical ratings"""
        if isinstance(v, (int, float)):
            # Convert score to categorical rating
            if v >= 8:
                return "excellent"
            elif v >= 6:
                return "good"
            elif v >= 4:
                return "fair"
            else:
                return "poor"
        elif isinstance(v, str):
            # Handle string numbers
            try:
                score = float(v)
                if score >= 8:
                    return "excellent"
                elif score >= 6:
                    return "good"
                elif score >= 4:
                    return "fair"
                else:
                    return "poor"
            except ValueError:
                # If it's already a valid categorical value, keep it
                if v.lower() in ["excellent", "good", "fair", "poor"]:
                    return v.lower()
                # Default fallback
                return "fair"
        return "fair"
    
    keyword_analysis: Dict[str, Any] = Field(..., description="Keyword analysis results")

    # New fields for enhanced evaluation
    wording_suggestions: Optional[List[WordingSuggestion]] = Field(None, description="Structured wording improvement suggestions")
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


# ---------------------------------------------------------------------------
# Phase 1 — ResumeDocumentJSON and associated schemas
# ---------------------------------------------------------------------------
from typing import Literal


class Contact(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    links: List[str] = Field(default_factory=list)


class Bullet(BaseModel):
    id: str
    text: str
    raw_text: str


class ExperienceEntry(BaseModel):
    company: str
    role: str
    dates: Optional[str] = None
    location: Optional[str] = None
    bullets: List[Bullet] = Field(default_factory=list)


class EducationEntry(BaseModel):
    school: str
    degree: Optional[str] = None
    dates: Optional[str] = None
    gpa: Optional[str] = None


class Skills(BaseModel):
    hard: List[str] = Field(default_factory=list)
    soft: List[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str
    bullets: List[Bullet] = Field(default_factory=list)


class ResumeDocumentJSON(BaseModel):
    contact: Contact
    summary: Optional[str] = None
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    projects: List[ProjectEntry] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    raw_text: str


class BulletFlag(BaseModel):
    bullet_id: str
    severity: Literal["critical", "warning", "info"]
    reason: str
    category: Literal["quantification", "verb", "structure", "clarity", "redundancy", "ats"]


class FormatIssue(BaseModel):
    type: str
    location: str
    fix_hint: str


class EvaluationReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    bullet_flags: List[BulletFlag]
    format_issues: List[FormatIssue]
    summary_critique: Optional[str] = None
    skill_gaps: List[str] = Field(default_factory=list)


class Placeholder(BaseModel):
    token: str
    what: str


class RewriteResult(BaseModel):
    rewritten: str
    placeholders: List[Placeholder]
    applied_changes: List[str]
