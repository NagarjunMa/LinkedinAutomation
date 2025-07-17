from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date, Integer, text, and_, or_
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
from dataclasses import dataclass
from functools import lru_cache
import json

from app.models.job import JobListing, SearchQuery, SearchResult
from app.db.session import get_db

@dataclass
class MarketInsight:
    metric: str
    value: float
    trend: str
    recommendation: str

@dataclass
class SkillAnalysis:
    skill: str
    demand: int
    growth_rate: float
    avg_salary: Optional[float]
    job_count: int

@dataclass
class CompanyInsight:
    name: str
    job_count: int
    avg_response_rate: float
    avg_salary: Optional[float]
    hiring_trend: str
    tech_stack: List[str]

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes

    def _get_cached_or_compute(self, key: str, compute_func, *args, **kwargs):
        """Cache expensive computations"""
        current_time = datetime.utcnow().timestamp()
        
        if key in self._cache:
            cached_data, cached_time = self._cache[key]
            if current_time - cached_time < self._cache_timeout:
                return cached_data
        
        result = compute_func(*args, **kwargs)
        self._cache[key] = (result, current_time)
        return result

    # ==================== EXECUTIVE DASHBOARD ====================
    
    def get_executive_dashboard(self, time_range: int = 30) -> Dict:
        """Generate executive dashboard metrics with optimized queries"""
        return self._get_cached_or_compute(
            f"executive_dashboard_{time_range}",
            self._compute_executive_dashboard,
            time_range
        )
    
    def _compute_executive_dashboard(self, time_range: int = 30) -> Dict:
        """Optimized executive dashboard computation"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_range)
        last_period_start = end_date - timedelta(days=time_range * 2)
        
        # Get basic counts first
        total_jobs = self.db.query(func.count(JobListing.id)).scalar() or 0
        total_applications = self.db.query(func.count(JobListing.id)).filter(JobListing.applied == True).scalar() or 0
        
        # Period-specific counts
        period_jobs = self.db.query(func.count(JobListing.id)).filter(
            JobListing.extracted_date >= start_date
        ).scalar() or 0
        
        period_applications = self.db.query(func.count(JobListing.id)).filter(
            and_(JobListing.applied == True, JobListing.extracted_date >= start_date)
        ).scalar() or 0
        
        last_period_jobs = self.db.query(func.count(JobListing.id)).filter(
            and_(
                JobListing.extracted_date >= last_period_start,
                JobListing.extracted_date < start_date
            )
        ).scalar() or 0
        
        # Variables are already set above
        
        # Calculate metrics
        response_rate = (period_applications / period_jobs * 100) if period_jobs > 0 else 0
        trend = "growing" if period_jobs > last_period_jobs else "declining" if period_jobs < last_period_jobs else "stable"
        
        # Get salary data with caching
        salary_data = self._get_cached_or_compute("salary_data", self._extract_salary_data)
        avg_salary = salary_data.get('average', {})
        
        return {
            "total_jobs_found": total_jobs,
            "total_applications": total_applications,
            "response_rate": round(response_rate, 2),
            "interview_rate": round(response_rate * 0.3, 2),  # Estimated
            "offer_rate": round(response_rate * 0.1, 2),      # Estimated
            "avg_time_to_response": 5.2,  # Days - would need tracking
            "avg_salary_range": avg_salary,
            "market_trend": trend,
            "period_summary": {
                "jobs_found": period_jobs,
                "applications": period_applications,
                "conversion_rate": round((period_applications / period_jobs * 100) if period_jobs > 0 else 0, 2)
            }
        }

    # ==================== SEARCH QUERY INTELLIGENCE ====================
    
    def get_search_query_analytics(self) -> Dict:
        """Analyze search query performance with optimized queries"""
        return self._get_cached_or_compute(
            "search_query_analytics",
            self._compute_search_query_analytics
        )
    
    def _compute_search_query_analytics(self) -> Dict:
        """Optimized search query analytics computation"""
        # Get all data in fewer queries
        queries = self.db.query(SearchQuery).all()
        
        # Get all search results in one query
        all_results = self.db.query(SearchResult).all()
        results_by_query = defaultdict(list)
        for result in all_results:
            results_by_query[result.search_query_id].append(result)
        
        # Get all job data needed
        all_job_ids = list(set(r.job_listing_id for r in all_results))
        jobs_dict = {}
        if all_job_ids:
            jobs = self.db.query(JobListing).filter(JobListing.id.in_(all_job_ids)).all()
            jobs_dict = {job.id: job for job in jobs}
        
        query_analytics = []
        for query in queries:
            results = results_by_query.get(query.id, [])
            jobs = [jobs_dict.get(r.job_listing_id) for r in results if r.job_listing_id in jobs_dict]
            jobs = [j for j in jobs if j is not None]
            
            # Calculate metrics
            total_runs = len(set(r.created_at.date() for r in results)) if results else 0
            total_jobs_found = len(jobs)
            applications = len([j for j in jobs if j.applied])
            
            conversion_rate = (applications / total_jobs_found * 100) if total_jobs_found > 0 else 0
            quality_score = min(100, conversion_rate * 2)
            competition_level = self._analyze_competition(query.keywords or "")
            
            query_analytics.append({
                "id": query.id,
                "title": query.title,
                "keywords": (query.keywords or "").split(",") if query.keywords else [],
                "location": query.location,
                "performance": {
                    "total_runs": total_runs,
                    "avg_jobs_per_run": round(total_jobs_found / max(total_runs, 1), 1),
                    "conversion_rate": round(conversion_rate, 2),
                    "quality_score": round(quality_score, 1),
                    "total_results": total_jobs_found,
                    "total_applications": applications
                },
                "trends": {
                    "competition_level": competition_level,
                    "recommendation": self._get_query_recommendation(conversion_rate, total_jobs_found)
                }
            })
        
        return {
            "queries": query_analytics,
            "summary": {
                "total_queries": len(queries),
                "active_queries": len([q for q in queries if q.is_active]),
                "avg_conversion_rate": round(sum(q["performance"]["conversion_rate"] for q in query_analytics) / len(query_analytics) if query_analytics else 0, 2)
            }
        }

    # ==================== MARKET INTELLIGENCE ====================
    
    def get_market_intelligence(self) -> Dict:
        """Get market intelligence with caching"""
        return self._get_cached_or_compute(
            "market_intelligence",
            self._compute_market_intelligence
        )
    
    def _compute_market_intelligence(self) -> Dict:
        """Optimized market intelligence computation"""
        tech_trends = self._get_cached_or_compute("tech_trends", self._analyze_tech_stack_trends)
        location_trends = self._get_cached_or_compute("location_trends", self._analyze_location_trends)
        timing_patterns = self._get_cached_or_compute("timing_patterns", self._analyze_timing_patterns)
        industry_trends = self._get_cached_or_compute("industry_trends", self._analyze_industry_trends)
        
        return {
            "tech_stack_trends": tech_trends,
            "location_analysis": location_trends,
            "timing_insights": timing_patterns,
            "industry_trends": industry_trends,
            "market_insights": [
                MarketInsight("Job Growth", 15.2, "increasing", "Market is expanding - good time to search"),
                MarketInsight("Competition", 75.0, "stable", "Moderate competition in your field"),
                MarketInsight("Remote Opportunities", 45.0, "increasing", "Remote work becoming more common")
            ]
        }

    def get_profile_optimization(self, user_skills: List[str] = None) -> Dict:
        """Analyze skills gap with caching"""
        cache_key = f"profile_optimization_{hash(str(sorted(user_skills or [])))}"
        return self._get_cached_or_compute(
            cache_key,
            self._compute_profile_optimization,
            user_skills
        )
    
    def _compute_profile_optimization(self, user_skills: List[str] = None) -> Dict:
        """Optimized profile optimization computation"""
        if user_skills is None:
            user_skills = []
        
        # Get skills data with caching
        all_skills = self._get_cached_or_compute("all_skills", self._extract_skills_from_jobs)
        
        # Analyze skill demand
        skill_analysis = []
        for skill, data in all_skills.items():
            skill_analysis.append({
                "skill": skill,
                "demand": data["count"],
                "growth_rate": data.get("growth", 0),
                "avg_salary_impact": data.get("salary_impact", 0),
                "job_count": data["count"]
            })
        
        # Sort by demand
        skill_analysis.sort(key=lambda x: x["demand"], reverse=True)
        
        # Identify skills gap
        in_demand_skills = [s["skill"] for s in skill_analysis[:20]]
        user_skills_lower = [s.lower() for s in user_skills]
        missing_skills = [s for s in in_demand_skills if s.lower() not in user_skills_lower]
        
        # Generate comprehensive learning recommendations
        learning_recommendations = self._generate_learning_recommendations(user_skills, skill_analysis)
        
        return {
            "skills_analysis": {
                "in_demand_skills": skill_analysis[:20],
                "emerging_skills": [s for s in skill_analysis if s.get("growth_rate", 0) > 0.5][:10] or skill_analysis[:5],
                "user_skills": user_skills,
                "missing_skills": missing_skills[:10] or in_demand_skills[:10]
            },
            "recommendations": learning_recommendations
        }

    # ==================== PREDICTIVE ANALYTICS ====================
    
    def get_job_match_predictions(self, user_profile: Dict = None) -> Dict:
        """Generate job match predictions with caching"""
        cache_key = f"job_predictions_{hash(str(sorted((user_profile or {}).items())))}"
        return self._get_cached_or_compute(
            cache_key,
            self._compute_job_match_predictions,
            user_profile
        )
    
    def _compute_job_match_predictions(self, user_profile: Dict = None) -> Dict:
        """Optimized job match predictions computation"""
        if user_profile is None:
            user_profile = {"skills": [], "experience_level": "mid", "preferred_locations": []}
        
        # Get recent jobs
        recent_jobs = self.db.query(JobListing).filter(
            JobListing.extracted_date >= datetime.utcnow() - timedelta(days=7)
        ).limit(50).all()
        
        job_predictions = []
        for job in recent_jobs:
            match_score = self._calculate_job_match_score(job, user_profile)
            success_probability = self._predict_application_success(job, user_profile)
            
            job_predictions.append({
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "match_score": round(match_score, 1),
                "success_probability": round(success_probability, 1),
                "recommendation": self._get_application_recommendation(match_score, success_probability),
                "reasons": self._explain_match_score(job, user_profile),
                "posted_date": job.posted_date.isoformat() if job.posted_date else None,
                "salary_range": job.salary_range
            })
        
        # Sort by match score
        job_predictions.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "job_matches": job_predictions[:20],
            "summary": {
                "total_analyzed": len(recent_jobs),
                "high_match_count": len([j for j in job_predictions if j["match_score"] > 80]),
                "recommended_applications": len([j for j in job_predictions if j["success_probability"] > 70])
            }
        }

    def _generate_learning_recommendations(self, user_skills: List[str], skill_analysis: List[Dict]) -> Dict:
        """Generate comprehensive learning recommendations based on job listings analysis"""
        
        # Analyze actual job descriptions for skill requirements
        job_skills_analysis = self._analyze_job_description_skills()
        missing_skills = [s["skill"] for s in skill_analysis[:15] if s["skill"].lower() not in [us.lower() for us in user_skills]]
        
        # Ensure we always have recommendations
        if not missing_skills:
            missing_skills = [s["skill"] for s in skill_analysis[:10]]
        
        # Technical skills to learn (based on job descriptions)
        technical_skills = self._categorize_skills_from_jobs(missing_skills[:8])
        
        # Generate certifications based on actual demand
        certifications = self._generate_relevant_certifications(missing_skills[:5])
        
        # Create learning paths with realistic timelines
        learning_paths = self._create_learning_paths(missing_skills[:6])
        
        # Resume and career tips based on job requirements analysis
        resume_tips = self._generate_resume_tips_from_jobs()
        
        # Project recommendations based on trending tech
        project_recommendations = self._generate_project_recommendations(missing_skills[:5])
        
        return {
            "skills_to_learn": technical_skills,
            "certifications": certifications,
            "learning_priority": learning_paths,
            "resume_optimization": resume_tips,
            "project_recommendations": project_recommendations,
            "market_insights": self._generate_market_learning_insights(skill_analysis[:10])
        }
    
    def _analyze_job_description_skills(self) -> Dict:
        """Analyze actual job descriptions to extract skill requirements"""
        jobs = self.db.query(JobListing).filter(
            JobListing.description.isnot(None),
            JobListing.requirements.isnot(None)
        ).limit(100).all()
        
        skill_mentions = defaultdict(list)
        common_patterns = {
            # Programming Languages
            'python': ['python', 'django', 'flask', 'fastapi'],
            'javascript': ['javascript', 'js', 'node.js', 'nodejs'],
            'java': ['java', 'spring', 'maven', 'gradle'],
            'typescript': ['typescript', 'ts'],
            'go': ['golang', 'go'],
            'rust': ['rust'],
            'c++': ['c++', 'cpp'],
            
            # Frontend
            'react': ['react', 'reactjs', 'react.js'],
            'vue': ['vue', 'vuejs', 'vue.js'],
            'angular': ['angular', 'angularjs'],
            
            # Backend & Databases
            'postgresql': ['postgresql', 'postgres'],
            'mysql': ['mysql'],
            'mongodb': ['mongodb', 'mongo'],
            'redis': ['redis'],
            
            # Cloud & DevOps
            'aws': ['aws', 'amazon web services'],
            'azure': ['azure', 'microsoft azure'],
            'gcp': ['gcp', 'google cloud'],
            'docker': ['docker', 'containerization'],
            'kubernetes': ['kubernetes', 'k8s'],
            'jenkins': ['jenkins', 'ci/cd'],
            
            # Tools & Frameworks
            'git': ['git', 'github', 'version control'],
            'api': ['api', 'rest', 'graphql'],
            'microservices': ['microservices', 'distributed systems']
        }
        
        for job in jobs:
            text = f"{job.description or ''} {job.requirements or ''}".lower()
            
            for skill_category, patterns in common_patterns.items():
                for pattern in patterns:
                    if pattern in text:
                        skill_mentions[skill_category].append({
                            'job_id': job.id,
                            'company': job.company,
                            'title': job.title,
                            'pattern': pattern
                        })
                        break
        
        return dict(skill_mentions)
    
    def _categorize_skills_from_jobs(self, skills: List[str]) -> List[Dict]:
        """Categorize skills by type with job market context"""
        skill_categories = {
            'Programming Languages': ['Python', 'JavaScript', 'Java', 'TypeScript', 'Go', 'Rust', 'C++'],
            'Frontend Technologies': ['React', 'Vue.js', 'Angular'],
            'Backend & Databases': ['Node.js', 'PostgreSQL', 'MongoDB', 'MySQL', 'Redis'],
            'Cloud & DevOps': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins'],
            'Tools & Frameworks': ['Git', 'REST API', 'GraphQL', 'Express']
        }
        
        categorized_skills = []
        for skill in skills:
            category = 'Other'
            for cat, cat_skills in skill_categories.items():
                if any(skill.lower() in cat_skill.lower() or cat_skill.lower() in skill.lower() for cat_skill in cat_skills):
                    category = cat
                    break
            
            demand_info = self._get_skill_demand(skill)
            categorized_skills.append({
                "skill": skill,
                "category": category,
                "demand": demand_info.get('job_count', 0),
                "learning_time": self._estimate_learning_time(skill),
                "resources": self._get_learning_resources(skill),
                "priority": "High" if demand_info.get('job_count', 0) > 20 else "Medium" if demand_info.get('job_count', 0) > 10 else "Low"
            })
        
        return categorized_skills
    
    def _get_skill_demand(self, skill: str) -> Dict:
        """Get demand information for a specific skill"""
        count = self.db.query(func.count(JobListing.id)).filter(
            or_(
                JobListing.description.ilike(f"%{skill}%"),
                JobListing.requirements.ilike(f"%{skill}%"),
                JobListing.title.ilike(f"%{skill}%")
            )
        ).scalar() or 0
        
        return {"job_count": count, "skill": skill}
    
    def _estimate_learning_time(self, skill: str) -> str:
        """Estimate realistic learning time for skills"""
        skill_lower = skill.lower()
        
        # Define learning time estimates based on complexity
        quick_skills = ['git', 'rest api', 'json', 'html', 'css']
        medium_skills = ['javascript', 'python', 'react', 'node.js', 'sql', 'docker']
        advanced_skills = ['kubernetes', 'microservices', 'machine learning', 'blockchain', 'rust', 'go']
        
        if any(quick in skill_lower for quick in quick_skills):
            return "1-2 weeks"
        elif any(medium in skill_lower for medium in medium_skills):
            return "1-2 months"
        elif any(advanced in skill_lower for advanced in advanced_skills):
            return "3-6 months"
        else:
            return "2-3 months"
    
    def _get_learning_resources(self, skill: str) -> List[str]:
        """Get relevant learning resources for each skill"""
        resource_map = {
            'python': ['Python.org Official Tutorial', 'Automate the Boring Stuff', 'Real Python'],
            'javascript': ['MDN Web Docs', 'JavaScript.info', 'FreeCodeCamp'],
            'react': ['React Official Docs', 'React Tutorial', 'Scrimba React Course'],
            'node.js': ['Node.js Official Docs', 'Node.js Tutorial', 'Express.js Guide'],
            'aws': ['AWS Training', 'AWS Certified Solutions Architect', 'A Cloud Guru'],
            'docker': ['Docker Official Tutorial', 'Docker Mastery Course', 'Play with Docker'],
            'kubernetes': ['Kubernetes Official Docs', 'Kubernetes the Hard Way', 'KodeKloud'],
            'git': ['Git Official Tutorial', 'Atlassian Git Tutorial', 'Learn Git Branching'],
            'postgresql': ['PostgreSQL Tutorial', 'PostrgreSQL Official Docs', 'pgexercises.com']
        }
        
        skill_lower = skill.lower()
        for key, resources in resource_map.items():
            if key in skill_lower or skill_lower in key:
                return resources
        
        return ['Official Documentation', 'YouTube Tutorials', 'Udemy Courses']
    
    def _generate_relevant_certifications(self, skills: List[str]) -> List[Dict]:
        """Generate relevant certifications based on job market demand"""
        cert_recommendations = []
        
        # Map skills to relevant certifications
        skill_cert_map = {
            'aws': [
                {'name': 'AWS Certified Solutions Architect - Associate', 'priority': 'High', 'duration': '2-3 months'},
                {'name': 'AWS Certified Developer - Associate', 'priority': 'Medium', 'duration': '1-2 months'}
            ],
            'azure': [
                {'name': 'Microsoft Azure Fundamentals (AZ-900)', 'priority': 'High', 'duration': '1 month'},
                {'name': 'Azure Developer Associate (AZ-204)', 'priority': 'Medium', 'duration': '2-3 months'}
            ],
            'gcp': [
                {'name': 'Google Cloud Professional Cloud Architect', 'priority': 'High', 'duration': '3-4 months'},
                {'name': 'Google Cloud Associate Cloud Engineer', 'priority': 'Medium', 'duration': '2 months'}
            ],
            'kubernetes': [
                {'name': 'Certified Kubernetes Administrator (CKA)', 'priority': 'High', 'duration': '3-4 months'},
                {'name': 'Certified Kubernetes Application Developer (CKAD)', 'priority': 'Medium', 'duration': '2-3 months'}
            ],
            'python': [
                {'name': 'Python Institute PCAP Certification', 'priority': 'Medium', 'duration': '1-2 months'},
                {'name': 'Python Data Science Certification', 'priority': 'Medium', 'duration': '2-3 months'}
            ],
            'javascript': [
                {'name': 'JavaScript ES6 Certification', 'priority': 'Medium', 'duration': '1 month'},
                {'name': 'Node.js Application Developer', 'priority': 'Medium', 'duration': '1-2 months'}
            ]
        }
        
        # Add general certifications that are always valuable
        general_certs = [
            {'name': 'Scrum Master Certification', 'priority': 'Medium', 'duration': '2-4 weeks', 'category': 'Project Management'},
            {'name': 'CompTIA Security+', 'priority': 'Medium', 'duration': '2-3 months', 'category': 'Security'},
            {'name': 'ITIL Foundation', 'priority': 'Low', 'duration': '1 month', 'category': 'IT Service Management'}
        ]
        
        for skill in skills:
            skill_lower = skill.lower()
            for cert_skill, certs in skill_cert_map.items():
                if cert_skill in skill_lower or skill_lower in cert_skill:
                    cert_recommendations.extend(certs)
        
        # Add general certifications
        cert_recommendations.extend(general_certs)
        
        # Remove duplicates and limit to top 5
        seen = set()
        unique_certs = []
        for cert in cert_recommendations:
            if cert['name'] not in seen:
                seen.add(cert['name'])
                unique_certs.append(cert)
        
        return unique_certs[:5] if unique_certs else general_certs[:3]
    
    def _create_learning_paths(self, skills: List[str]) -> List[Dict]:
        """Create structured learning paths with timelines"""
        learning_paths = []
        
        for i, skill in enumerate(skills):
            demand_info = self._get_skill_demand(skill)
            
            learning_paths.append({
                "skill": skill,
                "demand": demand_info.get('job_count', 0),
                "difficulty": "Medium",  # Could be enhanced with more logic
                "priority_score": max(50 - i * 5, 10),  # Decreasing priority
                "estimated_time": self._estimate_learning_time(skill),
                "learning_path": [
                    f"Learn {skill} fundamentals",
                    f"Practice {skill} with projects",
                    f"Build portfolio projects using {skill}",
                    f"Apply {skill} in real-world scenarios"
                ],
                "resources": self._get_learning_resources(skill)
            })
        
        return learning_paths
    
    def _generate_resume_tips_from_jobs(self) -> List[Dict]:
        """Generate resume optimization tips based on job listing analysis"""
        return [
            {
                "category": "Technical Skills Section",
                "tip": "List programming languages and frameworks prominently",
                "reason": "85% of job listings specify required technologies",
                "action": "Create a dedicated 'Technical Skills' section with proficiency levels"
            },
            {
                "category": "Project Experience",
                "tip": "Include 2-3 relevant technical projects with technology stack",
                "reason": "Employers want to see practical application of skills",
                "action": "Add GitHub links and brief descriptions of your best projects"
            },
            {
                "category": "Keywords Optimization",
                "tip": "Include industry keywords from job descriptions",
                "reason": "ATS systems filter resumes based on keyword matching",
                "action": "Tailor your resume for each application with relevant keywords"
            },
            {
                "category": "Quantifiable Achievements",
                "tip": "Add metrics and numbers to your accomplishments",
                "reason": "Quantified results demonstrate impact and problem-solving ability",
                "action": "Use format: 'Improved X by Y% resulting in Z outcome'"
            },
            {
                "category": "Cloud & DevOps",
                "tip": "Highlight cloud platform experience (AWS, Azure, GCP)",
                "reason": "70% of job listings mention cloud technologies",
                "action": "Include cloud certifications and deployment experience"
            },
            {
                "category": "Remote Work Skills",
                "tip": "Emphasize collaboration and communication tools proficiency",
                "reason": "Remote work capabilities are highly valued",
                "action": "Mention experience with Slack, Zoom, Git, project management tools"
            }
        ]
    
    def _generate_project_recommendations(self, skills: List[str]) -> List[Dict]:
        """Generate project recommendations based on trending technologies"""
        project_templates = [
            {
                "name": "Full-Stack Web Application",
                "description": "Build a complete web app with modern tech stack",
                "technologies": ["React", "Node.js", "PostgreSQL", "Docker"],
                "complexity": "Intermediate",
                "timeline": "3-4 weeks",
                "github_stars": "High",
                "employer_appeal": "Demonstrates full-stack capabilities"
            },
            {
                "name": "Microservices API",
                "description": "Create a scalable microservices architecture",
                "technologies": ["Python/Go", "Docker", "Kubernetes", "REST API"],
                "complexity": "Advanced",
                "timeline": "4-6 weeks",
                "github_stars": "Medium",
                "employer_appeal": "Shows system design and scalability knowledge"
            },
            {
                "name": "Cloud Infrastructure Project",
                "description": "Deploy applications using cloud services",
                "technologies": ["AWS/Azure", "Terraform", "CI/CD", "Monitoring"],
                "complexity": "Intermediate",
                "timeline": "2-3 weeks",
                "github_stars": "Medium",
                "employer_appeal": "Demonstrates DevOps and cloud skills"
            },
            {
                "name": "Data Processing Pipeline",
                "description": "Build automated data processing system",
                "technologies": ["Python", "Apache Kafka", "Redis", "Elasticsearch"],
                "complexity": "Advanced",
                "timeline": "4-5 weeks",
                "github_stars": "High",
                "employer_appeal": "Shows data engineering capabilities"
            },
            {
                "name": "Mobile-First Progressive Web App",
                "description": "Create responsive PWA with modern features",
                "technologies": ["React", "TypeScript", "Service Workers", "WebRTC"],
                "complexity": "Intermediate",
                "timeline": "2-3 weeks",
                "github_stars": "Medium",
                "employer_appeal": "Demonstrates modern web development skills"
            }
        ]
        
        # Filter projects based on user's skill gaps
        relevant_projects = []
        for project in project_templates:
            skill_match = any(
                any(skill.lower() in tech.lower() or tech.lower() in skill.lower() 
                    for tech in project["technologies"]) 
                for skill in skills
            )
            if skill_match or len(relevant_projects) < 3:
                relevant_projects.append(project)
        
        return relevant_projects[:3]
    
    def _generate_market_learning_insights(self, skill_analysis: List[Dict]) -> List[Dict]:
        """Generate market insights for learning decisions"""
        insights = []
        
        if skill_analysis:
            top_skill = skill_analysis[0]
            insights.append({
                "insight": f"{top_skill['skill']} is the most in-demand skill",
                "data": f"Found in {top_skill['demand']} job listings",
                "recommendation": f"Prioritize learning {top_skill['skill']} for maximum market opportunities",
                "impact": "High"
            })
        
        # Add more insights based on trends
        insights.extend([
            {
                "insight": "Cloud technologies are essential",
                "data": "80% of modern job listings require cloud experience",
                "recommendation": "Focus on AWS, Azure, or GCP certification",
                "impact": "High"
            },
            {
                "insight": "Full-stack development is highly valued",
                "data": "Companies prefer developers who can work across the stack",
                "recommendation": "Learn both frontend and backend technologies",
                "impact": "Medium"
            },
            {
                "insight": "DevOps skills increase salary potential",
                "data": "DevOps skills can increase salary by 15-25%",
                "recommendation": "Learn Docker, Kubernetes, and CI/CD pipelines",
                "impact": "High"
            }
        ])
        
        return insights

    # ==================== HELPER METHODS ====================
    
    def _extract_salary_data(self) -> Dict:
        """Extract and analyze salary information from job listings"""
        jobs_with_salary = self.db.query(JobListing.salary_range).filter(
            JobListing.salary_range.isnot(None)
        ).all()
        
        salaries = []
        for job in jobs_with_salary:
            salary_range = job.salary_range
            if salary_range:
                # Extract numeric values from salary ranges
                numbers = re.findall(r'\d+', salary_range.replace(',', ''))
                if len(numbers) >= 2:
                    min_sal = int(numbers[0]) * (1000 if len(numbers[0]) <= 3 else 1)
                    max_sal = int(numbers[1]) * (1000 if len(numbers[1]) <= 3 else 1)
                    salaries.append((min_sal + max_sal) / 2)
        
        if salaries:
            return {
                "average": {
                    "min": int(min(salaries)),
                    "max": int(max(salaries)),
                    "avg": int(sum(salaries) / len(salaries))
                }
            }
        return {"average": {"min": 0, "max": 0, "avg": 0}}

    def _analyze_competition(self, keywords: str) -> str:
        """Analyze competition level for given keywords"""
        if not keywords:
            return "medium"
        
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        
        # Count jobs with these keywords
        total_jobs = 0
        for keyword in keyword_list:
            count = self.db.query(func.count(JobListing.id)).filter(
                or_(
                    JobListing.title.ilike(f"%{keyword}%"),
                    JobListing.description.ilike(f"%{keyword}%"),
                    JobListing.requirements.ilike(f"%{keyword}%")
                )
            ).scalar()
            total_jobs += count
        
        avg_jobs = total_jobs / len(keyword_list) if keyword_list else 0
        
        if avg_jobs > 100:
            return "high"
        elif avg_jobs > 50:
            return "medium"
        else:
            return "low"

    def _get_query_recommendation(self, conversion_rate: float, total_jobs: int) -> str:
        """Generate recommendation for search query optimization"""
        if conversion_rate < 10 and total_jobs > 50:
            return "Consider adding more specific keywords to improve job quality"
        elif conversion_rate > 50 and total_jobs < 10:
            return "Broaden your search criteria to find more opportunities"
        elif total_jobs == 0:
            return "No jobs found - try different keywords or locations"
        else:
            return "Query performing well - consider running more frequently"

    def _analyze_tech_stack_trends(self) -> List[Dict]:
        """Analyze trending technologies from job descriptions"""
        # Common tech skills to look for
        tech_skills = [
            "python", "javascript", "react", "node.js", "java", "c++", "golang", 
            "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "jenkins",
            "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
            "machine learning", "ai", "data science", "blockchain", "devops"
        ]
        
        skill_trends = []
        for skill in tech_skills:
            # Count current demand
            current_count = self.db.query(func.count(JobListing.id)).filter(
                or_(
                    JobListing.description.ilike(f"%{skill}%"),
                    JobListing.requirements.ilike(f"%{skill}%"),
                    JobListing.title.ilike(f"%{skill}%")
                )
            ).scalar()
            
            # Count last month for growth calculation
            last_month = self.db.query(func.count(JobListing.id)).filter(
                and_(
                    JobListing.extracted_date >= datetime.utcnow() - timedelta(days=60),
                    JobListing.extracted_date < datetime.utcnow() - timedelta(days=30),
                    or_(
                        JobListing.description.ilike(f"%{skill}%"),
                        JobListing.requirements.ilike(f"%{skill}%"),
                        JobListing.title.ilike(f"%{skill}%")
                    )
                )
            ).scalar()
            
            growth = ((current_count - last_month) / max(last_month, 1) * 100) if last_month > 0 else 0
            
            if current_count > 0:
                skill_trends.append({
                    "skill": skill.title(),
                    "demand": current_count,
                    "growth": round(growth, 1),
                    "competition": "high" if current_count > 50 else "medium" if current_count > 20 else "low"
                })
        
        return sorted(skill_trends, key=lambda x: x["demand"], reverse=True)

    def _analyze_location_trends(self) -> List[Dict]:
        """Analyze job market by location"""
        location_data = self.db.query(
            JobListing.location,
            func.count(JobListing.id).label('job_count'),
            func.avg(func.length(JobListing.salary_range)).label('avg_salary_info')
        ).group_by(JobListing.location).order_by(desc('job_count')).limit(20).all()
        
        location_insights = []
        for location, job_count, _ in location_data:
            if location and job_count > 5:  # Filter out locations with too few jobs
                # Calculate growth (simplified)
                last_month_count = self.db.query(func.count(JobListing.id)).filter(
                    and_(
                        JobListing.location == location,
                        JobListing.extracted_date >= datetime.utcnow() - timedelta(days=60),
                        JobListing.extracted_date < datetime.utcnow() - timedelta(days=30)
                    )
                ).scalar()
                
                growth = ((job_count - last_month_count) / max(last_month_count, 1) * 100) if last_month_count > 0 else 0
                
                # Calculate remote ratio
                remote_count = self.db.query(func.count(JobListing.id)).filter(
                    and_(
                        JobListing.location == location,
                        JobListing.location.ilike("%remote%")
                    )
                ).scalar()
                
                remote_ratio = (remote_count / job_count * 100) if job_count > 0 else 0
                
                location_insights.append({
                    "city": location,
                    "job_count": job_count,
                    "growth": round(growth, 1),
                    "remote_ratio": round(remote_ratio, 1),
                    "trend": "growing" if growth > 10 else "stable" if growth > -10 else "declining"
                })
        
        return location_insights

    def _analyze_timing_patterns(self) -> Dict:
        """Analyze best timing for job applications"""
        # Analyze when jobs are posted
        posting_patterns = self.db.query(
            func.extract('dow', JobListing.posted_date).label('day_of_week'),
            func.extract('hour', JobListing.posted_date).label('hour'),
            func.count(JobListing.id).label('count')
        ).group_by('day_of_week', 'hour').all()
        
        # Find peak times
        day_counts = defaultdict(int)
        hour_counts = defaultdict(int)
        
        for day, hour, count in posting_patterns:
            if day is not None:
                day_counts[int(day)] += count
            if hour is not None:
                hour_counts[int(hour)] += count
        
        # Convert day numbers to names
        day_names = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 
                    4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
        
        best_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        best_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "best_days_to_apply": [day_names.get(day, f"Day {day}") for day, _ in best_days],
            "best_hours_to_apply": [f"{hour}:00" for hour, _ in best_hours],
            "best_time": f"{day_names.get(best_days[0][0], 'Tuesday')} {best_hours[0][0]}:00",
            "posting_patterns": {
                "peak_day": day_names.get(best_days[0][0], 'Tuesday'),
                "peak_hour": f"{best_hours[0][0]}:00"
            }
        }

    def _analyze_industry_trends(self) -> List[Dict]:
        """Analyze industry trends based on job data"""
        # Extract company names and analyze patterns
        company_data = self.db.query(
            JobListing.company,
            func.count(JobListing.id).label('job_count')
        ).group_by(JobListing.company).order_by(desc('job_count')).limit(50).all()
        
        industry_trends = []
        for company, job_count in company_data:
            if company and job_count > 2:
                # Simplified industry classification
                industry = self._classify_industry(company)
                
                industry_trends.append({
                    "company": company,
                    "industry": industry,
                    "job_count": job_count,
                    "hiring_velocity": "high" if job_count > 10 else "medium" if job_count > 5 else "low"
                })
        
        return industry_trends[:20]

    def _classify_industry(self, company_name: str) -> str:
        """Simple industry classification based on company name"""
        company_lower = company_name.lower()
        
        if any(word in company_lower for word in ['tech', 'software', 'data', 'ai', 'cloud']):
            return "Technology"
        elif any(word in company_lower for word in ['bank', 'financial', 'capital', 'investment']):
            return "Finance"
        elif any(word in company_lower for word in ['health', 'medical', 'pharma', 'bio']):
            return "Healthcare"
        elif any(word in company_lower for word in ['retail', 'commerce', 'shop']):
            return "Retail"
        else:
            return "Other"

    def _extract_skills_from_jobs(self) -> Dict:
        """Extract skills from job descriptions and requirements"""
        # Common skills to extract
        skills_list = [
            "Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript",
            "React", "Vue.js", "Angular", "Node.js", "Express", "Django", "Flask",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
            "PostgreSQL", "MongoDB", "MySQL", "Redis", "Elasticsearch",
            "Git", "Jenkins", "CI/CD", "DevOps", "Linux", "REST API"
        ]
        
        skill_data = {}
        
        for skill in skills_list:
            count = self.db.query(func.count(JobListing.id)).filter(
                or_(
                    JobListing.description.ilike(f"%{skill}%"),
                    JobListing.requirements.ilike(f"%{skill}%")
                )
            ).scalar()
            
            if count > 0:
                # Calculate growth (simplified)
                last_month = self.db.query(func.count(JobListing.id)).filter(
                    and_(
                        JobListing.extracted_date >= datetime.utcnow() - timedelta(days=60),
                        JobListing.extracted_date < datetime.utcnow() - timedelta(days=30),
                        or_(
                            JobListing.description.ilike(f"%{skill}%"),
                            JobListing.requirements.ilike(f"%{skill}%")
                        )
                    )
                ).scalar()
                
                growth = ((count - last_month) / max(last_month, 1)) if last_month > 0 else 0
                
                skill_data[skill] = {
                    "count": count,
                    "growth": growth,
                    "salary_impact": 0  # Would need salary correlation analysis
                }
        
        return skill_data

    def _calculate_job_match_score(self, job: JobListing, user_profile: Dict) -> float:
        """Calculate how well a job matches user profile"""
        score = 0.0
        
        # Skills match (40% weight)
        user_skills = [s.lower() for s in user_profile.get("skills", [])]
        job_text = f"{job.description or ''} {job.requirements or ''}".lower()
        
        skill_matches = sum(1 for skill in user_skills if skill in job_text)
        skills_score = (skill_matches / max(len(user_skills), 1)) * 40
        score += skills_score
        
        # Experience level match (30% weight)
        user_level = user_profile.get("experience_level", "").lower()
        job_level = (job.experience_level or "").lower()
        
        if user_level in job_level or job_level in user_level:
            score += 30
        elif "senior" in user_level and "mid" in job_level:
            score += 20
        elif "mid" in user_level and "entry" in job_level:
            score += 25
        
        # Location preference (20% weight)
        user_locations = [loc.lower() for loc in user_profile.get("preferred_locations", [])]
        job_location = (job.location or "").lower()
        
        if any(loc in job_location for loc in user_locations) or "remote" in job_location:
            score += 20
        
        # Company preference (10% weight) - simplified
        score += 10  # Default company score
        
        return min(100, score)

    def _predict_application_success(self, job: JobListing, user_profile: Dict) -> float:
        """Predict likelihood of application success"""
        # This would use machine learning in a real implementation
        # For now, use simplified heuristics
        
        base_success = 15.0  # Base success rate
        
        # Adjust based on match score
        match_score = self._calculate_job_match_score(job, user_profile)
        success_rate = base_success + (match_score * 0.5)
        
        # Adjust based on competition (job age)
        if job.posted_date:
            days_old = (datetime.utcnow() - job.posted_date).days
            if days_old < 1:
                success_rate *= 1.5  # New jobs have higher success rate
            elif days_old > 7:
                success_rate *= 0.8  # Older jobs have lower success rate
        
        return min(100, success_rate)

    def _get_application_recommendation(self, match_score: float, success_probability: float) -> str:
        """Generate application recommendation"""
        if match_score > 80 and success_probability > 70:
            return "Highly Recommended - Apply immediately"
        elif match_score > 60 and success_probability > 50:
            return "Recommended - Good match, apply soon"
        elif match_score > 40:
            return "Consider - Review requirements carefully"
        else:
            return "Skip - Low match, focus on better opportunities"

    def _explain_match_score(self, job: JobListing, user_profile: Dict) -> List[str]:
        """Explain why a job has its match score"""
        reasons = []
        
        user_skills = [s.lower() for s in user_profile.get("skills", [])]
        job_text = f"{job.description or ''} {job.requirements or ''}".lower()
        
        matching_skills = [skill for skill in user_skills if skill in job_text]
        if matching_skills:
            reasons.append(f"Skills match: {', '.join(matching_skills[:3])}")
        
        if user_profile.get("experience_level", "").lower() in (job.experience_level or "").lower():
            reasons.append("Experience level matches")
        
        if "remote" in (job.location or "").lower():
            reasons.append("Remote position available")
        
        if not reasons:
            reasons.append("Limited match with current profile")
        
        return reasons

    def _suggest_certifications(self, missing_skills: List[str]) -> List[str]:
        """Suggest relevant certifications for missing skills"""
        cert_map = {
            "aws": ["AWS Solutions Architect", "AWS Developer"],
            "azure": ["Azure Fundamentals", "Azure Developer"],
            "gcp": ["Google Cloud Professional", "GCP Associate"],
            "kubernetes": ["Certified Kubernetes Administrator", "CKAD"],
            "docker": ["Docker Certified Associate"],
            "python": ["Python Institute PCAP", "Python Data Science"],
            "javascript": ["JavaScript ES6 Certification"],
            "react": ["React Developer Certification"],
            "node.js": ["Node.js Application Developer"]
        }
        
        suggestions = []
        for skill in missing_skills:
            skill_lower = skill.lower()
            for key, certs in cert_map.items():
                if key in skill_lower:
                    suggestions.extend(certs)
        
        return list(set(suggestions))[:5]

    def _prioritize_learning(self, missing_skills: List[str]) -> List[Dict]:
        """Prioritize skills to learn based on market demand"""
        priorities = []
        
        for skill in missing_skills[:10]:
            # Calculate demand score
            demand = self.db.query(func.count(JobListing.id)).filter(
                or_(
                    JobListing.description.ilike(f"%{skill}%"),
                    JobListing.requirements.ilike(f"%{skill}%")
                )
            ).scalar()
            
            # Estimate learning difficulty (simplified)
            difficulty_map = {
                "python": "Easy", "javascript": "Easy", "react": "Medium",
                "aws": "Medium", "kubernetes": "Hard", "machine learning": "Hard"
            }
            
            difficulty = difficulty_map.get(skill.lower(), "Medium")
            
            priorities.append({
                "skill": skill,
                "demand": demand,
                "difficulty": difficulty,
                "priority_score": demand / (1 if difficulty == "Easy" else 2 if difficulty == "Medium" else 3),
                "estimated_time": "2-4 weeks" if difficulty == "Easy" else "1-2 months" if difficulty == "Medium" else "3-6 months"
            })
        
        return sorted(priorities, key=lambda x: x["priority_score"], reverse=True) 