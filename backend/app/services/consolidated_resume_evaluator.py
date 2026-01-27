"""
Consolidated Resume Evaluator Service.
Single comprehensive AI evaluation replacing the 12-agent system.
Provides faster, more cost-effective resume analysis with same quality.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import re
import fitz  # PyMuPDF for PDF processing
from docx import Document

from sqlalchemy.orm import Session

from app.core.ai_service import AIService
from app.schemas.resume import ResumeEvaluationResult
from app.services.profile_service import ProfileService

logger = logging.getLogger(__name__)

# Comprehensive evaluation prompt combining all agent expertise
COMPREHENSIVE_RESUME_EVALUATOR_PROMPT = """
You are a senior hiring manager with 20+ years of experience who has screened 10,000+ resumes,
hired hundreds of engineers across all levels (L3-L7), and worked at both FAANG companies and
high-growth startups. You combine expertise in ATS systems, recruiter psychology, Harvard Career
Services standards, and market trends.

═══════════════════════════════════════════════════════════
RESUME TO EVALUATE
═══════════════════════════════════════════════════════════

{resume_content}

═══════════════════════════════════════════════════════════
USER CONTEXT
═══════════════════════════════════════════════════════════

Target Roles: {target_roles}
Experience Level: {experience_level}
Target Companies: {target_companies}
Geographic Markets: {markets}

{user_detailed_context}

═══════════════════════════════════════════════════════════
EVALUATION FRAMEWORK (WEIGHTED SCORING)
═══════════════════════════════════════════════════════════

Perform comprehensive analysis across these dimensions with specified weights:

1. EXPERIENCE QUALITY & IMPACT (Weight: 22%)
   Evaluate:
   - Impact quantification: Measurable outcomes, revenue, cost savings, scale
   - Career progression: Promotions, expanding scope, leadership growth
   - Technical leadership: Architecture decisions, system design, mentoring
   - Achievement depth: Specific accomplishments vs generic duties
   - Scale credibility: Do metrics align with company size and role?

   Seniority-specific expectations:
   - New Grad/Entry: Internships, academic projects, learning potential
   - Mid-level (2-5 years): Increasing responsibility, measurable outcomes
   - Senior (5-8 years): Technical leadership, mentoring, architecture
   - Staff/Principal (8+ years): Strategic direction, org-wide impact

   Score 0-10 and identify top achievements and gaps.

