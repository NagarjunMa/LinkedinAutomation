from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class SkillData(BaseModel):
    """Individual skill with usage statistics"""
    skill: str = Field(..., description="Skill name")
    count: int = Field(..., ge=0, description="Number of occurrences")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of jobs mentioning this skill")
    category: Optional[str] = Field(None, description="Skill category (frontend, backend, etc.)")


class SkillsAnalysisResponse(BaseModel):
    """Skills analysis results"""
    top_skills: List[SkillData] = Field(default_factory=list, description="Most requested skills")
    trending_skills: List[str] = Field(default_factory=list, description="Emerging skills in recent posts")
    recommended_skills: List[str] = Field(default_factory=list, description="Skills user should learn")
    diversity_score: Optional[float] = Field(None, ge=0, le=100, description="How varied are skill requirements")


class WorkLocationPreference(BaseModel):
    """Work location statistics"""
    count: int = Field(..., ge=0)
    percentage: float = Field(..., ge=0, le=100)


class JobTitleDistribution(BaseModel):
    """Job title usage statistics"""
    title: str
    count: int = Field(..., ge=0)
    percentage: float = Field(..., ge=0, le=100)


class JobTitlesAnalysis(BaseModel):
    """Job titles analysis results"""
    distribution: List[JobTitleDistribution] = Field(default_factory=list)
    primary_focus: Optional[str] = Field(None, description="Most applied job type")
    diversity_score: int = Field(0, ge=0, description="Number of different job types")


class SalaryAnalysis(BaseModel):
    """Salary range analysis"""
    min: Optional[int] = Field(None, description="Minimum salary found")
    max: Optional[int] = Field(None, description="Maximum salary found")
    average: Optional[int] = Field(None, description="Average salary")
    count: int = Field(0, ge=0, description="Number of jobs with salary data")


class PreferencesAnalysisResponse(BaseModel):
    """Job preferences analysis results"""
    work_location: Dict[str, WorkLocationPreference] = Field(default_factory=dict)
    job_titles: JobTitlesAnalysis = Field(default_factory=JobTitlesAnalysis)
    company_sizes: Dict[str, WorkLocationPreference] = Field(default_factory=dict)
    salary_ranges: SalaryAnalysis = Field(default_factory=SalaryAnalysis)


class ApplicationVelocity(BaseModel):
    """Application velocity metrics"""
    apps_per_week: float = Field(..., ge=0, description="Average applications per week")
    total_period_weeks: float = Field(..., ge=0, description="Analysis period in weeks")


class TimingPatterns(BaseModel):
    """Application timing patterns"""
    peak_days: List[tuple] = Field(default_factory=list, description="Peak application days")
    day_distribution: Dict[str, int] = Field(default_factory=dict, description="Applications by day of week")


class SuccessMetrics(BaseModel):
    """Application success tracking"""
    application_rate: float = Field(..., ge=0, le=100, description="Percentage of jobs applied to")
    total_applied: int = Field(..., ge=0, description="Total applications submitted")
    total_viewed: int = Field(..., ge=0, description="Total jobs viewed")


class BehaviorAnalysisResponse(BaseModel):
    """Application behavior analysis results"""
    velocity: ApplicationVelocity
    timing_patterns: TimingPatterns
    success_metrics: SuccessMetrics


class MarketAnalysisResponse(BaseModel):
    """Market positioning analysis"""
    competition_level: Optional[str] = Field(None, description="Competition level: low, medium, high")
    market_demand_score: Optional[float] = Field(None, ge=0, le=100, description="Market demand for user skills")
    salary_competitiveness: Optional[str] = Field(None, description="Salary competitiveness: below, competitive, above")


class AnalyticsInsightData(BaseModel):
    """Individual analytics insight"""
    type: str = Field(..., description="Insight type")
    priority: str = Field(..., description="Priority level")
    title: str = Field(..., description="Insight title")
    message: str = Field(..., description="Detailed insight message")
    action: Optional[str] = Field(None, description="Recommended action")
    impact: Optional[str] = Field(None, description="Expected impact level")


class AnalyticsMetadata(BaseModel):
    """Analytics generation metadata"""
    user_id: str
    total_applications: int = Field(..., ge=0)
    analysis_period_days: int = Field(..., ge=1)
    analysis_date: str = Field(..., description="ISO datetime string")
    generation_time_seconds: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None, description="Generation status")


