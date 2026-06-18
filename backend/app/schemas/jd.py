from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Requirement(BaseModel):
    skill: str
    evidence_from_jd: str
    type: Literal["technical", "experience", "credential"]


class JDExtraction(BaseModel):
    must_have: List[Requirement]
    good_to_have: List[Requirement]
    soft_skills: List[str] = Field(default_factory=list)
    seniority: Literal["junior", "mid", "senior", "staff"]
    primary_role_category: Literal["SWE", "DS", "PM", "other"]
    country_hint: Literal["US", "IN", "other"]
    red_flags: List[str] = Field(default_factory=list)
    company_name: Optional[str] = None
    job_title: Optional[str] = None


class BulletPlaceholder(BaseModel):
    """Typed placeholder for hard numbers the AI couldn't verify.

    Same shape as ``app.schemas.resume_v2.Placeholder`` but redeclared
    here so JD schemas stay self-contained for OpenAI strict mode
    (which forbids dict fields without an explicit schema).
    """

    token: str
    what: str


class BulletOption(BaseModel):
    option_id: str
    text: str
    reason: str
    placeholders: List[BulletPlaceholder] = Field(default_factory=list)


class BulletDiff(BaseModel):
    bullet_id: str
    old: str
    new: str
    reason: str
    placeholders: List[BulletPlaceholder] = Field(default_factory=list)
    options: List[BulletOption] = Field(default_factory=list)


class SkillsReorder(BaseModel):
    new_order: List[str]
    rationale: str


class SummaryRewrite(BaseModel):
    old: Optional[str] = None
    new: str
    reason: str


class SuggestedAddition(BaseModel):
    section: str
    item: str
    reason: str


class BulletFitSignal(BaseModel):
    bullet_id: str
    relevance_score: int = Field(ge=0, le=100)
    evidence_level: Literal["high", "medium", "low"]
    recommendation: Literal["keep", "rewrite", "consider_trim"]
    matched_requirements: List[str] = Field(default_factory=list)
    noise_flags: List[str] = Field(default_factory=list)
    rationale: str


class ContentBudget(BaseModel):
    source_page_estimate: float = Field(ge=1)
    target_max_pages: int = Field(ge=1, le=2)
    recommended_bullet_budget: int = Field(ge=1)
    current_bullet_count: int = Field(ge=0)
    page_fit_risk: Literal["low", "medium", "high"]
    guidance: str


class DiffPlan(BaseModel):
    match_score: int = Field(ge=0, le=100)
    must_have_coverage_found: List[str]
    must_have_coverage_missing: List[str]
    good_to_have_coverage_found: List[str]
    good_to_have_coverage_missing: List[str]
    bullets: List[BulletDiff]
    skills_reorder: Optional[SkillsReorder] = None
    summary_rewrite: Optional[SummaryRewrite] = None
    suggested_additions: List[SuggestedAddition] = Field(default_factory=list)
    bullet_fit: List[BulletFitSignal] = Field(default_factory=list)
    content_budget: Optional[ContentBudget] = None
