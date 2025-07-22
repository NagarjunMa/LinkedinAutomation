from openai import AsyncOpenAI
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    """
    OpenAI GPT-4o-mini integration for job matching and resume parsing
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAPI_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        
    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract structured information from resume text using GPT-4o-mini
        
        Args:
            resume_text: Raw text extracted from resume file
            
        Returns:
            Structured profile data dictionary
        """
        prompt = f"""
        Extract structured information from this resume and return ONLY a valid JSON object with the following structure:

        {{
            "personal_info": {{
                "full_name": "string",
                "email": "string", 
                "phone": "string",
                "location": "string",
                "work_authorization": "string"
            }},
            "professional_summary": {{
                "years_of_experience": 0.0,
                "career_level": "entry|mid|senior",
                "summary": "string"
            }},
            "skills": {{
                "programming_languages": ["Python", "JavaScript"],
                "frameworks_libraries": ["React", "Django"],
                "tools_platforms": ["AWS", "Docker"],
                "soft_skills": ["Leadership", "Communication"]
            }},
            "experience": {{
                "job_titles": ["Software Engineer", "Intern"],
                "companies": ["Google", "Startup Inc"],
                "industries": ["Technology", "Finance"],
                "descriptions": ["Led team of 5", "Built scalable APIs"]
            }},
            "education": {{
                "degrees": ["B.S. Computer Science"],
                "institutions": ["Stanford University"],
                "graduation_years": [2022],
                "coursework": ["Data Structures", "Algorithms"]
            }},
            "preferences": {{
                "desired_roles": ["Software Engineer", "Full Stack Developer"],
                "preferred_locations": ["San Francisco", "Remote"],
                "salary_range_min": 80000,
                "salary_range_max": 120000,
                "job_types": ["Full-time"]
            }}
        }}

        Resume Text:
        {resume_text}

        Return ONLY the JSON object, no additional text or explanation:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume parser. Extract information and return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            if not content:
                logger.warning("Empty response from OpenAI, using fallback")
                return self._get_fallback_profile()
            
            try:
                parsed_data = json.loads(content)
                logger.info("Successfully parsed resume with AI")
                return parsed_data
            except json.JSONDecodeError as e:
                logger.error(f"AI returned invalid JSON: {e}")
                # Return fallback structure
                return self._get_fallback_profile()
                
        except Exception as e:
            logger.error(f"Error parsing resume with AI: {e}")
            return self._get_fallback_profile()
    
    async def generate_profile_insights(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI insights about user profile including strengths and career advice
        """
        prompt = f"""
        Analyze this user profile and provide insights. Return ONLY a valid JSON object:

        {{
            "profile_summary": "A professional 2-3 sentence summary",
            "strengths": ["Strong in Python", "Leadership experience"],
            "improvement_areas": ["Could learn cloud technologies", "Needs more frontend experience"],
            "career_advice": "Detailed career advice paragraph"
        }}

        User Profile:
        {json.dumps(profile_data, indent=2)}

        Return ONLY the JSON object:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a career counselor providing professional insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            if not content:
                logger.warning("Empty response from OpenAI for profile insights, using fallback")
                raise ValueError("Empty response")
                
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating profile insights: {e}")
            return {
                "profile_summary": "Experienced professional seeking new opportunities",
                "strengths": ["Technical skills", "Problem solving"],
                "improvement_areas": ["Continuous learning"],
                "career_advice": "Focus on building relevant skills and networking."
            }
    
    async def score_job_compatibility(
        self, 
        user_profile: Dict[str, Any], 
        job_description: str,
        job_title: str,
        job_requirements: str = ""
    ) -> Dict[str, Any]:
        """
        Score how well a job matches a user profile using AI
        
        Returns:
            Dictionary with compatibility score and detailed breakdown
        """
        # Extract key information for better scoring
        user_skills = user_profile.get('skills', {}).get('programming_languages', [])
        user_experience = user_profile.get('professional_summary', {}).get('years_of_experience', 0)
        user_location = user_profile.get('personal_info', {}).get('location', '')
        
        prompt = f"""Score this job match. Return ONLY valid JSON in this exact format:

