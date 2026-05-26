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


class BulletPlaceholder(BaseModel):
    """Typed placeholder for hard numbers the AI couldn't verify.

    Same shape as ``app.schemas.resume_v2.Placeholder`` but redeclared
    here so JD schemas stay self-contained for OpenAI strict mode
    (which forbids dict fields without an explicit schema).
    """

    token: str
    what: str


class BulletDiff(BaseModel):
    bullet_id: str
    old: str
    new: str
    reason: str
    placeholders: List[BulletPlaceholder] = Field(default_factory=list)


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
