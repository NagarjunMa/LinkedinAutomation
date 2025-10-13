import json
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.core.ai_service import AIService
from app.models.analytics import UserAnalytics, AnalyticsCache, AnalyticsInsight
from app.models.job import JobListing, JobApplication
from app.models.user import User

logger = logging.getLogger(__name__)


class AnalyticsIntelligenceService:
    """
    AI-powered analytics service that generates intelligent insights from user job application data
    """

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    async def generate_user_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Main analytics generation pipeline - creates comprehensive user insights
        """
        start_time = datetime.utcnow()

        try:
            # Get user's recent applications
            applications = await self.get_recent_applications(user_id, days)

            if len(applications) < 3:
                return await self.generate_minimal_analytics(user_id, applications)

            logger.info(f"Analyzing {len(applications)} applications for user {user_id}")

            # Generate all analytics components
            skills_analysis = await self.analyze_skills_patterns(applications)
            preferences_analysis = await self.analyze_job_preferences(applications)
            behavioral_analysis = await self.analyze_application_behavior(applications)
            market_analysis = await self.analyze_market_positioning(user_id, applications)

            # Generate AI insights
            ai_insights = await self.generate_ai_insights(
                skills_analysis, preferences_analysis, behavioral_analysis, applications
            )

            # Compile final analytics
            analytics_data = {
                "skills": skills_analysis,
                "preferences": preferences_analysis,
                "behavior": behavioral_analysis,
                "market": market_analysis,
                "insights": ai_insights,
                "metadata": {
                    "user_id": user_id,
                    "total_applications": len(applications),
                    "analysis_period_days": days,
                    "analysis_date": datetime.utcnow().isoformat(),
                    "generation_time_seconds": (datetime.utcnow() - start_time).total_seconds()
                }
            }

            # Store analytics in database
            await self.store_analytics(user_id, analytics_data, days)

            # Update cache for fast access
            await self.update_analytics_cache(user_id, analytics_data)

            logger.info(f"Analytics generated successfully for user {user_id}")
            return analytics_data

        except Exception as e:
            logger.error(f"Analytics generation failed for user {user_id}: {str(e)}")
            raise

    async def analyze_skills_patterns(self, applications: List[JobListing]) -> Dict[str, Any]:
        """
        Analyze skill patterns from job requirements using AI
        """
        # Combine all job requirements and descriptions
        all_text = []
        for app in applications:
            if app.requirements:
                all_text.append(app.requirements)
            if app.description:
                all_text.append(app.description)

        combined_text = "\n\n".join(all_text)

        if not combined_text.strip():
            return {"top_skills": [], "trending_skills": [], "recommended_skills": []}

        prompt = f"""
        Analyze these job requirements and descriptions to extract skill patterns:

        {combined_text[:8000]}  # Limit to avoid token limits

        Extract and analyze:
        1. Top 10 most frequently mentioned technical skills with occurrence count
        2. 5 trending/emerging skills that appear in multiple recent postings
        3. 5 recommended skills the candidate should learn based on gaps
        4. Calculate diversity score (1-100) for how varied the skill requirements are

        Return ONLY valid JSON:
        {{
            "top_skills": [
                {{"skill": "React", "count": 15, "percentage": 75, "category": "frontend"}},
                {{"skill": "Python", "count": 12, "percentage": 60, "category": "backend"}}
            ],
            "trending_skills": ["Docker", "GraphQL", "TypeScript"],
            "recommended_skills": ["Next.js", "AWS", "MongoDB"],
            "diversity_score": 85
        }}
        """

        try:
            response = await self.ai_service.generate_response(prompt)
            return json.loads(response)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Skills analysis failed: {e}")
            return await self.fallback_skills_analysis(applications)

    async def analyze_job_preferences(self, applications: List[JobListing]) -> Dict[str, Any]:
        """
        Analyze user's job preferences from application patterns
        """
        total_apps = len(applications)

        # Work location analysis
        location_counts = {"remote": 0, "hybrid": 0, "onsite": 0, "unknown": 0}

        for app in applications:
            location = (app.location or "").lower()
            if any(term in location for term in ["remote", "anywhere", "distributed"]):
                location_counts["remote"] += 1
            elif any(term in location for term in ["hybrid", "flexible"]):
                location_counts["hybrid"] += 1
            elif location and location != "unknown":
                location_counts["onsite"] += 1
            else:
                location_counts["unknown"] += 1

        work_location_prefs = {
            location: {
                "count": count,
                "percentage": round((count / total_apps) * 100, 1)
            }
            for location, count in location_counts.items()
        }

        # Job title distribution
        title_counter = Counter()
        for app in applications:
            normalized_title = self.normalize_job_title(app.title)
            title_counter[normalized_title] += 1

        title_distribution = [
            {
                "title": title,
                "count": count,
                "percentage": round((count / total_apps) * 100, 1)
            }
            for title, count in title_counter.most_common(10)
        ]

        # Company size analysis (if available in descriptions)
        company_sizes = await self.analyze_company_sizes(applications)

        # Salary range analysis
        salary_analysis = await self.analyze_salary_ranges(applications)

        return {
            "work_location": work_location_prefs,
            "job_titles": {
                "distribution": title_distribution,
                "primary_focus": title_distribution[0]["title"] if title_distribution else "Unknown",
                "diversity_score": len(title_counter)
            },
            "company_sizes": company_sizes,
            "salary_ranges": salary_analysis
        }

    async def analyze_application_behavior(self, applications: List[JobListing]) -> Dict[str, Any]:
        """
        Analyze user's application timing and behavior patterns
        """
        if not applications:
            return {}

        # Application velocity (apps per week)
        date_range = (max(app.extracted_date for app in applications if app.extracted_date) -
                     min(app.extracted_date for app in applications if app.extracted_date)).days
        weeks = max(date_range / 7, 1)
        velocity = len(applications) / weeks

        # Day-of-week patterns
        day_counts = defaultdict(int)
        for app in applications:
            if app.extracted_date:
                day_name = app.extracted_date.strftime("%A").lower()
                day_counts[day_name] += 1

        # Application success tracking
        applied_count = len([app for app in applications if app.applied])
        success_rate = (applied_count / len(applications)) * 100 if applications else 0

        return {
            "velocity": {
                "apps_per_week": round(velocity, 1),
                "total_period_weeks": round(weeks, 1)
            },
            "timing_patterns": {
                "peak_days": sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3],
                "day_distribution": dict(day_counts)
            },
            "success_metrics": {
                "application_rate": round(success_rate, 1),
                "total_applied": applied_count,
                "total_viewed": len(applications)
            }
        }

    async def generate_ai_insights(self, skills: Dict, preferences: Dict, behavior: Dict, applications: List) -> List[Dict]:
        """
        Generate actionable AI insights from analytics data
        """
        insights_prompt = f"""
        Based on this user's job application analytics, generate 3-5 actionable insights:

        Skills Analysis: {json.dumps(skills, indent=2)}
        Preferences: {json.dumps(preferences, indent=2)}
        Behavior: {json.dumps(behavior, indent=2)}
        Total Applications: {len(applications)}

        Generate insights in these categories:
        1. Skills development (what to learn next)
        2. Application strategy (how to improve approach)
        3. Market positioning (competitive advantages)
        4. Behavioral optimization (timing, targeting)

        Return JSON array of insights:
        [
            {{
                "type": "skill_development",
                "priority": "high",
                "title": "Expand Backend Skills",
                "message": "You're applying mostly to frontend roles but 60% mention full-stack experience...",
                "action": "Learn Node.js and Express to become more competitive",
                "impact": "high"
            }}
        ]
        """

        try:
            response = await self.ai_service.generate_response(insights_prompt)
            insights = json.loads(response)
            return insights if isinstance(insights, list) else []
        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return self.generate_fallback_insights(skills, preferences, behavior)

    def normalize_job_title(self, title: str) -> str:
        """Group similar job titles for better analysis"""
        if not title:
            return "Unknown"

        title_lower = title.lower()

        # Frontend roles
        if any(term in title_lower for term in ['frontend', 'front-end', 'front end', 'ui developer', 'react developer']):
            return 'Frontend Engineer'

        # Backend roles
        elif any(term in title_lower for term in ['backend', 'back-end', 'back end', 'api developer', 'server']):
            return 'Backend Engineer'

        # Full stack roles
        elif any(term in title_lower for term in ['full stack', 'fullstack', 'full-stack']):
            return 'Full Stack Engineer'

        # General software engineering
        elif any(term in title_lower for term in ['software engineer', 'software developer']):
            return 'Software Engineer'

        # Data roles
        elif any(term in title_lower for term in ['data scientist', 'data analyst', 'machine learning']):
            return 'Data Scientist'

        # DevOps roles
        elif any(term in title_lower for term in ['devops', 'site reliability', 'platform engineer']):
            return 'DevOps Engineer'

        # Product roles
        elif any(term in title_lower for term in ['product manager', 'product owner']):
            return 'Product Manager'

        else:
            return title.title()

    async def get_recent_applications(self, user_id: str, days: int = 30) -> List[JobListing]:
        """Get user's recent job applications"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get applications through JobApplication table
        applications = self.db.query(JobListing).join(
            JobApplication, JobListing.id == JobApplication.job_id
        ).filter(
            and_(
                JobApplication.user_id == user_id,
                JobApplication.created_at >= cutoff_date
            )
        ).order_by(desc(JobApplication.created_at)).all()

        return applications

    async def store_analytics(self, user_id: str, analytics_data: Dict, days: int):
        """Store analytics results in database"""
        try:
            # Check if analytics already exist for this user
            existing = self.db.query(UserAnalytics).filter(
                UserAnalytics.user_id == user_id
            ).first()

            if existing:
                # Update existing record
                existing.top_skills = analytics_data.get("skills", {}).get("top_skills", [])
                existing.trending_skills = analytics_data.get("skills", {}).get("trending_skills", [])
                existing.recommended_skills = analytics_data.get("skills", {}).get("recommended_skills", [])
                existing.work_location_preferences = analytics_data.get("preferences", {}).get("work_location", {})
                existing.job_title_distribution = analytics_data.get("preferences", {}).get("job_titles", {})
                existing.ai_insights = analytics_data.get("insights", [])
                existing.application_velocity = analytics_data.get("behavior", {}).get("velocity", {}).get("apps_per_week", 0)
                existing.total_applications_analyzed = analytics_data.get("metadata", {}).get("total_applications", 0)
                existing.last_updated = datetime.utcnow()
                existing.generation_time_seconds = analytics_data.get("metadata", {}).get("generation_time_seconds", 0)
            else:
                # Create new record
                new_analytics = UserAnalytics(
                    user_id=user_id,
                    top_skills=analytics_data.get("skills", {}).get("top_skills", []),
                    trending_skills=analytics_data.get("skills", {}).get("trending_skills", []),
                    recommended_skills=analytics_data.get("skills", {}).get("recommended_skills", []),
                    work_location_preferences=analytics_data.get("preferences", {}).get("work_location", {}),
                    job_title_distribution=analytics_data.get("preferences", {}).get("job_titles", {}),
                    ai_insights=analytics_data.get("insights", []),
                    application_velocity=analytics_data.get("behavior", {}).get("velocity", {}).get("apps_per_week", 0),
                    total_applications_analyzed=analytics_data.get("metadata", {}).get("total_applications", 0),
                    analysis_period_start=datetime.utcnow() - timedelta(days=days),
                    analysis_period_end=datetime.utcnow(),
                    generation_time_seconds=analytics_data.get("metadata", {}).get("generation_time_seconds", 0),
                    ai_confidence_score=85.0  # Default confidence
                )
                self.db.add(new_analytics)

            self.db.commit()
            logger.info(f"Analytics stored successfully for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to store analytics for user {user_id}: {e}")
            self.db.rollback()

    async def update_analytics_cache(self, user_id: str, analytics_data: Dict):
        """Update analytics cache for fast retrieval"""
        try:
            expires_at = datetime.utcnow() + timedelta(days=3)  # Cache for 3 days

            # Check if cache exists
            existing_cache = self.db.query(AnalyticsCache).filter(
                AnalyticsCache.user_id == user_id
            ).first()

            if existing_cache:
                existing_cache.cache_data = analytics_data
                existing_cache.expires_at = expires_at
                existing_cache.last_accessed = datetime.utcnow()
                existing_cache.access_count += 1
            else:
                new_cache = AnalyticsCache(
                    user_id=user_id,
                    cache_data=analytics_data,
                    expires_at=expires_at,
                    cache_size_bytes=len(json.dumps(analytics_data))
                )
                self.db.add(new_cache)

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to update cache for user {user_id}: {e}")
            self.db.rollback()

    async def get_cached_analytics(self, user_id: str) -> Optional[Dict]:
        """Get analytics from cache if available and not expired"""
        try:
            cache = self.db.query(AnalyticsCache).filter(
                and_(
                    AnalyticsCache.user_id == user_id,
                    AnalyticsCache.expires_at > datetime.utcnow()
                )
            ).first()

            if cache:
                cache.access_count += 1
                cache.last_accessed = datetime.utcnow()
                self.db.commit()
                return cache.cache_data

            return None

        except Exception as e:
            logger.error(f"Failed to get cached analytics for user {user_id}: {e}")
            return None

    # Fallback methods for when AI fails
    async def fallback_skills_analysis(self, applications: List[JobListing]) -> Dict:
        """Simple keyword-based skills analysis when AI fails"""
        common_skills = [
            "python", "javascript", "react", "node.js", "sql", "aws", "docker",
            "typescript", "java", "git", "rest api", "mongodb", "postgresql"
        ]

        skill_counts = Counter()
        total_text = ""

        for app in applications:
            text = f"{app.requirements or ''} {app.description or ''}".lower()
            total_text += text
            for skill in common_skills:
                if skill.lower() in text:
                    skill_counts[skill] += 1

        total_apps = len(applications)
        top_skills = [
            {
                "skill": skill,
                "count": count,
                "percentage": round((count / total_apps) * 100, 1),
                "category": "technical"
            }
            for skill, count in skill_counts.most_common(10)
        ]

        return {
            "top_skills": top_skills,
            "trending_skills": ["Docker", "TypeScript", "AWS"],
            "recommended_skills": ["GraphQL", "Next.js", "Kubernetes"],
            "diversity_score": len(skill_counts)
        }

    def generate_fallback_insights(self, skills: Dict, preferences: Dict, behavior: Dict) -> List[Dict]:
        """Generate basic insights when AI fails"""
        insights = []

        # Skills insight
        if skills.get("top_skills"):
            insights.append({
                "type": "skill_development",
                "priority": "medium",
                "title": "Skill Focus Analysis",
                "message": f"Your applications show focus on {skills['top_skills'][0]['skill']} and related technologies.",
                "action": "Consider expanding into complementary technologies",
                "impact": "medium"
            })

        # Application velocity insight
        velocity = behavior.get("velocity", {}).get("apps_per_week", 0)
        if velocity < 3:
            insights.append({
                "type": "behavioral_optimization",
                "priority": "high",
                "title": "Increase Application Volume",
                "message": f"You're applying to {velocity:.1f} jobs per week. Consider increasing your application rate.",
                "action": "Set a goal of 5-7 applications per week",
                "impact": "high"
            })

        return insights

    async def analyze_company_sizes(self, applications: List[JobListing]) -> Dict:
        """Analyze company size preferences from job descriptions"""
        # This would involve AI analysis of company descriptions
        # For now, return placeholder data
        return {
            "startup": {"count": 0, "percentage": 0},
            "mid_size": {"count": 0, "percentage": 0},
            "enterprise": {"count": 0, "percentage": 0}
        }

    async def analyze_salary_ranges(self, applications: List[JobListing]) -> Dict:
        """Extract and analyze salary information"""
        salaries = []

        for app in applications:
            if app.salary_range:
                # Simple regex to extract salary numbers
                numbers = re.findall(r'\$[\d,]+', app.salary_range)
                if len(numbers) >= 2:
                    try:
                        min_salary = int(numbers[0].replace('$', '').replace(',', ''))
                        max_salary = int(numbers[1].replace('$', '').replace(',', ''))
                        salaries.append((min_salary, max_salary))
                    except ValueError:
                        continue

        if not salaries:
            return {"min": None, "max": None, "average": None}

        all_mins = [s[0] for s in salaries]
        all_maxs = [s[1] for s in salaries]

        return {
            "min": min(all_mins),
            "max": max(all_maxs),
            "average": round(sum(all_mins + all_maxs) / len(all_mins + all_maxs)),
            "count": len(salaries)
        }

    async def analyze_market_positioning(self, user_id: str, applications: List[JobListing]) -> Dict:
        """Analyze user's market position and competitiveness"""
        # Placeholder for market analysis
        return {
            "competition_level": "medium",
            "market_demand_score": 75.0,
            "salary_competitiveness": "competitive"
        }

    async def generate_minimal_analytics(self, user_id: str, applications: List[JobListing]) -> Dict:
        """Generate minimal analytics for users with few applications"""
        return {
            "skills": {"message": "Apply to more jobs to get detailed skills analysis"},
            "preferences": {"message": "More application data needed for preference analysis"},
            "behavior": {"message": "Continue applying to build behavioral insights"},
            "insights": [{
                "type": "getting_started",
                "priority": "high",
                "title": "Keep Building Your Application History",
                "message": "Apply to at least 10 jobs to unlock detailed analytics and insights.",
                "action": "Continue applying to jobs that match your interests",
                "impact": "high"
            }],
            "metadata": {
                "user_id": user_id,
                "total_applications": len(applications),
                "analysis_date": datetime.utcnow().isoformat(),
                "status": "insufficient_data"
            }
        }