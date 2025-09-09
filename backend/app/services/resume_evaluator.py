import os
import uuid
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import fitz  # PyMuPDF for PDF processing
from docx import Document
import re
from app.core.ai_service import AIService
from app.schemas.resume import ResumeEvaluationResult, AIEvaluationPrompt
from app.models.resume import Resume, ResumeEvaluation

logger = logging.getLogger(__name__)


class ResumeEvaluatorService:
    """Service for AI-powered resume evaluation"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.evaluation_prompts = self._load_evaluation_prompts()
    
    def _load_evaluation_prompts(self) -> Dict[str, str]:
        """Load the comprehensive evaluation prompts"""
        return {
            "primary_evaluation": self._get_primary_evaluation_prompt(),
            "experience_validation": self._get_experience_validation_prompt(),
            "ats_compliance": self._get_ats_compliance_prompt(),
            "keyword_analysis": self._get_keyword_analysis_prompt()
        }
    
    def _get_primary_evaluation_prompt(self) -> str:
        """Senior hiring manager evaluation prompt - brutally honest, actionable feedback"""
        return """
        You are a senior hiring manager with 20+ years of experience in the technology industry. You have personally screened over 10,000 resumes, hired hundreds of engineers across all levels (L3-L7), and worked at both MAANG companies and high-growth startups. You understand what separates good candidates from exceptional hires and have deep knowledge of ATS systems, recruiter psychology, and market trends.

        Your Mission: Provide brutally honest, actionable resume feedback that transforms candidates from "maybe" to "must interview." You prioritize truth over politeness, focusing on what actually gets results in today's competitive hiring market.

        EVALUATION FRAMEWORK - Complete assessment in under 6 seconds:

        1. Initial Assessment (Score: 0-10)
        Rate the resume immediately based on:
        - First Impression (6-second recruiter scan test)
        - ATS Compatibility (formatting, keywords, structure)
        - Experience Relevance (role alignment, progression, impact)
        - Technical Depth (skill validation, project complexity)
        - Leadership Indicators (team size, cross-functional work, mentoring)

        2. Deep Analysis Categories

        A. Structure & Format (Weight: 15%)
        - Standard format adherence (Summary → Experience → Skills → Education → Projects)
        - One-page optimization (for <8 years experience) or strategic two-page layout
        - ATS-friendly formatting (clear headers, bullet points, readable fonts)
        - Information hierarchy and visual scanning optimization

        B. Professional Summary (Weight: 20%)
        - Value proposition clarity within first 10 words
        - Quantified experience level and specialization
        - Keyword density for target roles
        - Differentiation from generic templates

        C. Experience Section (Weight: 40%)
        - Impact Over Tasks: Each bullet shows measurable business outcomes
        - Scale Indicators: User volumes, system throughput, team sizes, global reach
        - Technical Leadership: Architecture decisions, system design, technology adoption
        - Career Progression: Increasing responsibility, scope, and impact
        - Action Verb Diversity: Avoid repetitive language that hurts ATS scores
        - Credibility Check: Do metrics align with company size and role level?

        D. Technical Skills (Weight: 10%)
        - Current technology relevance (2024-2025 market demands)
        - Skill categorization and logical grouping
        - Depth vs breadth balance for experience level
        - Integration with experience bullets (skills should appear in context)

        E. Education & Projects (Weight: 15%)
        - Educational credentials appropriate for role level
        - Projects that demonstrate innovation, complexity, or business impact
        - Evidence of continuous learning and adaptation to new technologies

        3. Red Flag Detection
        Immediately flag these resume killers:
        - Job Hopping: Multiple roles under 18 months without clear progression
        - Scale Inconsistencies: Metrics that don't match company size or role level
        - Technology Misalignment: Outdated or irrelevant skill stacks
        - Generic Language: Template phrases without specific achievements
        - Format Issues: Poor ATS compatibility, wall of text, inconsistent formatting
        - Timeline Gaps: Unexplained employment gaps over 6 months
        - Typos/Grammar: Any spelling or grammatical errors (instant disqualification)

        4. Company-Specific Assessment
        Based on target company type, evaluate fit for:
        - MAANG Companies (L4-L6 roles): Distributed systems experience at scale, leadership potential, innovation mindset
        - Startups: Full-stack versatility, speed of execution, early-stage company experience
        - Enterprise/Traditional: Process adherence, client-facing experience, industry-specific compliance

        RESPONSE FORMAT - Be direct and actionable:
        {
            "overall_score": <0-100>,
            "ats_compliance_score": <0-100>,
            "content_quality_score": <0-100>,
            "experience_points_score": <0-100>,
            "job_relevance_score": <0-100>,
            "quality_checks_score": <0-100>,
            "strengths": ["What makes this candidate stand out positively"],
            "improvements": ["Critical issues that prevent interview callbacks"],
            "ats_compatibility": "excellent|good|fair|poor",
            "detailed_feedback": "Executive summary with immediate hiring manager perspective",
            "keyword_analysis": {
                "relevant": ["job-relevant keywords found"],
                "missing": ["critical missing keywords"],
                "score": <0-100>
            },
            "critical_issues": {
                "immediate_fixes": ["Issues that prevent interview callbacks"],
                "strategic_improvements": ["Changes that elevate from good to exceptional"],
                "nice_to_have": ["Polish items for competitive advantage"]
            },
            "market_positioning": {
                "current_level": "Current competitive level in market",
                "salary_range": "Salary range positioning",
                "target_roles": "Role levels candidate should target",
                "company_fit": {
                    "maang_companies": <1-10>,
                    "startups": <1-10>,
                    "enterprise": <1-10>
                }
            }
        }

        KEY PHRASES TO USE:
        - "This resume currently positions you for..."
        - "Immediate red flags that hurt your chances..."
        - "To compete at [target company level], you need..."
        - "Your strongest differentiator is..."
        - "Critical gaps compared to successful candidates..."

        Remember: Your goal is to transform resumes into interview-generating machines. Be the hiring manager every candidate wishes they could consult before applying. Focus on what actually works in today's competitive market, not outdated resume advice.
        """
    
    def _get_experience_validation_prompt(self) -> str:
        """Prompt for validating individual experience points"""
        return """
        Evaluate each resume experience point for authenticity and impact:

        For this experience point: "[EXPERIENCE_POINT]"

        EVALUATE:
        1. REALISM CHECK (0-10): 
           - Is this achievement possible given the role/experience level?
           - Are the technologies and methods appropriate?
           - Does the timeline make sense?

        2. SPECIFICITY SCORE (0-10):
           - Are technical details specific enough?
           - Is the methodology clearly explained?
           - Are results quantified with real metrics?

        3. IMPACT ASSESSMENT (0-10):
           - Is the impact measurable and significant?
           - Does it show business value understanding?
           - Is it relevant to the target role?

        FLAG IF:
        - Uses vague language ("various," "multiple," "several")
        - Claims expertise in recently released technologies
        - Shows impossible improvements (90%+ gains consistently)
        - Lacks technical context for claimed achievements
        - Contains buzzwords without implementation details

        REWRITE SUGGESTION:
        If score < 24/30, provide improved version following Action-Method-Impact format.
        """
    
    def _get_ats_compliance_prompt(self) -> str:
        """Prompt for ATS compliance analysis"""
        return """
        Analyze this resume for ATS (Applicant Tracking System) compatibility:

        ATS COMPLIANCE CHECKLIST:
        1. File Format: PDF preferred, Word acceptable
        2. Text Parsing: All text must be selectable, no images of text
        3. Standard Sections: Contact, Summary, Experience, Education, Skills
        4. Font Consistency: Standard fonts (Arial, Calibri, Times New Roman)
        5. Bullet Points: Standard bullet characters, not custom symbols
        6. Headers: Clear, standard section headers
        7. Margins: Standard margins (0.5-1 inch)
        8. Length: 1-2 pages for most roles
        9. Keywords: Relevant industry and job-specific terms
        10. No Graphics: Avoid tables, charts, images that may not parse

        Provide ATS compatibility score and specific recommendations.
        """
    
    def _get_keyword_analysis_prompt(self) -> str:
        """Prompt for keyword analysis"""
        return """
        Analyze this resume for keyword optimization:

        KEYWORD ANALYSIS FRAMEWORK:
        1. Technical Skills: Programming languages, frameworks, tools
        2. Industry Terms: Domain-specific terminology and concepts
        3. Soft Skills: Leadership, communication, problem-solving indicators
        4. Certifications: Professional certifications and qualifications
        5. Action Verbs: Strong action words for experience descriptions

        EVALUATE:
        - Keyword density (optimal 2-4% for target keywords)
        - Relevance to target role
        - Modern vs. outdated terminology
        - Missing critical keywords
        - Keyword placement and context

        Provide keyword score and specific recommendations.
        """
    
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
    
    def _preprocess_resume_text(self, text: str) -> str:
        """Clean and preprocess resume text for AI analysis"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might confuse AI
        text = re.sub(r'[^\w\s\-\.\,\!\?\(\)\:\;]', '', text)
        
        # Normalize line breaks
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        return text.strip()
    
    async def evaluate_resume(self, resume_text: str, target_role: Optional[str] = None, 
                            target_industry: Optional[str] = None) -> ResumeEvaluationResult:
        """Main method to evaluate resume using AI"""
        try:
            start_time = datetime.now()
            
            # Preprocess text
            cleaned_text = self._preprocess_resume_text(resume_text)
            
            # Prepare evaluation prompt
            evaluation_prompt = self._prepare_evaluation_prompt(
                cleaned_text, target_role, target_industry
            )
            
            # Get AI evaluation
            ai_response = await self.ai_service.get_completion(
                prompt=evaluation_prompt,
                max_tokens=2000,
                temperature=0.3
            )
            
            # Parse AI response
            evaluation_data = self._parse_ai_response(ai_response)
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds())
            
            # Create evaluation result
            result = ResumeEvaluationResult(
                overall_score=evaluation_data.get('overall_score', 0),
                ats_compliance_score=evaluation_data.get('ats_compliance_score', 0),
                content_quality_score=evaluation_data.get('content_quality_score', 0),
                experience_points_score=evaluation_data.get('experience_points_score', 0),
                job_relevance_score=evaluation_data.get('job_relevance_score', 0),
                quality_checks_score=evaluation_data.get('quality_checks_score', 0),
                strengths=evaluation_data.get('strengths', []),
                improvements=evaluation_data.get('improvements', []),
                detailed_feedback=evaluation_data.get('detailed_feedback', ''),
                ats_compatibility=evaluation_data.get('ats_compatibility', 'fair'),
                keyword_analysis=evaluation_data.get('keyword_analysis', {}),
                critical_issues=evaluation_data.get('critical_issues'),
                market_positioning=evaluation_data.get('market_positioning'),
                evaluated_at=datetime.now(),
                ai_model_version=self.ai_service.model_name,
                processing_time=processing_time
            )
            
            logger.info(f"Resume evaluation completed in {processing_time}s with score {result.overall_score}")
            return result
            
        except Exception as e:
            logger.error(f"Resume evaluation failed: {e}")
            raise
    
    def _prepare_evaluation_prompt(self, resume_text: str, target_role: Optional[str], 
                                 target_industry: Optional[str]) -> str:
        """Prepare the evaluation prompt with resume text and context"""
        base_prompt = self.evaluation_prompts["primary_evaluation"]
        
        # Customize prompt based on target role and industry
        if target_role:
            base_prompt = base_prompt.replace("[ROLE_TITLE]", target_role)
        else:
            base_prompt = base_prompt.replace("[ROLE_TITLE]", "Software Engineer")  # Default
        
        # Add industry context if provided
        industry_context = ""
        if target_industry:
            industry_context = f"\n\nINDUSTRY CONTEXT: This resume is being evaluated for {target_industry} industry positions."
        
        # Combine prompt with resume text
        full_prompt = f"{base_prompt}{industry_context}\n\nRESUME TEXT TO EVALUATE:\n{resume_text[:4000]}..."  # Limit text length
        
        return full_prompt
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response and extract evaluation data"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            # Fallback: try to parse structured text
            return self._parse_structured_response(ai_response)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return self._parse_structured_response(ai_response)
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return self._get_default_evaluation()
    
    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response that might not be in JSON format"""
        try:
            # Extract scores using regex patterns
            overall_score = self._extract_score(response, r'overall.*?score.*?(\d+)', 0)
            ats_score = self._extract_score(response, r'ats.*?compliance.*?(\d+)', 0)
            content_score = self._extract_score(response, r'content.*?quality.*?(\d+)', 0)
            experience_score = self._extract_score(response, r'experience.*?points.*?(\d+)', 0)
            relevance_score = self._extract_score(response, r'job.*?relevance.*?(\d+)', 0)
            quality_score = self._extract_score(response, r'quality.*?checks.*?(\d+)', 0)
            
            # Extract strengths and improvements
            strengths = self._extract_list_items(response, r'strengths?.*?[:|]\s*(.*?)(?=\n|$)', 'No strengths identified')
            improvements = self._extract_list_items(response, r'improvements?.*?[:|]\s*(.*?)(?=\n|$)', 'No improvements identified')
            
            # Extract ATS compatibility
            ats_compatibility = self._extract_ats_compatibility(response)
            
            return {
                'overall_score': overall_score,
                'ats_compliance_score': ats_score,
                'content_quality_score': content_score,
                'experience_points_score': experience_score,
                'job_relevance_score': relevance_score,
                'quality_checks_score': quality_score,
                'strengths': strengths,
                'improvements': improvements,
                'ats_compatibility': ats_compatibility,
                'detailed_feedback': response[:500] + '...' if len(response) > 500 else response,
                'keyword_analysis': {
                    'relevant': [],
                    'missing': [],
                    'score': 5.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing structured response: {e}")
            return self._get_default_evaluation()
    
    def _extract_score(self, text: str, pattern: str, default: int) -> int:
        """Extract numeric score from text using regex"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
        return default
    
    def _extract_list_items(self, text: str, pattern: str, default: str) -> List[str]:
        """Extract list items from text"""
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            items_text = match.group(1).strip()
            # Split by common list separators
            items = re.split(r'[,;•\-\*]', items_text)
            return [item.strip() for item in items if item.strip()]
        return [default]
    
    def _extract_ats_compatibility(self, text: str) -> str:
        """Extract ATS compatibility rating"""
        text_lower = text.lower()
        if 'excellent' in text_lower:
            return 'excellent'
        elif 'good' in text_lower:
            return 'good'
        elif 'fair' in text_lower:
            return 'fair'
        elif 'poor' in text_lower:
            return 'poor'
        return 'fair'  # Default
    
    def _get_default_evaluation(self) -> Dict[str, Any]:
        """Return default evaluation when parsing fails"""
        return {
            'overall_score': 50,
            'ats_compliance_score': 10,
            'content_quality_score': 15,
            'experience_points_score': 12,
            'job_relevance_score': 8,
            'quality_checks_score': 5,
            'strengths': ['Resume uploaded successfully'],
            'improvements': ['AI evaluation could not be completed'],
            'ats_compatibility': 'fair',
            'detailed_feedback': 'Resume was uploaded but AI evaluation encountered an error. Please try again.',
            'keyword_analysis': {
                'relevant': [],
                'missing': [],
                'score': 5.0
            }
        }
    
    async def validate_resume_storage_limit(self, user_id: str, current_count: int) -> bool:
        """Check if user can upload more resumes"""
        max_resumes = 5
        return current_count < max_resumes
    
    async def cleanup_old_resumes(self, user_id: str, keep_count: int = 5) -> List[str]:
        """Remove old resumes to maintain storage limit"""
        # This would be implemented in the repository layer
        # For now, return empty list
        return []