class FullAnalyticsResponse(BaseModel):
    """Complete analytics response"""
    skills: SkillsAnalysisResponse = Field(default_factory=SkillsAnalysisResponse)
    preferences: PreferencesAnalysisResponse = Field(default_factory=PreferencesAnalysisResponse)
    behavior: Optional[BehaviorAnalysisResponse] = Field(None)
    market: Optional[MarketAnalysisResponse] = Field(None)
    insights: List[AnalyticsInsightData] = Field(default_factory=list)
    metadata: AnalyticsMetadata

    class Config:
        schema_extra = {
            "example": {
                "skills": {
                    "top_skills": [
                        {"skill": "React", "count": 15, "percentage": 75.0, "category": "frontend"},
                        {"skill": "TypeScript", "count": 12, "percentage": 60.0, "category": "frontend"}
                    ],
                    "trending_skills": ["Docker", "GraphQL"],
                    "recommended_skills": ["Next.js", "AWS"],
                    "diversity_score": 85.0
                },
                "preferences": {
                    "work_location": {
                        "remote": {"count": 12, "percentage": 60.0},
                        "hybrid": {"count": 6, "percentage": 30.0},
                        "onsite": {"count": 2, "percentage": 10.0}
                    },
                    "job_titles": {
                        "distribution": [
                            {"title": "Frontend Engineer", "count": 8, "percentage": 40.0}
                        ],
                        "primary_focus": "Frontend Engineer",
                        "diversity_score": 3
                    }
                },
                "insights": [
                    {
                        "type": "skill_development",
                        "priority": "high",
                        "title": "Expand Backend Skills",
                        "message": "Consider learning backend technologies to become full-stack",
                        "action": "Learn Node.js and Express",
                        "impact": "high"
                    }
                ],
                "metadata": {
                    "user_id": "user123",
                    "total_applications": 20,
                    "analysis_period_days": 30,
                    "analysis_date": "2024-10-12T10:30:00Z",
                    "generation_time_seconds": 2.5
                }
            }
        }


class AnalyticsOverviewResponse(BaseModel):
    """Simplified analytics overview for dashboard cards"""
    top_skills_preview: List[SkillData] = Field(default_factory=list, description="Top 5 skills preview")
    primary_job_focus: Optional[str] = Field(None, description="Main job type user applies to")
    application_velocity: Optional[float] = Field(None, description="Apps per week")
    success_rate: Optional[float] = Field(None, description="Application success rate")
    key_insights_count: int = Field(0, description="Number of actionable insights")
    last_updated: Optional[str] = Field(None, description="Last analytics update")

    class Config:
        schema_extra = {
            "example": {
                "top_skills_preview": [
                    {"skill": "React", "count": 15, "percentage": 75.0},
                    {"skill": "JavaScript", "count": 13, "percentage": 65.0}
                ],
                "primary_job_focus": "Frontend Engineer",
                "application_velocity": 3.5,
                "success_rate": 65.0,
                "key_insights_count": 4,
                "last_updated": "2024-10-12T10:30:00Z"
            }
        }


class TrendDataPoint(BaseModel):
    """Single data point for trend charts"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    applications: int = Field(..., ge=0, description="Number of applications")
    responses: Optional[int] = Field(None, ge=0, description="Number of responses received")


class TrendAnalysisResponse(BaseModel):
    """Application trends over time"""
    data_points: List[TrendDataPoint] = Field(..., description="Trend data points")
    period_days: int = Field(..., ge=1, description="Analysis period in days")
    total_applications: int = Field(..., ge=0, description="Total applications in period")
    average_per_week: float = Field(..., ge=0, description="Average applications per week")
    trend_direction: str = Field(..., description="up, down, or stable")

    class Config:
        schema_extra = {
            "example": {
                "data_points": [
                    {"date": "2024-10-05", "applications": 3, "responses": 1},
                    {"date": "2024-10-06", "applications": 2, "responses": 0},
                    {"date": "2024-10-07", "applications": 4, "responses": 2}
                ],
                "period_days": 7,
                "total_applications": 25,
                "average_per_week": 3.6,
                "trend_direction": "up"
            }
        }


class AnalyticsHealthResponse(BaseModel):
    """Analytics system health status"""
    status: str = Field(..., description="healthy, warning, or error")
    last_update: Optional[str] = Field(None, description="Last analytics update time")
    cache_hit_rate: Optional[float] = Field(None, ge=0, le=100, description="Cache efficiency percentage")
    pending_updates: int = Field(0, ge=0, description="Number of users needing updates")
    system_load: Optional[str] = Field(None, description="low, medium, or high")


class AnalyticsRequest(BaseModel):
    """Request parameters for analytics generation"""
    days: int = Field(30, ge=1, le=365, description="Analysis period in days")
    force_refresh: bool = Field(False, description="Force fresh generation, ignore cache")
    include_insights: bool = Field(True, description="Include AI-generated insights")


class UserPreferencesUpdate(BaseModel):
    """Update user preferences for analytics"""
    weekly_digest: bool = Field(True, description="Send weekly analytics digest")
    insight_notifications: bool = Field(True, description="Send insight notifications")
    analysis_period_days: int = Field(30, ge=7, le=90, description="Default analysis period")


# Response wrapper models
class AnalyticsAPIResponse(BaseModel):
    """Standard API response wrapper"""
    status: str = Field(..., description="success, error, or warning")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[Union[
        FullAnalyticsResponse,
        AnalyticsOverviewResponse,
        TrendAnalysisResponse,
        AnalyticsHealthResponse
    ]] = Field(None)
    errors: Optional[List[str]] = Field(None, description="List of errors if any")

    @validator('status')
    def validate_status(cls, v):
        if v not in ['success', 'error', 'warning']:
            raise ValueError('Status must be success, error, or warning')
        return v


class AnalyticsErrorResponse(BaseModel):
    """Error response for analytics endpoints"""
    status: str = Field("error")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        schema_extra = {
            "example": {
                "status": "error",
                "message": "Insufficient application data for analytics generation",
                "error_code": "INSUFFICIENT_DATA",
                "details": {
                    "applications_found": 2,
                    "minimum_required": 3,
                    "suggestion": "Apply to more jobs to unlock analytics insights"
                }
            }
        }