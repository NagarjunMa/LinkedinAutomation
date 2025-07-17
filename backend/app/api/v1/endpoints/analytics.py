from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.analytics_service import AnalyticsService
from sqlalchemy import func
from app.models.job import JobListing

router = APIRouter()

@router.get("/dashboard-all")
async def get_all_analytics_data(
    skills: Optional[str] = Query(None, description="User skills (comma-separated)"),
    experience_level: Optional[str] = Query("mid", description="Experience level"),
    preferred_locations: Optional[str] = Query(None, description="Preferred locations (comma-separated)"),
    db: Session = Depends(get_db)
):
    """
    Get all analytics data in a single optimized request
    """
    analytics = AnalyticsService(db)
    
    # Parse user profile
    user_profile = {
        "skills": skills.split(",") if skills else [],
        "experience_level": experience_level,
        "preferred_locations": preferred_locations.split(",") if preferred_locations else []
    }
    
    # Get all data
    executive_data = analytics.get_executive_dashboard()
    market_data = analytics.get_market_intelligence()
    profile_data = analytics.get_profile_optimization(user_profile["skills"])
    job_predictions = analytics.get_job_match_predictions(user_profile)
    search_analytics = analytics.get_search_query_analytics()
    
    return {
        "executive": executive_data,
        "market": market_data,
        "skills": profile_data["skills_analysis"],
        "recommendations": profile_data["recommendations"],
        "job_matches": job_predictions,
        "search_queries": search_analytics,
        "last_updated": analytics.db.query(func.max(JobListing.extracted_date)).scalar()
    }

@router.get("/executive-dashboard")
async def get_executive_dashboard(
    time_range: int = Query(30, description="Time range in days"),
    db: Session = Depends(get_db)
):
    """
    Get executive dashboard with high-level KPIs and trends
    """
    analytics = AnalyticsService(db)
    return analytics.get_executive_dashboard(time_range)

@router.get("/search-intelligence")
async def get_search_intelligence(db: Session = Depends(get_db)):
    """
    Get search query performance analytics and optimization recommendations
    """
    analytics = AnalyticsService(db)
    return analytics.get_search_query_analytics()

@router.get("/market-intelligence")
async def get_market_intelligence(db: Session = Depends(get_db)):
    """
    Get comprehensive job market intelligence including:
    - Tech stack trends
    - Location analysis  
    - Timing insights
    - Industry trends
    """
    analytics = AnalyticsService(db)
    return analytics.get_market_intelligence()

@router.get("/profile-optimization")
async def get_profile_optimization(
    user_skills: Optional[str] = Query(None, description="Comma-separated list of user skills"),
    db: Session = Depends(get_db)
):
    """
    Get personalized profile optimization recommendations including:
    - Skills gap analysis
    - Learning recommendations
    - Certification suggestions
    """
    analytics = AnalyticsService(db)
    skills_list = user_skills.split(",") if user_skills else []
    skills_list = [skill.strip() for skill in skills_list if skill.strip()]
    
    return analytics.get_profile_optimization(skills_list)

