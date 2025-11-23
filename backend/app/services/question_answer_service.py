"""
Application Question Answer Service
Generates authentic responses based on user's actual experience
"""

import asyncio
from openai import AsyncOpenAI
from typing import List, Dict
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from app.models.job import JobListing
from app.models.resume import ResumeEvaluation
from app.models.profile import ProfileInfo
import logging

logger = logging.getLogger(__name__)


class QuestionAnswerService:
    """Service for generating authentic application answers"""

    def __init__(self, db: Session):
        self.db = db
        if not settings.OPENAI_API_KEY:
            logger.error("OpenAI API key not configured - QuestionAnswerService will not work")
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_answers_batch(
        self,
        user_id: str,
        job_id: str,
        questions: List[str],
        job_description: str = None
    ) -> List[dict]:
        """Generate answers for multiple questions"""

        try:
            # Get user context once
            user_context = await self.get_user_context(user_id)
            job_context = await self.get_job_context(job_id, job_description)

            # Generate answers in parallel
            tasks = [
                self.generate_single_answer(q, user_context, job_context)
                for q in questions
            ]

            answers = await asyncio.gather(*tasks)

            return [
                {
                    'question': questions[i],
                    'answer': answers[i],
                    'word_count': len(answers[i].split()),
                    'char_count': len(answers[i])
                }
                for i in range(len(questions))
            ]
        except Exception as e:
            logger.error(f"Error in generate_answers_batch: {e}")
            raise

    async def get_user_context(self, user_id: str) -> dict:
        """Get user's profile and resume data"""

        try:
            # Get latest resume
            resume = self.db.query(ResumeEvaluation).filter(
                ResumeEvaluation.user_id == user_id
            ).order_by(ResumeEvaluation.created_at.desc()).first()

            # Get profile
            profile = self.db.query(ProfileInfo).filter(
                ProfileInfo.user_id == user_id
            ).first()

            # Get user basic info
            user = self.db.query(User).filter(User.user_id == user_id).first()

            resume_content = ""
            if resume:
                resume_content = resume.resume_content or ""

            # Extract structured data from resume
            projects = await self.extract_projects_from_resume(resume_content)
            achievements = await self.extract_achievements_from_resume(resume_content)

            return {
                'resume_text': resume_content,
                'projects': projects,
                'achievements': achievements,
                'background': profile.background_summary if profile else "Software development experience",
                'university': getattr(profile, 'university', 'University'),
                'experience_level': getattr(profile, 'experience_level', 'Mid-level'),
                'name': user.full_name if user else "User"
            }
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            # Return fallback context
            return {
                'resume_text': "Software development experience",
                'projects': "Various software projects",
                'achievements': "Technical achievements in software development",
                'background': "Software development experience",
                'university': 'University',
                'experience_level': 'Mid-level',
                'name': 'User'
            }

    async def get_job_context(self, job_id: str, job_description: str = None) -> dict:
        """Get job details for context"""

        try:
            # Start with default context
            job_context = {
                'title': 'Software Engineer',
                'company': 'Tech Company',
                'description': 'Software development role',
                'requirements': 'Programming skills, problem solving'
            }

            # Try to get job data from database if available
            if job_id != "sample-job-id":
                try:
                    job_id_int = int(job_id)
                    job = self.db.query(JobListing).filter(JobListing.id == job_id_int).first()
                    if job:
                        job_context.update({
                            'title': job.title or job_context['title'],
                            'company': job.company or job_context['company'],
                            'description': job.description or job_context['description'],
                            'requirements': job.requirements or job_context['requirements']
                        })
                except (ValueError, TypeError):
                    pass  # Keep default context

            # Override with provided job description if available
            if job_description and job_description.strip():
                job_context['description'] = job_description.strip()
                # Extract requirements from job description if it looks structured
                if 'requirements:' in job_description.lower() or 'qualifications:' in job_description.lower():
                    job_context['requirements'] = job_description.strip()

            return job_context
        except Exception as e:
            logger.error(f"Error getting job context: {e}")
            return {
                'title': 'Software Engineer',
                'company': 'Tech Company',
                'description': 'Software development role',
                'requirements': 'Programming skills, problem solving'
            }

    async def generate_single_answer(
        self,
        question: str,
        user_context: dict,
        job_context: dict
    ) -> str:
        """Generate one authentic answer"""

        try:
            prompt = f"""
You are helping a job candidate answer an application question using ONLY their actual experience.
Make the answer sound authentic and personal - as if the candidate is naturally explaining their work.

Question: {question}

Candidate's ACTUAL Experience:
Resume: {user_context['resume_text'][:2000]}

Key Projects: {user_context['projects']}

Achievements: {user_context['achievements']}

Background: {user_context['background']}

Job Context:
Position: {job_context['title']} at {job_context['company']}
Requirements: {job_context['requirements'][:500]}

RULES FOR AUTHENTIC ANSWERS:

1. VOICE & TONE:
   - First-person: "I built..." not "The candidate built..."
   - Conversational: "I was excited to..." not "I endeavored to..."
   - Natural language: "really challenging" not "significantly complex"
   - Personal perspective: "What I found interesting was..."

2. FORBIDDEN AI PHRASES (Never use):
   ❌ "leveraged", "spearheaded", "facilitated", "utilized"
   ❌ "cutting-edge", "innovative solutions", "best practices"
   ❌ "demonstrated", "showcased", "exemplified"
   ✅ Use instead: built, created, solved, improved, learned, helped

3. CONTENT REQUIREMENTS:
   - Use ONLY their actual projects from resume
   - Include real metrics and outcomes
   - Explain decision-making process
   - Show genuine interest in the work
   - Connect to THIS specific job

4. STRUCTURE:
   - Direct answer to question (1 sentence)
   - Specific example from experience (2-3 sentences)
   - Impact/outcome with metrics (1-2 sentences)
   - Connection to target role (1 sentence)

5. LENGTH: 150-200 words

Example GOOD answer:
"I built a full-stack e-commerce platform that handled our Black Friday traffic - about 10,000 concurrent users.
The interesting challenge was that our previous system crashed at 1,000 users, so I had to rethink how we cached
product data. I moved from database queries to Redis for the hot products, which cut response time from 800ms to
45ms. The result was zero downtime during our biggest sales day, and actually our conversion rate went up 12%
because pages loaded faster. For this role at {job_context['company']}, I think that experience with optimizing
for scale would be really relevant."

Example BAD answer:
"I leveraged cutting-edge technologies to spearhead an innovative solution that facilitated seamless user experiences
and demonstrated exceptional technical prowess in building scalable systems."

Generate the answer now. Sound like a smart student explaining their actual work, not an AI essay.
"""

            answer = await self.openai_call(prompt)
            return answer.strip()
        except Exception as e:
            logger.error(f"Error generating single answer: {e}")
            return f"I have experience with {question.lower()} that would be valuable for this role. Based on my background in software development, I can contribute effectively to this position."

    async def extract_projects_from_resume(self, resume_text: str) -> str:
        """Extract project descriptions from resume"""

        if not resume_text or len(resume_text) < 50:
            return "Various software development projects including web applications and system improvements."

        try:
            prompt = f"""
Extract 2-3 most significant projects from this resume:

{resume_text}

For each project, include:
- Project name and description
- Technologies used
- Impact/outcomes

Format as bullet list. Keep concise.
"""

            return await self.openai_call(prompt)
        except Exception as e:
            logger.error(f"Error extracting projects: {e}")
            return "Various software development projects including web applications and system improvements."

    async def extract_achievements_from_resume(self, resume_text: str) -> str:
        """Extract quantified achievements"""

        if not resume_text or len(resume_text) < 50:
            return "Improved system performance, contributed to team projects, and delivered quality software solutions."

        try:
            prompt = f"""
Extract top 5 quantified achievements from this resume:

{resume_text}

Include metrics like:
- Performance improvements (%)
- User numbers
- Revenue impact
- Time savings

Format as bullet list with metrics.
"""

            return await self.openai_call(prompt)
        except Exception as e:
            logger.error(f"Error extracting achievements: {e}")
            return "Improved system performance, contributed to team projects, and delivered quality software solutions."

    async def openai_call(self, prompt: str) -> str:
        """Make OpenAI API call with error handling"""

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=0.7
            )

            content = response.choices[0].message.content
            if content is None:
                logger.warning("OpenAI returned None content")
                return "Based on my experience in software development, I believe I can contribute effectively to this role and am excited about the opportunity to apply my skills."

            return content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            # Return a fallback response
            return "Based on my experience in software development, I believe I can contribute effectively to this role and am excited about the opportunity to apply my skills."