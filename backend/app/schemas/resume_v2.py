"""Phase 1 resume schemas — canonical structured resume representation.

New code should import from here. The legacy endpoint (resumes.py) still imports
from resume_legacy.py. The compat shim (resume.py) re-exports both.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


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
    location: Optional[str] = None
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


class ScoreBreakdown(BaseModel):
    content_quality: int = Field(ge=0, le=100)
    role_fit: int = Field(ge=0, le=100)
    evidence_strength: int = Field(ge=0, le=100)
    recruiter_readability: int = Field(ge=0, le=100)


class ScoreExplanation(BaseModel):
    category: Literal[
        "content_quality",
        "role_fit",
        "evidence_strength",
        "recruiter_readability",
    ]
    score: int = Field(ge=0, le=100)
    reason: str
    evidence: List[str] = Field(default_factory=list)
    before_applying_action: str


class EvaluationReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    readiness_label: Literal["ready", "minor_edits", "needs_work"]
    score_breakdown: ScoreBreakdown
    score_explanation: List[ScoreExplanation]
    top_actions_before_applying: List[str] = Field(default_factory=list)
    parser_confidence: Literal["high", "medium", "low"]
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


class ChangeItem(BaseModel):
    type: Literal["bullet_update", "skills_reorder", "summary_update"]
    bullet_id: Optional[str] = None
    new_text: Optional[str] = None
    new_skills_order: Optional[List[str]] = None
    new_summary: Optional[str] = None


class ApplyTailorRequest(BaseModel):
    accepted_changes: List[ChangeItem]
    template_id: Optional[str] = None


class ApplyTailorResponse(BaseModel):
    version_id: str
    preview_html: str
    company_name: Optional[str]
    target_role_title: Optional[str] = None
    suggested_template: str
    filename_hint: str
    warning: Optional[str] = None