2. ABOVE FOLD IMPACT (Weight: 18%)
   Analyze first third of resume (recruiter's 7-second scan):
   - Does top section immediately convey value proposition?
   - Are strongest achievements visible without scrolling?
   - Is contact information clear and professional?
   - Does professional summary hook attention in first 10 words?
   - Would recruiter continue reading or move to next candidate?

   Test: Can recruiter understand candidate's value in 7 seconds?
   Score 0-10 for immediate impact.

3. HARVARD CAREER SERVICES COMPLIANCE (Weight: 18%)
   Check strict adherence to Harvard standards:
   - No personal pronouns (I, me, my, we)
   - No passive voice ("was responsible for" → "Delivered")
   - Strong action verbs starting each bullet (Built, Led, Optimized, Designed)
   - No abbreviations without explanation
   - No narrative/paragraph style (bullet points only)
   - All achievements quantified with metrics
   - No grammar or spelling errors (zero tolerance)

   Flag every violation with specific location and correction.
   Score 0-10 for Harvard compliance.

4. RECRUITER PSYCHOLOGY & SCANNING (Weight: 15%)
   Optimize for recruiter reading behavior:
   - F-pattern reading: Left-side keyword density and visual anchors
   - First bullet strength: Is first bullet in each section the strongest?
   - White space utilization: Strategic spacing for cognitive processing
   - Bold text usage: Highlighting without overdoing (job titles only)
   - Information hierarchy: Most important details most visible
   - Scanning flow: Can recruiter skim efficiently?

   Score 0-10 for recruiter-friendly optimization.

5. FORMAT & STRUCTURE (Weight: 13%)
   Assess visual presentation:
   - Standard section order: Summary → Experience → Skills → Education
   - One page for <8 years experience, strategic two-page for senior
   - 1-inch margins, 10-12pt body text, 14-16pt headers
   - Professional fonts: Arial, Calibri, Times New Roman
   - Clear visual hierarchy with consistent formatting
   - No tables, headers, footers, text boxes (ATS parsing issues)
   - White space balance: Not cramped, not sparse

   Score 0-10 for structure quality.

6. DETAILED CONTENT ANALYSIS (Weight: 13%)
   Deep dive into content quality:
   - Bullet point effectiveness: Action verb + specific task + quantified result
   - Each bullet 1-2 lines maximum
   - 3-5 bullets per role (no more, no less)
   - No repetitive language across bullets
   - Technical specificity: Exact tools, technologies, methodologies
   - Consistency: Tense, formatting, style throughout
   - Storytelling: Clear career narrative and progression

   Score 0-10 for content excellence.

7. ATS COMPATIBILITY (Weight: 12%)
   Technical parsing assessment:
   - Clear section headers that ATS recognizes
   - Keyword density for target roles (10-15 relevant keywords minimum)
   - PDF optimization for text extraction
   - No graphics, images, icons (ATS ignores them)
   - Standard formatting ATS can parse
   - File size <2MB, proper filename (Firstname_Lastname_Resume.pdf)

   Score 0-10 for ATS friendliness.

8. SKILLS ASSESSMENT (Weight: 10%)
   Technical skills evaluation:
   - 8-12 most relevant skills for target roles
   - 2024-2025 technology currency (modern vs outdated stack)
   - Skill categorization: Programming, Cloud, Tools, Frameworks
   - Skills appear in experience context, not just listed
   - No filler skills (MS Word, typing, email)
   - Most relevant skills listed first (not alphabetical)

   Score 0-10 for skills strength.

9. FINAL POLISH (Weight: 9%)
   Professional finishing touches:
   - Zero typos or grammar errors (instant disqualification)
   - Date consistency: "Jan 2020 – Dec 2022" format throughout
   - Capitalization consistency
   - Professional email address (not partyguy123@gmail.com)
   - LinkedIn URL properly formatted
   - No personal information (photo, age, marital status, hobbies)

   Score 0-10 for polish and professionalism.

10. COMPANY FIT ASSESSMENT (Weight: 7%)
    Evaluate alignment with target company types:

    FAANG/Tech Giants:
    - Distributed systems at massive scale
    - Cross-functional leadership and collaboration
    - Innovation mindset and technical depth
    - Ownership and customer obsession indicators

    Startups:
    - Full-stack versatility and wear-many-hats capability
    - Speed of execution and scrappy problem-solving
    - Early-stage experience and ambiguity tolerance
    - Adaptability and rapid learning

    Enterprise/Traditional:
    - Process adherence and documentation skills
    - Client-facing experience and business acumen
    - Industry compliance and domain expertise
    - Stakeholder management

    Score 0-10 for each company type.

11. RED FLAGS (Penalty Weight: -15%)
    Immediate disqualifiers and major concerns:
    - Job hopping: Multiple roles <18 months without clear progression
    - Scale inconsistencies: "Managed 100-person team at 20-person startup"
    - Outdated technology: Heavy Java 6, Flash, deprecated frameworks
    - Generic template language: "Results-oriented professional seeking..."
    - Employment gaps >6 months unexplained
    - Typos, grammar errors, formatting inconsistencies
    - Missing quantification: All bullets just describe tasks
    - Passive voice throughout: "Was responsible for..."

    Each red flag reduces overall score. Flag severity and specific fixes.

═══════════════════════════════════════════════════════════
OUTPUT FORMAT (RETURN AS JSON)
═══════════════════════════════════════════════════════════

Return your complete analysis as a valid JSON object with all fields populated.
Include specific examples, line references, and actionable improvements.
Ensure all scores are justified with evidence from the resume.
"""


class ConsolidatedResumeEvaluator:
    """Single comprehensive AI service replacing 12-agent architecture."""

    def __init__(self, ai_service: AIService, max_resume_length: int = 8000):
        self.ai_service = ai_service
        self.max_resume_length = max_resume_length  # Configurable token optimization
        self.comprehensive_prompt = COMPREHENSIVE_RESUME_EVALUATOR_PROMPT

    def _sanitize_for_prompt(self, text: str, field_name: str = "text") -> str:
        """Sanitize text to prevent prompt injection attacks."""
        if not text:
            return ""

        # Remove control characters and null bytes
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        # Escape potential prompt injection patterns
        # Escape curly braces to prevent format string attacks
        text = text.replace('{', '{{').replace('}', '}}')

        # Remove potential command injection patterns
        dangerous_patterns = [
            r'(?i)ignore.*previous.*instructions',
            r'(?i)disregard.*above',
            r'(?i)forget.*context',
            r'(?i)system\s*:',
            r'(?i)assistant\s*:',
            r'(?i)\[INST\]',
            r'<\|.*\|>',
        ]

        for pattern in dangerous_patterns:
            text = re.sub(pattern, '[REDACTED]', text)

        # Log if suspicious content was found
        if '[REDACTED]' in text:
            logger.warning(f"Suspicious content detected and redacted in {field_name}")

        return text

    def _preprocess_resume_text(self, text: str) -> str:
        """Clean and preprocess resume text for AI analysis with security measures."""
        # First sanitize for security
        text = self._sanitize_for_prompt(text, "resume_content")

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters that might confuse AI (safer character whitelist)
        # Use string translation for better performance and avoid ReDoS
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n\r-.,!?():;@#$%&*+/={}')
        text = ''.join(char for char in text if char in allowed_chars)

        # Normalize line breaks
        text = text.replace('\n', ' ').replace('\r', ' ')

        # Limit length for token optimization
        if len(text) > self.max_resume_length:
            text = text[:self.max_resume_length] + "... [truncated for analysis]"
            logger.warning(f"Resume content truncated to {self.max_resume_length} characters")

        return text.strip()

    async def extract_resume_text(self, file_path: str, file_type: str) -> str:
        """Extract text content from resume file"""
        try:
            if file_type.lower() in ['pdf', 'application/pdf']:
                return self._extract_pdf_text(file_path)
            elif file_type.lower() in ['docx', 'doc', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
                return self._extract_docx_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from Word document"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"DOCX text extraction failed: {e}")
            raise

    async def evaluate_resume(
        self,
        resume_text: str,
        user_id: str,
        resume_id: str,
        db: Session,
        target_role: Optional[str] = None,
        target_seniority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive resume evaluation using single AI prompt.

        Args:
            resume_text: The resume content to evaluate
            user_id: User ID for context retrieval
            resume_id: Resume ID for tracking
            target_role: Optional specific target role
            target_seniority: Optional target seniority level

        Returns:
            Comprehensive evaluation results with scores and recommendations
        """
        try:
            start_time = datetime.now(timezone.utc)

            # Preprocess resume text
            cleaned_text = self._preprocess_resume_text(resume_text)

            # Fetch user profile for context (using passed db session)
            try:
                profile = ProfileService.get_profile_with_stats(db, user_id)
                if profile is None:
                    logger.info(f"No profile found for user {user_id}, using defaults")
                    profile = {}
            except Exception as e:
                logger.warning(f"Could not fetch profile for user {user_id}: {e}")
                profile = {}

            # Build comprehensive user context
            user_context = self._build_user_context(profile, target_role, target_seniority)

            # Sanitize all user-controlled inputs before prompt formatting
            safe_target_roles = ", ".join([
                self._sanitize_for_prompt(role, "target_role")
                for role in user_context.get("target_roles", ["General"])
            ])
            safe_experience_level = self._sanitize_for_prompt(
                user_context.get("experience_level", "mid-level"), "experience_level"
            )
            safe_target_companies = ", ".join([
                self._sanitize_for_prompt(company, "target_company")
                for company in user_context.get("target_companies", ["Tech companies"])
            ])
            safe_markets = ", ".join([
                self._sanitize_for_prompt(market, "market")
                for market in user_context.get("markets", ["United States"])
            ])

            # Sanitize context fields
            safe_context = {
                "background_summary": self._sanitize_for_prompt(
                    str(user_context.get("background_summary", "")), "background_summary"
                ),
                "years_experience": min(50, max(0, int(user_context.get("years_experience", 0)))),
                "preferred_locations": [
                    self._sanitize_for_prompt(loc, "location")
                    for loc in user_context.get("preferred_locations", [])
                ][:5],  # Limit to 5 locations
                "minimum_salary": min(1000000, max(0, int(user_context.get("minimum_salary", 0) or 0)))
            }

            # Format the comprehensive prompt with sanitized inputs
            evaluation_prompt = self.comprehensive_prompt.format(
                resume_content=cleaned_text,
                target_roles=safe_target_roles,
                experience_level=safe_experience_level,
                target_companies=safe_target_companies,
                markets=safe_markets,
                user_detailed_context=json.dumps(safe_context, indent=2)
            )

            # Single comprehensive AI call (replacing 12 parallel agents)
            logger.info(f"Starting consolidated resume evaluation for resume {resume_id}")

            response = await self.ai_service.create_completion(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert resume evaluator. Provide your analysis as a valid JSON object."
                    },
                    {
                        "role": "user",
                        "content": evaluation_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            # Parse and validate response
            evaluation_result = self._parse_evaluation_response(response)

            # Add metadata
            evaluation_result["evaluation_id"] = resume_id
            evaluation_result["user_id"] = user_id
            evaluation_result["evaluated_at"] = datetime.now(timezone.utc).isoformat()
            evaluation_result["processing_time_seconds"] = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()
            evaluation_result["evaluation_method"] = "consolidated_single_prompt"

            logger.info(
                f"Completed consolidated evaluation for resume {resume_id} "
                f"in {evaluation_result['processing_time_seconds']:.2f} seconds"
            )

            return evaluation_result

        except Exception as e:
            logger.error(f"Error in consolidated resume evaluation: {str(e)}", extra={
                "resume_id": resume_id,
                "user_id": user_id,
                "error_type": type(e).__name__
            })
            # Re-raise with sanitized message to avoid information leakage
            raise RuntimeError("Resume evaluation failed. Please try again.") from e

    def _build_user_context(
        self,
        profile: Dict[str, Any],
        target_role: Optional[str],
        target_seniority: Optional[str]
    ) -> Dict[str, Any]:
        """Build comprehensive user context for evaluation."""

        # Extract years of experience from profile or estimate
        years_experience = profile.get("years_of_experience", 0)
        if years_experience == 0 and profile.get("experience_level"):
            experience_map = {
                "entry": 0,
                "junior": 1,
                "mid": 3,
                "senior": 5,
                "lead": 7,
                "principal": 10,
                "staff": 10
            }
            years_experience = experience_map.get(
                profile.get("experience_level", "").lower(), 3
            )

        return {
            "user_id": profile.get("user_id"),
            "target_roles": profile.get("target_job_titles", []) or (
                [target_role] if target_role else ["Software Engineer"]
            ),
            "experience_level": (
                profile.get("experience_level") or
                target_seniority or
                "mid-level"
            ),
            "target_companies": profile.get("target_companies", [
                "FAANG", "Startups", "Enterprise"
            ]),
            "markets": profile.get("preferred_locations", ["United States"]),
            "background_summary": profile.get("background_summary", ""),
            "years_experience": years_experience,
            "preferred_locations": profile.get("preferred_locations", []),
            "minimum_salary": profile.get("minimum_salary"),
            "skills": profile.get("skills", [])
        }

    def _parse_evaluation_response(self, response: Any) -> Dict[str, Any]:
        """Parse and validate AI response."""
        try:
            # Extract JSON from response
            content = response.choices[0].message.content

            # Parse JSON response
            evaluation_data = json.loads(content)

            # Ensure all required fields are present with defaults
            required_fields = {
                "overall_score": 0,
                "category_scores": {},
                "seven_second_test": {},
                "executive_summary": "",
                "strengths": [],
                "critical_issues": {},
                "specific_recommendations": {},
                "company_fit_assessment": {},
                "red_flags_detected": {},
                "market_positioning": {},
                "tactical_checklist": {},
                "action_plan_prioritized": [],
                "next_version_guidance": {}
            }

            for field, default_value in required_fields.items():
                if field not in evaluation_data:
                    evaluation_data[field] = default_value
                    logger.warning(f"Missing field '{field}' in AI response, using default")

            # Validate score ranges
            if "overall_score" in evaluation_data:
                score = evaluation_data["overall_score"]
                if not (0 <= score <= 100):
                    evaluation_data["overall_score"] = max(0, min(100, score))

            # Validate category scores
            if "category_scores" in evaluation_data:
                for category, score in evaluation_data["category_scores"].items():
                    if not (0 <= score <= 10):
                        evaluation_data["category_scores"][category] = max(0, min(10, score))

            return evaluation_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            # Return a basic structure with error indication
            return {
                "overall_score": 0,
                "error": "Failed to parse AI response",
                "raw_response": str(content) if 'content' in locals() else None
            }
        except Exception as e:
            logger.error(f"Unexpected error parsing AI response: {e}")
            raise

    def calculate_weighted_score(self, category_scores: Dict[str, float]) -> float:
        """Calculate overall weighted score from category scores."""

        # Define weights for each category
        weights = {
            "experience_impact": 0.22,
            "above_fold_impact": 0.18,
            "harvard_compliance": 0.18,
            "recruiter_psychology": 0.15,
            "format_structure": 0.13,
            "detailed_content": 0.13,
            "ats_compatibility": 0.12,
            "skills_assessment": 0.10,
            "final_polish": 0.09,
            "company_fit": 0.07,
            "red_flags": -0.15  # Negative weight for penalties
        }

        total_score = 0
        total_weight = 0

        for category, weight in weights.items():
            if category in category_scores:
                score = category_scores[category]
                # Convert 0-10 scores to 0-100 for final score
                normalized_score = score * 10 if category != "red_flags" else score
                total_score += normalized_score * abs(weight)
                total_weight += abs(weight)

        # Calculate weighted average
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0

        return max(0, min(100, final_score))  # Ensure score is between 0-100