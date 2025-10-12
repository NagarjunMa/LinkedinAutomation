"""
Experience Analysis Agent for resume evaluation.
Analyzes work experience for impact, progression, and credibility.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class ExperienceAnalysisAgent(BaseAgent):
    """Agent specialized in work experience analysis."""
    
    def __init__(self, ai_service=None):
        super().__init__("ExperienceAnalysisAgent", ai_service)
    
    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze work experience for impact and progression.
        
        Args:
            resume_content: The resume text to analyze
            context: Additional context (target roles, user preferences, etc.)
            
        Returns:
            Dictionary containing experience analysis results
        """
        context = context or {}
        target_roles = context.get('target_roles', [])
        target_seniority = context.get('target_seniority', 'mid-level')
        years_experience = context.get('years_experience', 0)
        
        # Limit resume content length to prevent overly long prompts
        max_content_length = 8000
        if len(resume_content) > max_content_length:
            resume_content = resume_content[:max_content_length] + "... [truncated]"
            self.logger.warning(f"Resume content truncated to {max_content_length} characters")
        
        prompt = f"""
        You are a senior hiring manager with 15+ years of experience evaluating candidates for technical roles.
        Analyze this resume focusing ONLY on work experience quality, impact, and career progression.

        Resume Content:
        {resume_content}

        Target Roles: {', '.join(target_roles) if target_roles else 'General technical roles'}
        Target Seniority Level: {target_seniority}
        Years of Experience: {years_experience}

        SENIORITY-SPECIFIC EXPECTATIONS:
        Fresh Graduates/Entry-Level: Focus on internships, academic projects, hackathons, and learning potential
        Mid-Level (2-5 years): Focus on increasing project responsibility, skill development, and measurable outcomes
        Senior Level (5+ years): Focus on technical leadership, mentoring, architecture decisions, and business impact
        Principal/Staff Level (8+ years): Focus on strategic technical direction, cross-functional leadership, and organizational impact

        Evaluate the following aspects:

        1. IMPACT QUANTIFICATION (0-10):
           - Measurable outcomes and achievements
           - Revenue, cost savings, efficiency improvements
           - Scale indicators (users, transactions, team size)
           - Before/after comparisons

        2. CAREER PROGRESSION (0-10):
           - Clear advancement in responsibilities
           - Increasing scope and complexity
           - Leadership growth indicators
           - Skill development trajectory

        3. TECHNICAL LEADERSHIP (0-10):
           - Architecture and design decisions
           - Team mentoring and development
           - Technical strategy and planning
           - Innovation and problem-solving

        4. SCALE & CREDIBILITY (0-10):
           - Company size and reputation
           - Project complexity and scope
           - Industry recognition
           - Cross-functional collaboration

        5. ACHIEVEMENT DEPTH (0-10):
           - Specific technical accomplishments
           - Business impact measurement
           - Problem-solving examples
           - Innovation and creativity

        Return your analysis as JSON in this exact format:
        {{
            "experience_score": 0-10,
            "impact_analysis": {{
                "quantified_achievements": [
                    {{"achievement": "description", "impact": "measurement", "score": 0-10}}
                ],
                "missing_metrics": ["suggestion1", "suggestion2"],
                "impact_strength": "high|medium|low"
            }},
            "progression_analysis": {{
                "career_trajectory": "upward|lateral|mixed",
                "responsibility_growth": "clear|unclear|missing",
                "leadership_development": "strong|moderate|weak",
                "progression_concerns": ["issue1", "issue2"]
            }},
            "technical_leadership": {{
                "architecture_experience": "extensive|moderate|limited",
                "team_leadership": "strong|moderate|weak", 
                "innovation_examples": ["example1", "example2"],
                "leadership_gaps": ["gap1", "gap2"]
            }},
            "credibility_indicators": {{
                "company_reputation": "high|medium|low",
                "project_scale": "enterprise|mid|small",
                "industry_recognition": "strong|moderate|none",
                "cross_functional_work": "extensive|moderate|limited"
            }},
            "strengths": [
                "Specific strength 1",
                "Specific strength 2"
            ],
            "improvement_areas": [
                "Specific improvement 1", 
                "Specific improvement 2"
            ],
            "rewrite_suggestions": [
                {{"current": "current bullet point", "improved": "enhanced version"}}
            ],
            "experience_gaps": [
                "Missing experience type 1",
                "Missing experience type 2"
            ]
        }}

        Focus on actionable insights that will help the candidate better present their experience.
        Be specific about what makes experience compelling and what's missing.
        """

        result = await self.llm_call(prompt)
        
        # Add agent-specific metadata
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "experience_analysis",
            "target_roles": target_roles,
            "target_seniority": target_seniority,
            "years_experience": years_experience
        })
        
        return result
    
    def get_capabilities(self) -> list:
        """Return experience analysis capabilities."""
        return [
            "impact_quantification",
            "career_progression_analysis",
            "technical_leadership_assessment",
            "credibility_evaluation",
            "achievement_analysis"
        ]
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate experience analysis result structure."""
        required_fields = ["experience_score", "impact_analysis", "progression_analysis", "strengths", "improvement_areas"]
        return all(field in result for field in required_fields) and isinstance(result.get("experience_score"), (int, float))