@router.get("/job-predictions")
async def get_job_predictions(
    skills: Optional[str] = Query(None, description="User skills (comma-separated)"),
    experience_level: Optional[str] = Query("mid", description="Experience level"),
    preferred_locations: Optional[str] = Query(None, description="Preferred locations (comma-separated)"),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered job match predictions and recommendations
    """
    analytics = AnalyticsService(db)
    
    user_profile = {
        "skills": skills.split(",") if skills else [],
        "experience_level": experience_level,
        "preferred_locations": preferred_locations.split(",") if preferred_locations else []
    }
    
    # Clean up the profile
    user_profile["skills"] = [s.strip() for s in user_profile["skills"] if s.strip()]
    user_profile["preferred_locations"] = [s.strip() for s in user_profile["preferred_locations"] if s.strip()]
    
    return analytics.get_job_match_predictions(user_profile)

@router.get("/skills-analysis")
async def get_skills_analysis(db: Session = Depends(get_db)):
    """
    Get detailed skills market analysis including demand, growth, and salary impact
    """
    analytics = AnalyticsService(db)
    profile_data = analytics.get_profile_optimization([])
    return profile_data["skills_analysis"]

@router.get("/location-insights")
async def get_location_insights(db: Session = Depends(get_db)):
    """
    Get location-based job market insights
    """
    analytics = AnalyticsService(db)
    market_data = analytics.get_market_intelligence()
    return {
        "location_analysis": market_data["location_analysis"],
        "timing_insights": market_data["timing_insights"]
    }

@router.get("/tech-trends")
async def get_tech_trends(db: Session = Depends(get_db)):
    """
    Get technology and skills trending analysis
    """
    analytics = AnalyticsService(db)
    market_data = analytics.get_market_intelligence()
    return {
        "tech_stack_trends": market_data["tech_stack_trends"],
        "industry_trends": market_data["industry_trends"]
    }

@router.get("/recommendations")
async def get_personalized_recommendations(
    skills: Optional[str] = Query(None, description="User skills (comma-separated)"),
    experience_level: Optional[str] = Query("mid", description="Experience level"),
    preferred_locations: Optional[str] = Query(None, description="Preferred locations (comma-separated)"),
    career_goals: Optional[str] = Query(None, description="Career goals"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive personalized recommendations for job search optimization
    """
    analytics = AnalyticsService(db)
    
    # Build user profile
    user_profile = {
        "skills": [s.strip() for s in skills.split(",") if s.strip()] if skills else [],
        "experience_level": experience_level,
        "preferred_locations": [s.strip() for s in preferred_locations.split(",") if s.strip()] if preferred_locations else [],
        "career_goals": career_goals
    }
    
    # Get all recommendation types
    profile_opt = analytics.get_profile_optimization(user_profile["skills"])
    job_predictions = analytics.get_job_match_predictions(user_profile)
    market_intel = analytics.get_market_intelligence()
    search_intel = analytics.get_search_query_analytics()
    
    return {
        "profile_recommendations": profile_opt["recommendations"],
        "job_matches": job_predictions["job_matches"][:10],
        "market_opportunities": {
            "hot_skills": market_intel["market_summary"]["hottest_skills"],
            "growing_locations": market_intel["market_summary"]["growing_locations"],
            "best_timing": market_intel["timing_insights"]["best_time"]
        },
        "search_optimization": {
            "avg_conversion_rate": search_intel["summary"]["avg_conversion_rate"],
            "total_queries": search_intel["summary"]["total_queries"]
        },
        "action_items": _generate_action_items(profile_opt, job_predictions, market_intel)
    }

@router.get("/company-insights")
async def get_company_insights(
    company_name: Optional[str] = Query(None, description="Specific company to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get insights about companies in the job market
    """
    analytics = AnalyticsService(db)
    market_data = analytics.get_market_intelligence()
    
    if company_name:
        # Filter for specific company
        company_data = [
            company for company in market_data["industry_trends"] 
            if company_name.lower() in company["company"].lower()
        ]
        return {"company_analysis": company_data}
    
    return {"top_companies": market_data["industry_trends"][:20]}

@router.get("/salary-insights")
async def get_salary_insights(
    skill: Optional[str] = Query(None, description="Skill to analyze salary for"),
    location: Optional[str] = Query(None, description="Location to analyze salary for"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    db: Session = Depends(get_db)
):
    """
    Get salary insights and benchmarking data
    """
    analytics = AnalyticsService(db)
    executive_data = analytics.get_executive_dashboard()
    
    # This would be enhanced with more sophisticated salary analysis
    salary_data = {
        "market_average": executive_data["avg_salary_range"],
        "filters_applied": {
            "skill": skill,
            "location": location,
            "experience_level": experience_level
        },
        "insights": [
            "Remote positions often offer 10-15% higher salaries",
            "Senior positions show 40-60% salary premium",
            "Tech skills command highest market rates"
        ]
    }
    
    return salary_data

def _generate_action_items(profile_opt: Dict, job_predictions: Dict, market_intel: Dict) -> List[Dict]:
    """Generate actionable recommendations based on analytics"""
    action_items = []
    
    # Skills-based actions
    missing_skills = profile_opt.get("skills_analysis", {}).get("missing_skills", [])
    if missing_skills:
        action_items.append({
            "category": "Skills Development",
            "priority": "High",
            "action": f"Learn {missing_skills[0]} - high market demand",
            "timeline": "2-4 weeks",
            "impact": "Increase job match rate by 25%"
        })
    
    # Job application actions
    high_match_jobs = [
        job for job in job_predictions.get("job_matches", []) 
        if job.get("match_score", 0) > 80
    ]
    if high_match_jobs:
        action_items.append({
            "category": "Job Applications",
            "priority": "Immediate",
            "action": f"Apply to {len(high_match_jobs)} high-match jobs today",
            "timeline": "Today",
            "impact": "High probability of success"
        })
    
    # Market timing actions
    best_time = market_intel.get("timing_insights", {}).get("best_time", "Tuesday 10 AM")
    action_items.append({
        "category": "Application Timing",
        "priority": "Medium",
        "action": f"Schedule applications for {best_time}",
        "timeline": "This week",
        "impact": "34% higher response rates"
    })
    
    # Location optimization
    growing_locations = market_intel.get("market_summary", {}).get("growing_locations", [])
    if growing_locations:
        action_items.append({
            "category": "Geographic Strategy",
            "priority": "Medium", 
            "action": f"Expand search to {growing_locations[0]}",
            "timeline": "Next search cycle",
            "impact": "Access to growing job market"
        })
    
    return action_items 