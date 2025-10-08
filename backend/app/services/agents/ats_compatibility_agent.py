"""
ATS Compatibility Agent for resume evaluation.
Analyzes resume for ATS (Applicant Tracking System) compatibility.
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class ATSCompatibilityAgent(BaseAgent):
    """Agent specialized in ATS compatibility analysis."""
    
    def __init__(self, ai_service=None):
        super().__init__("ATSCompatibilityAgent", ai_service)
    
    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze resume for ATS compatibility.
        
        Args:
            resume_content: The resume text to analyze
            context: Additional context (target roles, etc.)
            
        Returns:
            Dictionary containing ATS analysis results
        """
        context = context or {}
        target_roles = context.get('target_roles', [])
        
        # Limit resume content length to prevent overly long prompts
        max_content_length = 8000  # Adjust based on your needs
        if len(resume_content) > max_content_length:
            resume_content = resume_content[:max_content_length] + "... [truncated]"
            self.logger.warning(f"Resume content truncated to {max_content_length} characters")
        
        prompt = f"""
        You are an ATS parsing expert with 10+ years of experience in recruitment technology. 
        Analyze this resume ONLY for ATS compatibility and keyword optimization.

        Resume Content:
        {resume_content}

        Target Roles: {', '.join(target_roles) if target_roles else 'General'}

        Evaluate the following aspects:

        1. FORMAT PARSING RELIABILITY (0-10):
           - Clear section headers (Experience, Education, Skills, etc.)
           - Consistent bullet point formatting
           - Proper spacing and line breaks
           - Table and column structure (if any)

        2. KEYWORD DENSITY & PLACEMENT (0-10):
           - Technical skills mentioned in job descriptions
           - Industry-specific terminology
           - Action verbs and quantifiable metrics
   - Keyword distribution across sections

        3. FILE FORMAT COMPATIBILITY (0-10):
           - PDF format optimization
           - Text extraction quality
           - Font and formatting preservation
           - Image and graphic handling

        4. SECTION ORGANIZATION (0-10):
           - Logical flow and structure
           - Contact information placement
           - Skills section organization
           - Experience chronological order

        Return your analysis as JSON in this exact format:
        {{
            "ats_score": 0-10,
            "parsing_issues": [
                "Specific issue 1",
                "Specific issue 2"
            ],
            "keyword_optimization": {{
                "missing_keywords": ["keyword1", "keyword2"],
                "overused_keywords": ["keyword3"],
                "placement_suggestions": ["Move X to Y section"]
            }},
            "format_recommendations": [
                "Specific format improvement 1",
                "Specific format improvement 2"
            ],
            "section_analysis": {{
                "contact_info": "score and issues",
                "summary": "score and issues", 
                "experience": "score and issues",
                "skills": "score and issues",
                "education": "score and issues"
            }},
            "critical_fixes": [
                "Must-fix issues that prevent ATS parsing"
            ],
            "optimization_priority": "high|medium|low"
        }}

        Focus on actionable, specific recommendations that will improve ATS parsing success.
        """

        result = await self.llm_call(prompt)
        
        # Add agent-specific metadata
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "ats_compatibility",
            "target_roles": target_roles
        })
        
        return result
    
    def get_capabilities(self) -> list:
        """Return ATS-specific capabilities."""
        return [
            "ats_parsing_analysis",
            "keyword_optimization", 
            "format_compatibility",
            "section_organization",
            "file_format_analysis"
        ]
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate ATS analysis result structure."""
        required_fields = ["ats_score", "parsing_issues", "keyword_optimization", "format_recommendations"]
        return all(field in result for field in required_fields) and isinstance(result.get("ats_score"), (int, float))
