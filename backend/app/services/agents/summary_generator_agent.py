"""
Summary Generator Agent for resume evaluation.
Synthesizes results from all other agents into a comprehensive evaluation.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class SummaryGeneratorAgent(BaseAgent):
    """Agent specialized in synthesizing multi-agent analysis results."""
    
    def __init__(self, ai_service=None):
        super().__init__("SummaryGeneratorAgent", ai_service)
    
    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze method required by base class. This agent doesn't analyze resume content directly.
        Instead, it synthesizes results from other agents.
        """
        # This agent doesn't analyze resume content directly
        # It only synthesizes results from other agents
        return {
            "agent_name": self.agent_name,
            "analysis_type": "summary_generation",
            "note": "SummaryGeneratorAgent requires results from other agents to function"
        }
    
    async def generate(self, all_agent_results: Dict[str, Any], user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation summary from all agent results.
        
        Args:
            all_agent_results: Results from all evaluation agents
            user_profile: User context and preferences
            
        Returns:
            Dictionary containing comprehensive evaluation summary
        """
        user_profile = user_profile or {}
        
        prompt = f"""
        You are a senior resume optimization expert and career coach with 20+ years of experience.
        Synthesize the analysis from multiple specialized agents into a comprehensive, actionable evaluation.

        Agent Analysis Results:
        ATS Analysis: {all_agent_results.get('ats', {})}
        Experience Analysis: {all_agent_results.get('experience', {})}
        Skills Analysis: {all_agent_results.get('skills', {})}
        Format Analysis: {all_agent_results.get('format', {})}
        Red Flag Analysis: {all_agent_results.get('red_flags', {})}
        Company Fit Analysis: {all_agent_results.get('company_fit', {})}

        User Context: {user_profile}

        Create a comprehensive evaluation that:

        1. CALCULATES OVERALL SCORE (0-100):
           - Weight each agent's contribution appropriately
           - Consider critical issues and red flags
           - Factor in company fit and market positioning

        2. GENERATES EXECUTIVE SUMMARY (2-3 sentences):
           - Key strengths and positioning
           - Critical areas for improvement
           - Market competitiveness assessment

        3. IDENTIFIES TOP STRENGTHS (3-5 items):
           - Most compelling differentiators
           - Market-relevant advantages
   - Positioning opportunities

        4. IDENTIFIES CRITICAL IMPROVEMENTS (3-5 items):
           - Must-fix issues that prevent interviews
           - Strategic improvements for competitiveness
           - Quick wins for immediate impact

        5. PROVIDES SPECIFIC RECOMMENDATIONS:
           - Summary rewrite with examples
           - Experience bullet improvements
           - Skills section optimization
           - ATS optimization strategies

        6. ASSESSES MARKET POSITIONING:
           - Competitive level and salary range
           - Target role recommendations
           - Company type fit analysis

        Return your synthesis as JSON in this exact format:
        {{
            "overall_score": 0-100,
            "executive_summary": "2-3 sentence summary of key strengths, critical improvements, and market position",
            "strengths": [
                {{
                    "strength": "Specific strength description",
                    "impact": "Why this matters to employers",
                    "evidence": "Specific evidence from resume"
                }}
            ],
            "critical_improvements": {{
                "immediate_fixes": [
                    {{
                        "issue": "Critical issue description",
                        "impact": "Why this prevents interviews",
                        "fix": "Specific fix with example",
                        "priority": "critical|high"
                    }}
                ],
                "strategic_improvements": [
                    {{
                        "improvement": "Strategic improvement description",
                        "impact": "How this improves competitiveness",
                        "action": "Specific action to take",
                        "priority": "high|medium"
                    }}
                ],
                "nice_to_have": [
                    {{
                        "enhancement": "Nice-to-have enhancement",
                        "impact": "How this adds polish",
                        "action": "Specific action to take",
                        "priority": "low"
                    }}
                ]
            }},
            "specific_recommendations": {{
                "summary_rewrite": {{
                    "current": "Current summary (if any)",
                    "improved": "Enhanced summary with specific examples",
                    "reasoning": "Why this is better"
                }},
                "experience_bullets": [
                    {{
                        "current": "Current bullet point",
                        "improved": "Enhanced bullet point with metrics",
                        "reasoning": "Why this is more compelling"
                    }}
                ],
                "skills_optimization": [
                    {{
                        "action": "Add/remove/reorganize skill",
                        "reasoning": "Why this improves marketability",
                        "example": "Specific example of how to present"
                    }}
                ],
                "ats_optimization": [
                    {{
                        "action": "Specific ATS improvement",
                        "reasoning": "Why this helps parsing",
                        "implementation": "How to implement"
                    }}
                ]
            }},
            "market_positioning": {{
                "competitive_level": "Senior|Mid|Entry|Mixed",
                "salary_range": "Estimated salary range based on experience and skills",
                "target_roles": ["role1", "role2", "role3"],
                "company_fit": {{
                    "best_fit": "maang|startups|enterprise|mixed",
                    "fit_explanation": "Why this is the best fit",
                    "positioning_advice": "How to position for target companies"
                }},
                "market_competitiveness": "high|medium|low",
                "differentiation_factors": ["factor1", "factor2", "factor3"]
            }},
            "action_plan": {{
                "immediate_actions": [
                    {{
                        "action": "Specific action to take",
                        "timeline": "1-2 days|1 week|2 weeks",
                        "impact": "Expected impact on competitiveness"
                    }}
                ],
                "short_term_goals": [
                    {{
                        "goal": "Specific goal to achieve",
                        "timeline": "1-2 weeks|1 month",
                        "steps": ["step1", "step2", "step3"]
                    }}
                ],
                "long_term_development": [
                    {{
                        "development_area": "Area to develop",
                        "timeline": "3-6 months|6-12 months",
                        "resources": ["resource1", "resource2"]
                    }}
                ]
            }},
            "confidence_indicators": {{
                "ats_confidence": "high|medium|low",
                "experience_confidence": "high|medium|low",
                "skills_confidence": "high|medium|low",
                "overall_confidence": "high|medium|low"
            }}
        }}

        Focus on actionable, specific recommendations that will immediately improve the candidate's competitiveness.
        Prioritize fixes that prevent interviews over nice-to-have improvements.
        Consider the user's target roles and company preferences in all recommendations.
        """

        result = await self.llm_call(prompt)
        
        # Add agent-specific metadata
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "comprehensive_summary",
            "user_profile": user_profile,
            "agent_count": len(all_agent_results),
            "synthesis_timestamp": "2024-01-01T00:00:00Z"  # This would be actual timestamp
        })
        
        return result
    
    def get_capabilities(self) -> list:
        """Return summary generation capabilities."""
        return [
            "multi_agent_synthesis",
            "comprehensive_evaluation",
            "action_plan_generation",
            "market_positioning_analysis",
            "executive_summary_creation"
        ]
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate summary generation result structure."""
        required_fields = ["overall_score", "executive_summary", "strengths", "critical_improvements", "market_positioning"]
        return all(field in result for field in required_fields) and isinstance(result.get("overall_score"), (int, float))
