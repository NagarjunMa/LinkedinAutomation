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
from app.schemas.resume_legacy import ResumePrecisionAnalysis, ResumeEvaluationResult
from app.services.profile_service import ProfileService

logger = logging.getLogger(__name__)

# Comprehensive evaluation prompt combining all agent expertise
COMPREHENSIVE_RESUME_EVALUATOR_PROMPT = """
Role: You are a Hyper-Critical Senior Hiring Manager and ATS Architect with 20+ years of experience. You have hired for FAANG and high-growth startups.
Current Date: {current_date}

### OBJECTIVE
Perform a "Precision Analysis" of the provided resume. You are certifying the candidate's market readiness. If a resume is mediocre, the score MUST be low. Do not provide generic encouragement; provide high-impact, data-driven critiques.

### INPUT DATA
Target Roles: {target_roles}
User Context: {user_detailed_context}

### RESUME CONTENT
### START_CONTENT ###
{resume_content}
### END_CONTENT ###

### EVALUATION LOGIC & UI BUCKETS

1. OPTICAL STRENGTHS (The 7-Second Scan):
   - Assess visual hierarchy, branding, and "Above the Fold" impact.
   - Does the header immediately communicate the candidate's value proposition?

2. STRATEGIC IMPROVEMENTS (Architecture & Seniority):
   - Identify gaps in leadership, project ownership, and technical scope.
   - SENIORITY ALIGNMENT: Ensure the narrative shifts from "executing tasks" to "driving business outcomes" as roles progress.
   - PARSING PROTECTION: If the resume text appears jumbled or out of chronological order (potential PDF extraction error), suggest a "Single-Column, ATS-Optimized Layout" as the top priority.

3. WORDING SUGGESTIONS (The Google XYZ Audit):
   - Identify weak, passive bullet points (e.g., "Responsible for," "Worked on").
   - Every suggestion MUST follow the Google XYZ Formula: "Accomplished [X] as measured by [Y], by doing [Z]."
   - Demand metrics: %, $, ms latency, number of users, or scale.

4. ATS COMPATIBILITY (Technical Parsability):
   - Check keyword density for {target_roles}.
   - Identify "Parsing Blockers" (tables, columns, non-standard headers).

### SCORING CALIBRATION (Strict Baseline)
- 90-100 (Exceptional): FAANG-ready. Perfect quantification. High keyword density. Clear leadership narrative.
- 70-89 (Strong): Competent but missing high-level metrics (the "Y" in XYZ) or specific technical leadership evidence.
- 50-69 (Needs Work): Significant use of passive voice, generic task descriptions, or poor information hierarchy.
- <50 (Fail): Lack of quantification, outdated tech stack, or major formatting/parsing issues.

### CRITICAL CONSTRAINTS
- NO PERSONAL PRONOUNS: Flag "I", "me", or "my" as violations of Harvard Career Standards.
- NO HALLUCINATION: If a section is already in the top 1%, state "Exceeds Industry Standards."
- SENSITIVE DATA: Ignore and do not output SSNs, specific home addresses, or government ID numbers.
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
        
    def _truncate_text(self, text: str, max_words: int = 1500) -> str:
        """Truncate text to max_words to prevent token overflow during API call"""
        words = text.split()
        if len(words) > max_words:
            logger.info(f"Truncating resume text from {len(words)} to {max_words} words")
            return " ".join(words[:max_words])
        return text

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
        Evaluate resume using single consolidated prompt with Structured Outputs.
        Returns a dict matching the ResumePrecisionAnalysis schema structure.
        """
        try:
            start_time = datetime.now(timezone.utc)

            # 1. Preprocess & Truncate
            cleaned_text = self._preprocess_resume_text(resume_text)
            truncated_text = self._truncate_text(cleaned_text, max_words=1500)

            # 2. Fetch User Profile for Context
            try:
                profile = ProfileService.get_profile_with_stats(db, user_id)
                if profile is None:
                    logger.info(f"No profile found for user {user_id}, using defaults")
                    profile = {}
            except Exception as e:
                logger.warning(f"Could not fetch profile for user {user_id}: {e}")
                profile = {}

            # 3. Build User Context
            user_context = self._build_user_context(profile, target_role, target_seniority)
            
            # Prepare formatted strings for prompt
            target_roles_str = ", ".join(user_context.get("target_roles", ["General Tech Role"]))
            user_context_str = json.dumps(user_context, indent=2)
            current_date_str = datetime.now().strftime("%B %d, %Y")

            # 4. Format Prompt
            evaluation_prompt = self.comprehensive_prompt.format(
                current_date=current_date_str,
                resume_content=truncated_text,
                target_roles=target_roles_str,
                user_detailed_context=user_context_str
            )

            # 5. Call OpenAI with Structured Outputs
            logger.info(f"Starting consolidated resume evaluation for resume {resume_id}")
            
            # We access the client directly for beta.chat.completions.parse
            # Assumes ai_service.client is an AsyncOpenAI instance
            messages = [
                {"role": "system", "content": evaluation_prompt},
                {"role": "user", "content": "Analyze this resume."}
            ]

            completion = await self.ai_service.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06", # Using a model that supports Structured Outputs
                messages=messages,
                response_format=ResumePrecisionAnalysis,
                temperature=0.0
            )

            # 6. Extract Parsed Result
            result: ResumePrecisionAnalysis = completion.choices[0].message.parsed
            
            # 7. Convert to Dict and Add Metadata
            evaluation_result = result.model_dump()
            
            evaluation_result["evaluation_id"] = resume_id
            evaluation_result["user_id"] = user_id
            evaluation_result["evaluated_at"] = datetime.now(timezone.utc).isoformat()
            evaluation_result["processing_time_seconds"] = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()
            evaluation_result["evaluation_method"] = "structured_precision_analysis"

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