import json
from openai import AsyncOpenAI
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.job import JobListing, UserProfile
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class ReferralEmailGenerator:
    """AI-powered referral email generation service"""

    TEMPLATES = {
        'software_engineering': {
            'focus': 'scalable and innovative software solutions',
            'skills_format': 'full-stack development ({skills})',
            'value_prop': 'building scalable systems',
            'keywords': ['software', 'engineer', 'developer', 'programming', 'full stack', 'backend', 'frontend']
        },
        'frontend': {
            'focus': 'creating exceptional user experiences',
            'skills_format': 'frontend expertise ({skills})',
            'value_prop': 'crafting intuitive interfaces',
            'keywords': ['frontend', 'ui', 'ux', 'react', 'vue', 'angular', 'javascript', 'typescript']
        },
        'backend': {
            'focus': 'building robust backend infrastructure',
            'skills_format': 'backend development ({skills})',
            'value_prop': 'designing scalable architectures',
            'keywords': ['backend', 'api', 'database', 'server', 'microservices', 'cloud', 'python', 'java']
        },
        'data': {
            'focus': 'driving insights through data analysis and machine learning',
            'skills_format': 'data science expertise ({skills})',
            'value_prop': 'transforming data into actionable insights',
            'keywords': ['data', 'analytics', 'machine learning', 'ai', 'python', 'sql', 'scientist', 'analyst']
        },
        'mobile': {
            'focus': 'creating seamless mobile experiences',
            'skills_format': 'mobile development ({skills})',
            'value_prop': 'building intuitive mobile applications',
            'keywords': ['mobile', 'ios', 'android', 'react native', 'flutter', 'swift', 'kotlin']
        },
        'devops': {
            'focus': 'streamlining development and deployment processes',
            'skills_format': 'DevOps expertise ({skills})',
            'value_prop': 'optimizing development workflows',
            'keywords': ['devops', 'infrastructure', 'docker', 'kubernetes', 'aws', 'azure', 'ci/cd']
        }
    }

    def __init__(self, db: Session):
        self.db = db
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured - using fallback email generation")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def classify_job_category(self, job_title: str, job_description: str = "") -> str:
        """Classify job into template category based on title and description"""
        job_text = f"{job_title} {job_description}".lower()

        # Score each template based on keyword matches
        scores = {}
        for template_name, template_data in self.TEMPLATES.items():
            score = 0
            for keyword in template_data['keywords']:
                if keyword in job_text:
                    score += 1
            scores[template_name] = score

        # Return template with highest score, default to software_engineering
        best_template = max(scores, key=scores.get)
        return best_template if scores[best_template] > 0 else 'software_engineering'

    def extract_relevant_skills(self, user_skills: List[str], job_requirements: str) -> List[str]:
        """Extract user skills most relevant to the job"""
        if not user_skills or not job_requirements:
            return user_skills[:5] if user_skills else []

        job_requirements_lower = job_requirements.lower()
        relevant_skills = []

        # Find skills mentioned in job requirements
        for skill in user_skills:
            if skill.lower() in job_requirements_lower:
                relevant_skills.append(skill)

        # Add remaining skills up to 5 total
        for skill in user_skills:
            if skill not in relevant_skills and len(relevant_skills) < 5:
                relevant_skills.append(skill)

        return relevant_skills[:5]

    async def get_user_profile(self, user_id: str) -> Dict:
        """Get user profile information"""
        try:
            # Get user basic info
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Get detailed profile if available
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

            if profile:
                return {
                    'name': user.full_name or 'User',
                    'email': user.email,
                    'experience_summary': profile.professional_summary or f"{profile.years_of_experience} years of experience",
                    'skills': profile.programming_languages or [],
                    'job_titles': profile.job_titles or [],
                    'companies': profile.companies or []
                }
            else:
                # Fallback to basic user info
                return {
                    'name': user.full_name or 'User',
                    'email': user.email,
                    'experience_summary': 'Software development experience',
                    'skills': [],
                    'job_titles': [],
                    'companies': []
                }
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            raise

    async def get_job_data(self, job_id: int) -> Dict:
        """Get job listing information"""
        try:
            job = self.db.query(JobListing).filter(JobListing.id == job_id).first()
            if not job:
                # Return default job data instead of raising an error
                return {
                    'title': 'Software Engineer',
                    'company': 'Tech Company',
                    'location': 'Remote',
                    'description': '',
                    'requirements': '',
                    'job_type': '',
                    'experience_level': ''
                }

            return {
                'title': job.title,
                'company': job.company,
                'location': job.location or 'Remote',
                'description': job.description or '',
                'requirements': job.requirements or '',
                'job_type': job.job_type or '',
                'experience_level': job.experience_level or ''
            }
        except Exception as e:
            logger.error(f"Error getting job data: {e}")
            # Return default job data
            return {
                'title': 'Software Engineer',
                'company': 'Tech Company',
                'location': 'Remote',
                'description': '',
                'requirements': '',
                'job_type': '',
                'experience_level': ''
            }

    async def generate_referral_email(
        self,
        user_profile: Dict,
        job_data: Dict,
        contact_info: Dict
    ) -> Dict:
        """Generate personalized referral email using template"""
        try:
            # Determine job category
            job_category = self.classify_job_category(
                job_data.get('title', ''),
                job_data.get('description', '')
            )

            # For now, always use fallback method to avoid OpenAI API issues
            return self._generate_fallback_email(user_profile, job_data, contact_info, job_category)

        except Exception as e:
            logger.error(f"Error generating referral email: {e}")
            # Fallback to template-based generation
            return self._generate_fallback_email(user_profile, job_data, contact_info, 'software_engineering')

    def _generate_fallback_email(
        self,
        user_profile: Dict,
        job_data: Dict,
        contact_info: Dict,
        template_category: str
    ) -> Dict:
        """Generate fallback email when AI fails"""
        template = self.TEMPLATES.get(template_category, self.TEMPLATES['software_engineering'])

        # Use contact's company instead of job company for referral context
        referral_company = contact_info.get('company', job_data['company'])

        subject = f"Referral request for {job_data['title']} role at {referral_company}"

        body = f"""Hi {contact_info['name']},

I hope this message finds you well! I saw that you're {contact_info.get('position', 'working')} at {contact_info['company']}, and I wanted to reach out about an opportunity.

I'm currently exploring the {job_data['title']} role at {referral_company}. With my background in {user_profile.get('experience_summary', 'software development')}, I believe I could contribute meaningfully to your team's mission of {template['focus']}.

Would you be comfortable providing a referral or sharing insights about the role? I completely understand if it's not possible - no pressure at all.

Thanks for considering, and I hope to hear from you soon!

Best regards,
{user_profile.get('name', 'User')}"""

        return {
            'subject': subject,
            'body': body,
            'template_used': template_category
        }