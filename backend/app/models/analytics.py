from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class UserAnalytics(Base):
    """
    Stores AI-generated analytics and insights for users based on their job application patterns
    """
    __tablename__ = "user_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)

    # Skills Analysis - AI-extracted from job requirements
    top_skills = Column(JSON)  # [{"skill": "React", "percentage": 78, "count": 23, "trend": "stable"}]
    trending_skills = Column(JSON)  # ["Docker", "AWS", "GraphQL"] - emerging in recent posts
    recommended_skills = Column(JSON)  # ["Next.js", "TypeScript"] - gaps in current applications
    skills_diversity_score = Column(Float)  # 0-100, how varied are the skill requirements

    # Job Preferences Analysis
    work_location_preferences = Column(JSON)  # {"remote": {"count": 15, "percentage": 60}, "hybrid": {...}}
    job_title_distribution = Column(JSON)  # [{"title": "Frontend Engineer", "count": 12, "percentage": 45}]
    company_size_preferences = Column(JSON)  # {"startup": 40%, "mid": 35%, "enterprise": 25%}
    salary_range_analysis = Column(JSON)  # {"min": 80000, "max": 150000, "average": 115000}

    # Application Behavior Patterns
    application_velocity = Column(Float)  # Average applications per week
    application_success_rate = Column(Float)  # Percentage that get responses
    peak_application_days = Column(JSON)  # ["monday", "tuesday"] - when user applies most
    application_time_patterns = Column(JSON)  # {"morning": 20%, "afternoon": 60%, "evening": 20%}

    # AI-Generated Behavioral Insights
    ai_insights = Column(JSON)  # [{"type": "strength", "category": "skills", "message": "Strong in modern frontend"}, ...]
    success_patterns = Column(JSON)  # What types of jobs get better responses
    improvement_suggestions = Column(JSON)  # [{"area": "skills", "suggestion": "Add backend skills", "priority": "high"}]
    weekly_recommendation = Column(Text)  # Specific action for next week

    # Market Intelligence
    competition_level = Column(String(20))  # "low", "medium", "high" - based on skills vs market
    market_demand_score = Column(Float)  # 0-100 score for user's skill set demand
    salary_competitiveness = Column(String(20))  # "below", "competitive", "above"

    # Analytics Metadata
    total_applications_analyzed = Column(Integer)
    analysis_period_start = Column(DateTime)
    analysis_period_end = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    analytics_version = Column(String(10), default="1.0")  # For future improvements

    # Performance tracking
    generation_time_seconds = Column(Float)  # How long analytics took to generate
    ai_confidence_score = Column(Float)  # 0-100 confidence in AI insights

    def __repr__(self):
        return f"<UserAnalytics {self.user_id} - {self.total_applications_analyzed} apps>"

class AnalyticsCache(Base):
    """
    Fast-access cache for analytics data to avoid regenerating frequently
    """
    __tablename__ = "analytics_cache"

    user_id = Column(String(100), primary_key=True, index=True)
    cache_data = Column(JSON, nullable=False)  # Complete analytics payload
    cache_type = Column(String(50), default="full_analytics")  # "full_analytics", "skills_only", etc.

    # Cache management
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)

    # Cache metadata
    data_hash = Column(String(64))  # Hash of source data to detect changes
    cache_size_bytes = Column(Integer)  # For monitoring cache efficiency

    def __repr__(self):
        return f"<AnalyticsCache {self.user_id} - expires {self.expires_at}>"

class AnalyticsInsight(Base):
    """
    Individual insights that can be tracked, rated, and improved over time
    """
    __tablename__ = "analytics_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    analytics_id = Column(Integer, ForeignKey("user_analytics.id"), nullable=False)

    # Insight details
    insight_type = Column(String(50), nullable=False)  # "skill_gap", "market_trend", "behavior_pattern"
    category = Column(String(50))  # "skills", "preferences", "timing", "strategy"
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")  # "low", "medium", "high", "critical"

    # Actionability
    is_actionable = Column(Boolean, default=True)
    action_required = Column(Text)  # Specific action user should take
    estimated_impact = Column(String(20))  # "low", "medium", "high"
    implementation_difficulty = Column(String(20))  # "easy", "medium", "hard"

    # User feedback and tracking
    user_rating = Column(Integer)  # 1-5 stars from user
    user_feedback = Column(Text)  # User's notes on the insight
    was_acted_upon = Column(Boolean, default=False)
    action_date = Column(DateTime)

    # AI confidence and validation
    ai_confidence = Column(Float)  # 0-100 confidence in this insight
    validation_status = Column(String(20), default="pending")  # "pending", "validated", "incorrect"

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    shown_to_user = Column(Boolean, default=False)
    shown_at = Column(DateTime)

    def __repr__(self):
        return f"<AnalyticsInsight {self.insight_type}: {self.title[:30]}...>"

# Performance indexes for efficient querying
Index('idx_user_analytics_user_updated', UserAnalytics.user_id, UserAnalytics.last_updated.desc())
Index('idx_analytics_cache_user_expires', AnalyticsCache.user_id, AnalyticsCache.expires_at)
Index('idx_insights_user_type_priority', AnalyticsInsight.user_id, AnalyticsInsight.insight_type, AnalyticsInsight.priority)
Index('idx_insights_actionable_shown', AnalyticsInsight.is_actionable, AnalyticsInsight.shown_to_user)