{{"compatibility_score": 75.0, "confidence_score": 80.0, "reasoning": "Good skills match with Python and React", "match_factors": ["Technical Skills", "Experience"], "skills_match_score": 80.0, "experience_match_score": 70.0, "location_match_score": 90.0, "salary_match_score": 75.0, "culture_match_score": 65.0}}

CANDIDATE: {user_experience} years experience with skills: {', '.join(user_skills[:3]) if user_skills else 'General skills'}. Located in: {user_location}

JOB: {job_title} - {job_description[:600]}

Score 0-100 based on skill match, experience fit, and requirements. Return only JSON:"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert job matching AI. Score compatibility objectively."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            
            if not content:
                logger.warning("Empty response from OpenAI for job scoring, using fallback")
                raise ValueError("Empty response")
                
            result = json.loads(content)
            
            # Ensure score is within bounds
            result["compatibility_score"] = max(0.0, min(100.0, result.get("compatibility_score", 0.0)))
            
            return result
            
        except Exception as e:
            logger.error(f"Error scoring job compatibility: {e}")
            return {
                "compatibility_score": 50.0,
                "confidence_score": 30.0,
                "reasoning": "Unable to analyze compatibility",
                "match_factors": [],
                "mismatch_factors": ["analysis_failed"],
                "breakdown": {
                    "skills_match": 50.0,
                    "experience_match": 50.0,
                    "location_match": 50.0,
                    "salary_match": 50.0,
                    "culture_match": 50.0
                }
            }
    
    async def generate_daily_digest(
        self,
        user_profile: Dict[str, Any],
        top_jobs: List[Dict[str, Any]],
        market_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized daily digest content
        """
        prompt = f"""
        Create a personalized daily job digest. Return ONLY a valid JSON object:

        {{
            "digest_title": "Engaging title like '5 Perfect Matches for Software Engineer'",
            "digest_summary": "2-3 sentence summary of today's opportunities",
            "digest_html": "HTML formatted email content with job highlights",
            "market_insights": ["Insight 1", "Insight 2"],
            "skill_recommendations": ["Learn React", "Practice system design"]
        }}

        User Profile: {user_profile.get('professional_summary', 'New graduate')}
        Preferred Roles: {user_profile.get('preferences', {}).get('desired_roles', [])}
        
        Top Jobs Today: {len(top_jobs)} matches
        {json.dumps(top_jobs[:3], indent=2) if top_jobs else "No jobs"}

        Market Data: {market_data or 'No market data available'}

        Create engaging, personalized content. Return ONLY the JSON object:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a career coach creating personalized job digests."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.4
            )
            
            content = response.choices[0].message.content.strip()
            
            if not content:
                logger.warning("Empty response from OpenAI for daily digest, using fallback")
                raise ValueError("Empty response")
                
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating daily digest: {e}")
            return {
                "digest_title": f"{len(top_jobs)} New Job Matches",
                "digest_summary": "Check out today's job opportunities tailored for you.",
                "digest_html": "<h1>Your Daily Job Digest</h1><p>New opportunities await!</p>",
                "market_insights": ["Job market remains competitive"],
                "skill_recommendations": ["Continue developing your core skills"]
            }
    
    def _get_fallback_profile(self) -> Dict[str, Any]:
        """
        Return basic profile structure when AI parsing fails
        """
        return {
            "personal_info": {
                "full_name": "",
                "email": "",
                "phone": "",
                "location": "",
                "work_authorization": ""
            },
            "professional_summary": {
                "years_of_experience": 0.0,
                "career_level": "entry",
                "summary": ""
            },
            "skills": {
                "programming_languages": [],
                "frameworks_libraries": [],
                "tools_platforms": [],
                "soft_skills": []
            },
            "experience": {
                "job_titles": [],
                "companies": [],
                "industries": [],
                "descriptions": []
            },
            "education": {
                "degrees": [],
                "institutions": [],
                "graduation_years": [],
                "coursework": []
            },
            "preferences": {
                "desired_roles": [],
                "preferred_locations": [],
                "salary_range_min": 0,
                "salary_range_max": 0,
                "job_types": ["Full-time"]
            }
        }

# Global AI service instance
ai_service = AIService() 