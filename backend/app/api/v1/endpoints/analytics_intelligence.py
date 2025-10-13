from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.user import User
from app.services.analytics_intelligence import AnalyticsIntelligenceService
from app.schemas.analytics import (
    AnalyticsAPIResponse,
    FullAnalyticsResponse,
    AnalyticsOverviewResponse,
    TrendAnalysisResponse,
    AnalyticsHealthResponse,
    AnalyticsErrorResponse,
    AnalyticsRequest,
    UserPreferencesUpdate
)
import logging

logger = logging.getLogger(__name__)
from app.tasks.analytics_tasks import update_user_analytics_task

router = APIRouter()


def get_current_user_mock(db: Session = Depends(get_db)) -> User:
    """
    Temporary mock for user authentication
    Replace with your actual authentication dependency
    """
    # For now, get the first user in the database
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    return user


@router.get("/overview", response_model=AnalyticsAPIResponse)
async def get_analytics_overview(
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Get analytics overview for dashboard display
    Returns simplified analytics data for quick dashboard cards
    """
    try:
        analytics_service = AnalyticsIntelligenceService(db)

        # Try to get cached analytics first
        cached_data = await analytics_service.get_cached_analytics(current_user.user_id)

        if cached_data:
            logger.info(f"Serving cached analytics for user {current_user.user_id}")
            # Convert full analytics to overview format
            overview_data = _convert_to_overview(cached_data)
            return AnalyticsAPIResponse(
                status="success",
                message="Analytics overview retrieved from cache",
                data=overview_data
            )

        # Generate fresh analytics if no cache
        logger.info(f"Generating fresh analytics overview for user {current_user.user_id}")
        analytics_data = await analytics_service.generate_user_analytics(current_user.user_id)

        if analytics_data.get("metadata", {}).get("status") == "insufficient_data":
            return AnalyticsAPIResponse(
                status="warning",
                message="Insufficient application data for detailed analytics",
                data=AnalyticsOverviewResponse(
                    key_insights_count=len(analytics_data.get("insights", [])),
                    last_updated=datetime.utcnow().isoformat()
                )
            )

        overview_data = _convert_to_overview(analytics_data)
        return AnalyticsAPIResponse(
            status="success",
            message="Analytics overview generated successfully",
            data=overview_data
        )

    except Exception as e:
        logger.error(f"Analytics overview failed for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics overview: {str(e)}"
        )


@router.get("/full", response_model=AnalyticsAPIResponse)
async def get_full_analytics(
    days: int = Query(30, ge=7, le=90, description="Analysis period in days"),
    force_refresh: bool = Query(False, description="Force fresh generation"),
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Get complete analytics data for detailed analytics page
    """
    try:
        analytics_service = AnalyticsIntelligenceService(db)

        # Check cache unless force refresh is requested
        if not force_refresh:
            cached_data = await analytics_service.get_cached_analytics(current_user.user_id)
            if cached_data and cached_data.get("metadata", {}).get("analysis_period_days") == days:
                logger.info(f"Serving cached full analytics for user {current_user.user_id}")
                full_response = _convert_to_full_response(cached_data)
                return AnalyticsAPIResponse(
                    status="success",
                    message="Full analytics retrieved from cache",
                    data=full_response
                )

        # Generate fresh analytics
        logger.info(f"Generating fresh full analytics for user {current_user.user_id} ({days} days)")
        analytics_data = await analytics_service.generate_user_analytics(current_user.user_id, days)

        if analytics_data.get("metadata", {}).get("status") == "insufficient_data":
            return AnalyticsAPIResponse(
                status="warning",
                message="Insufficient application data for detailed analytics",
                data=_convert_to_full_response(analytics_data)
            )

        full_response = _convert_to_full_response(analytics_data)
        return AnalyticsAPIResponse(
            status="success",
            message="Full analytics generated successfully",
            data=full_response
        )

    except Exception as e:
        logger.error(f"Full analytics failed for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate full analytics: {str(e)}"
        )


@router.get("/skills", response_model=AnalyticsAPIResponse)
async def get_skills_analytics(
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Get detailed skills analysis only
    """
    try:
        analytics_service = AnalyticsIntelligenceService(db)

        # Try cache first
        cached_data = await analytics_service.get_cached_analytics(current_user.user_id)
        if cached_data:
            skills_data = cached_data.get("skills", {})
            return AnalyticsAPIResponse(
                status="success",
                message="Skills analytics retrieved",
                data=skills_data
            )

        # Generate fresh skills analysis
        applications = await analytics_service.get_recent_applications(current_user.user_id)
        if len(applications) < 3:
            return AnalyticsAPIResponse(
                status="warning",
                message="Insufficient applications for skills analysis",
                data={"message": "Apply to more jobs to get detailed skills analysis"}
            )

        skills_data = await analytics_service.analyze_skills_patterns(applications)
        return AnalyticsAPIResponse(
            status="success",
            message="Skills analysis generated",
            data=skills_data
        )

    except Exception as e:
        logger.error(f"Skills analytics failed for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate skills analytics: {str(e)}"
        )


@router.get("/trends", response_model=AnalyticsAPIResponse)
async def get_application_trends(
    days: int = Query(30, ge=7, le=90, description="Analysis period in days"),
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Get application trends over time for charts
    """
    try:
        analytics_service = AnalyticsIntelligenceService(db)

        # Get applications for the period
        applications = await analytics_service.get_recent_applications(current_user.user_id, days)

        if len(applications) == 0:
            return AnalyticsAPIResponse(
                status="warning",
                message="No applications found for trend analysis",
                data=TrendAnalysisResponse(
                    data_points=[],
                    period_days=days,
                    total_applications=0,
                    average_per_week=0.0,
                    trend_direction="stable"
                )
            )

        # Generate trend data
        trend_data = _generate_trend_data(applications, days)

        return AnalyticsAPIResponse(
            status="success",
            message="Application trends generated",
            data=trend_data
        )

    except Exception as e:
        logger.error(f"Trends analytics failed for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate trends: {str(e)}"
        )


@router.post("/refresh")
async def refresh_analytics(
    background_tasks: BackgroundTasks,
    request: AnalyticsRequest = AnalyticsRequest(),
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Trigger analytics refresh in background
    """
    try:
        # Queue background task for analytics generation
        background_tasks.add_task(
            lambda: update_user_analytics_task.delay(current_user.user_id, request.days)
        )

        return AnalyticsAPIResponse(
            status="success",
            message="Analytics refresh queued successfully",
            data={"user_id": current_user.user_id, "days": request.days}
        )

    except Exception as e:
        logger.error(f"Analytics refresh failed for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue analytics refresh: {str(e)}"
        )


@router.get("/health", response_model=AnalyticsAPIResponse)
async def get_analytics_health(
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Get analytics system health status for the current user
    """
    try:
        from app.models.analytics import UserAnalytics, AnalyticsCache

        # Check user's analytics status
        user_analytics = db.query(UserAnalytics).filter(
            UserAnalytics.user_id == current_user.user_id
        ).first()

        cache_entry = db.query(AnalyticsCache).filter(
            AnalyticsCache.user_id == current_user.user_id
        ).first()

        # Determine health status
        status = "healthy"
        last_update = None
        cache_status = "none"

        if user_analytics:
            last_update = user_analytics.last_updated.isoformat() if user_analytics.last_updated else None

            # Check if analytics are stale (older than 7 days)
            if user_analytics.last_updated and user_analytics.last_updated < datetime.utcnow() - timedelta(days=7):
                status = "warning"

        if cache_entry:
            if cache_entry.expires_at > datetime.utcnow():
                cache_status = "valid"
            else:
                cache_status = "expired"

        health_data = AnalyticsHealthResponse(
            status=status,
            last_update=last_update,
            cache_hit_rate=100.0 if cache_status == "valid" else 0.0,
            pending_updates=1 if status == "warning" else 0,
            system_load="low"
        )

        return AnalyticsAPIResponse(
            status="success",
            message="Analytics health status retrieved",
            data=health_data
        )

    except Exception as e:
        logger.error(f"Health check failed for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check analytics health: {str(e)}"
        )


@router.put("/preferences")
async def update_analytics_preferences(
    preferences: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Update user's analytics preferences
    """
    try:
        # For now, just acknowledge the update
        # In a real implementation, you'd store these in a user preferences table

        logger.info(f"Analytics preferences updated for user {current_user.user_id}: {preferences.dict()}")

        return AnalyticsAPIResponse(
            status="success",
            message="Analytics preferences updated successfully",
            data=preferences.dict()
        )

    except Exception as e:
        logger.error(f"Preferences update failed for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update preferences: {str(e)}"
        )


# Helper functions
def _convert_to_overview(analytics_data: dict) -> AnalyticsOverviewResponse:
    """Convert full analytics data to overview format"""
    skills = analytics_data.get("skills", {})
    preferences = analytics_data.get("preferences", {})
    behavior = analytics_data.get("behavior", {})
    metadata = analytics_data.get("metadata", {})

    return AnalyticsOverviewResponse(
        top_skills_preview=skills.get("top_skills", [])[:5],  # Top 5 only
        primary_job_focus=preferences.get("job_titles", {}).get("primary_focus"),
        application_velocity=behavior.get("velocity", {}).get("apps_per_week"),
        success_rate=behavior.get("success_metrics", {}).get("application_rate"),
        key_insights_count=len(analytics_data.get("insights", [])),
        last_updated=metadata.get("analysis_date")
    )


def _convert_to_full_response(analytics_data: dict) -> FullAnalyticsResponse:
    """Convert analytics data to full response format"""
    from app.schemas.analytics import (
        SkillsAnalysisResponse, PreferencesAnalysisResponse,
        BehaviorAnalysisResponse, MarketAnalysisResponse,
        AnalyticsMetadata, AnalyticsInsightData,
        ApplicationVelocity, TimingPatterns, SuccessMetrics
    )

    skills_data = analytics_data.get("skills", {})
    preferences_data = analytics_data.get("preferences", {})
    behavior_data = analytics_data.get("behavior", {})
    market_data = analytics_data.get("market", {})
    insights_data = analytics_data.get("insights", [])
    metadata = analytics_data.get("metadata", {})

    # Convert insights to proper format
    insights = []
    for insight in insights_data:
        if isinstance(insight, dict) and all(key in insight for key in ['type', 'priority', 'title', 'message']):
            insights.append(AnalyticsInsightData(**insight))

    # Handle behavior data with defaults for insufficient data
    behavior_response = None
    if behavior_data and not behavior_data.get('message'):  # Only if it's real data, not just a message
        try:
            behavior_response = BehaviorAnalysisResponse(**behavior_data)
        except Exception:
            behavior_response = None
    elif behavior_data:  # Has insufficient data message, create default structure
        behavior_response = BehaviorAnalysisResponse(
            velocity=ApplicationVelocity(
                apps_per_week=0.0,
                total_period_weeks=1.0
            ),
            timing_patterns=TimingPatterns(
                peak_days=[],
                day_distribution={}
            ),
            success_metrics=SuccessMetrics(
                application_rate=0.0,
                total_applied=0,
                total_viewed=0
            )
        )

    # Create default metadata if missing required fields
    if not metadata or not all(key in metadata for key in ['user_id', 'total_applications', 'analysis_period_days', 'analysis_date']):
        metadata = {
            "user_id": metadata.get("user_id", "demo_user"),
            "total_applications": metadata.get("total_applications", 0),
            "analysis_period_days": metadata.get("analysis_period_days", 30),
            "analysis_date": metadata.get("analysis_date", datetime.utcnow().isoformat()),
            "generation_time_seconds": metadata.get("generation_time_seconds", 0.0),
            "status": metadata.get("status", "insufficient_data")
        }

    return FullAnalyticsResponse(
        skills=SkillsAnalysisResponse(**skills_data) if skills_data and not skills_data.get('message') else SkillsAnalysisResponse(),
        preferences=PreferencesAnalysisResponse(**preferences_data) if preferences_data and not preferences_data.get('message') else PreferencesAnalysisResponse(),
        behavior=behavior_response,
        market=MarketAnalysisResponse(**market_data) if market_data and not market_data.get('message') else None,
        insights=insights,
        metadata=AnalyticsMetadata(**metadata)
    )


def _generate_trend_data(applications, days: int) -> TrendAnalysisResponse:
    """Generate trend data from applications"""
    from collections import defaultdict
    from app.schemas.analytics import TrendDataPoint

    # Group applications by date
    daily_counts = defaultdict(int)

    for app in applications:
        if hasattr(app, 'extracted_date') and app.extracted_date:
            date_str = app.extracted_date.strftime("%Y-%m-%d")
            daily_counts[date_str] += 1

    # Create data points for chart
    data_points = []
    total_apps = len(applications)

    # Fill in missing dates with 0
    start_date = datetime.utcnow() - timedelta(days=days)
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        count = daily_counts.get(date_str, 0)

        data_points.append(TrendDataPoint(
            date=date_str,
            applications=count,
            responses=0  # Would need response tracking for this
        ))

    # Calculate trend direction
    if len(data_points) >= 7:
        first_week = sum(dp.applications for dp in data_points[:7])
        last_week = sum(dp.applications for dp in data_points[-7:])

        if last_week > first_week * 1.2:
            trend_direction = "up"
        elif last_week < first_week * 0.8:
            trend_direction = "down"
        else:
            trend_direction = "stable"
    else:
        trend_direction = "stable"

    average_per_week = (total_apps / max(days / 7, 1))

    return TrendAnalysisResponse(
        data_points=data_points,
        period_days=days,
        total_applications=total_apps,
        average_per_week=round(average_per_week, 2),
        trend_direction=trend_direction
    )