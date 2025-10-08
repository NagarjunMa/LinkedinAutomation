"""
Skills Assessment Agent for resume evaluation.
Analyzes technical skills for relevance, depth, and market alignment.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class SkillsAssessmentAgent(BaseAgent):
    """Agent specialized in technical skills analysis."""
    
    def __init__(self, ai_service=None):
        super().__init__("SkillsAssessmentAgent", ai_service)
        # Market trends data - in production, this would come from a database or API
        self.market_trends = {
            "2024_hot_skills": [
                "AI/ML", "Cloud Computing", "DevOps", "Cybersecurity", 
                "Data Engineering", "React", "Python", "Kubernetes",
                "TypeScript", "AWS", "Docker", "GraphQL"
            ],
            "emerging_skills": [
                "Generative AI", "Edge Computing", "Quantum Computing",
                "Blockchain", "IoT", "AR/VR", "Web3"
            ],
            "declining_skills": [
                "jQuery", "AngularJS", "PHP", "Flash", "Silverlight"
            ]
        }
    
    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze technical skills for market relevance and depth.
        
        Args:
            resume_content: The resume text to analyze
            context: Additional context (target roles, industry, etc.)
            
        Returns:
            Dictionary containing skills analysis results
        """
        context = context or {}
        target_roles = context.get('target_roles', [])
        industry = context.get('industry', 'Technology')
        
        prompt = f"""
        You are a technical skills expert and hiring manager with deep knowledge of current technology trends.
        Analyze this resume focusing ONLY on technical skills, their relevance, and market alignment.

        Resume Content:
        {resume_content}

        Target Roles: {', '.join(target_roles) if target_roles else 'General technical roles'}
        Industry: {industry}

        Current Market Trends (2024-2025):
        Hot Skills: {', '.join(self.market_trends['2024_hot_skills'])}
        Emerging Skills: {', '.join(self.market_trends['emerging_skills'])}
        Declining Skills: {', '.join(self.market_trends['declining_skills'])}

        Evaluate the following aspects:

        1. SKILL RELEVANCE (0-10):
           - Alignment with target roles
           - Current market demand
           - Industry-specific requirements
           - Future-proofing potential

        2. TECHNICAL DEPTH (0-10):
           - Proficiency levels indicated
           - Years of experience per skill
           - Project complexity demonstrated
           - Certification and training

        3. SKILLS ORGANIZATION (0-10):
           - Clear categorization
           - Logical grouping
           - Proficiency indicators
           - Easy scanning for recruiters

        4. MARKET ALIGNMENT (0-10):
           - Hot skills presence
           - Emerging skills awareness
           - Outdated skills removal
           - Skill combination strategy

        5. COMPLETENESS (0-10):
           - Core skills for target roles
           - Supporting skills
           - Soft skills integration
   - Missing critical skills

        Return your analysis as JSON in this exact format:
        {{
            "skills_score": 0-10,
            "skill_analysis": {{
                "hot_skills_present": ["skill1", "skill2"],
                "hot_skills_missing": ["skill3", "skill4"],
                "emerging_skills": ["skill5", "skill6"],
                "outdated_skills": ["skill7", "skill8"],
                "skill_depth_indicators": {{
                    "expert": ["skill1", "skill2"],
                    "proficient": ["skill3", "skill4"],
                    "familiar": ["skill5", "skill6"]
                }}
            }},
            "market_alignment": {{
                "demand_score": 0-10,
                "future_relevance": 0-10,
                "competitive_advantage": "high|medium|low",
                "skill_gaps": ["gap1", "gap2"]
            }},
            "organization_quality": {{
                "categorization": "excellent|good|fair|poor",
                "proficiency_indicators": "clear|unclear|missing",
                "scanning_ease": "high|medium|low",
                "improvement_suggestions": ["suggestion1", "suggestion2"]
            }},
            "role_specific_analysis": {{
                "core_skills_coverage": 0-10,
                "missing_core_skills": ["skill1", "skill2"],
                "nice_to_have_skills": ["skill3", "skill4"],
                "overqualified_areas": ["area1", "area2"]
            }},
            "recommendations": {{
                "add_skills": [
                    {{"skill": "skill_name", "reason": "why important", "priority": "high|medium|low"}}
                ],
                "remove_skills": [
                    {{"skill": "skill_name", "reason": "why remove"}}
                ],
                "reorganize_suggestions": ["suggestion1", "suggestion2"],
                "proficiency_improvements": ["improvement1", "improvement2"]
            }},
            "strengths": [
                "Specific strength 1",
                "Specific strength 2"
            ],
            "critical_gaps": [
                "Missing critical skill 1",
                "Missing critical skill 2"
            ]
        }}

        Focus on actionable recommendations that will improve the candidate's marketability.
        Consider both current market needs and future trends.
        """

        result = await self.llm_call(prompt)
        
        # Add agent-specific metadata
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "skills_assessment",
            "target_roles": target_roles,
            "industry": industry,
            "market_trends_version": "2024-2025"
        })
        
        return result
    
    def get_capabilities(self) -> list:
        """Return skills assessment capabilities."""
        return [
            "technical_skills_analysis",
            "market_relevance_assessment",
            "skill_depth_evaluation",
            "organization_quality_review",
            "trend_alignment_analysis"
        ]
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate skills analysis result structure."""
        required_fields = ["skills_score", "skill_analysis", "market_alignment", "recommendations"]
        return all(field in result for field in required_fields) and isinstance(result.get("skills_score"), (int, float))
