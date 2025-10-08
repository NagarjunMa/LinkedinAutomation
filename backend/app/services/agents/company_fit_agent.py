"""
Company Fit Agent for resume evaluation.
Analyzes resume fit for different company types and cultures.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class CompanyFitAgent(BaseAgent):
    """Agent specialized in company culture and hiring fit analysis."""
    
    def __init__(self, ai_service=None):
        super().__init__("CompanyFitAgent", ai_service)
        # Company type characteristics - in production, this would come from a database
        self.company_profiles = {
            "maang": {
                "name": "MAANG Companies",
                "characteristics": [
                    "Large scale systems", "High performance", "Innovation focus",
                    "Leadership experience", "Technical depth", "Global impact",
                    "Fast-paced environment", "High standards"
                ],
                "key_indicators": [
                    "Scalable system experience", "Team leadership", "Technical innovation",
                    "Cross-functional collaboration", "High-impact projects", "Mentoring experience"
                ]
            },
            "startups": {
                "name": "Startups",
                "characteristics": [
                    "Versatility", "Speed of execution", "Resource constraints",
                    "Wear multiple hats", "Adaptability", "Growth mindset",
                    "Risk tolerance", "Innovation focus"
                ],
                "key_indicators": [
                    "Full-stack experience", "Rapid prototyping", "Startup experience",
                    "Product ownership", "Customer focus", "Agile methodologies"
                ]
            },
            "enterprise": {
                "name": "Enterprise Companies",
                "characteristics": [
                    "Process orientation", "Compliance focus", "Stability",
                    "Business acumen", "Stakeholder management", "Risk management",
                    "Documentation", "Long-term thinking"
                ],
                "key_indicators": [
                    "Enterprise software experience", "Compliance knowledge",
                    "Stakeholder management", "Process improvement", "Business impact",
                    "Documentation skills"
                ]
            }
        }
    
    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze resume fit for different company types.
        
        Args:
            resume_content: The resume text to analyze
            context: Additional context (target companies, preferences, etc.)
            
        Returns:
            Dictionary containing company fit analysis results
        """
        context = context or {}
        target_companies = context.get('target_companies', ['maang', 'startups', 'enterprise'])
        preferred_company_size = context.get('preferred_company_size', 'any')
        
        prompt = f"""
        You are a company culture and hiring expert with deep knowledge of different organizational types.
        Analyze this resume for fit with various company cultures and hiring patterns.

        Resume Content:
        {resume_content}

        Target Company Types: {', '.join(target_companies)}
        Preferred Company Size: {preferred_company_size}

        Company Type Profiles:

        MAANG COMPANIES (Meta, Apple, Amazon, Netflix, Google):
        - Characteristics: Large scale systems, high performance, innovation focus, leadership experience
        - Key Indicators: Scalable system experience, team leadership, technical innovation, cross-functional work
        - Hiring Focus: Technical depth, leadership potential, high-impact achievements, global perspective

        STARTUPS:
        - Characteristics: Versatility, speed, resource constraints, multiple hats, adaptability
        - Key Indicators: Full-stack experience, rapid prototyping, startup experience, product ownership
        - Hiring Focus: Versatility, growth mindset, customer focus, agile methodologies

        ENTERPRISE COMPANIES:
        - Characteristics: Process orientation, compliance, stability, business acumen, stakeholder management
        - Key Indicators: Enterprise software experience, compliance knowledge, stakeholder management
        - Hiring Focus: Process improvement, business impact, documentation, long-term thinking

        Evaluate fit for each company type:

        1. MAANG FIT (0-10):
           - Technical depth and innovation
           - Leadership and mentoring experience
           - Scale and impact of projects
           - Cross-functional collaboration

        2. STARTUP FIT (0-10):
           - Versatility and adaptability
           - Full-stack capabilities
           - Growth mindset and risk tolerance
           - Customer and product focus

        3. ENTERPRISE FIT (0-10):
           - Process and compliance orientation
           - Business acumen and stakeholder management
           - Documentation and long-term thinking
           - Stability and reliability focus

        Return your analysis as JSON in this exact format:
        {{
            "company_fit_scores": {{
                "maang": {{
                    "score": 0-10,
                    "strengths": ["strength1", "strength2"],
                    "gaps": ["gap1", "gap2"],
                    "positioning_advice": "How to position for MAANG companies"
                }},
                "startups": {{
                    "score": 0-10,
                    "strengths": ["strength1", "strength2"],
                    "gaps": ["gap1", "gap2"],
                    "positioning_advice": "How to position for startups"
                }},
                "enterprise": {{
                    "score": 0-10,
                    "strengths": ["strength1", "strength2"],
                    "gaps": ["gap1", "gap2"],
                    "positioning_advice": "How to position for enterprise"
                }}
            }},
            "overall_fit_analysis": {{
                "best_fit": "maang|startups|enterprise|mixed",
                "fit_explanation": "Why this is the best fit",
                "versatility_score": 0-10,
                "adaptability_indicators": ["indicator1", "indicator2"]
            }},
            "positioning_strategies": {{
                "maang_positioning": {{
                    "key_messages": ["message1", "message2"],
                    "resume_highlights": ["highlight1", "highlight2"],
                    "interview_prep": ["prep1", "prep2"]
                }},
                "startup_positioning": {{
                    "key_messages": ["message1", "message2"],
                    "resume_highlights": ["highlight1", "highlight2"],
                    "interview_prep": ["prep1", "prep2"]
                }},
                "enterprise_positioning": {{
                    "key_messages": ["message1", "message2"],
                    "resume_highlights": ["highlight1", "highlight2"],
                    "interview_prep": ["prep1", "prep2"]
                }}
            }},
            "culture_alignment": {{
                "work_style": "collaborative|independent|mixed",
                "innovation_focus": "high|medium|low",
                "risk_tolerance": "high|medium|low",
                "growth_mindset": "strong|moderate|weak"
            }},
            "recommendations": {{
                "resume_tailoring": [
                    {{"company_type": "maang", "changes": ["change1", "change2"]}},
                    {{"company_type": "startups", "changes": ["change1", "change2"]}},
                    {{"company_type": "enterprise", "changes": ["change1", "change2"]}}
                ],
                "skill_development": [
                    {{"skill": "skill1", "priority": "high|medium|low", "reason": "why important"}}
                ],
                "experience_gaps": [
                    {{"experience": "experience1", "company_types": ["maang", "startups"], "priority": "high|medium|low"}}
                ]
            }}
        }}

        Focus on actionable positioning advice that will help the candidate succeed with their target company types.
        Consider both current fit and potential for growth within each company culture.
        """

        result = await self.llm_call(prompt)
        
        # Add agent-specific metadata
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "company_fit",
            "target_companies": target_companies,
            "preferred_company_size": preferred_company_size
        })
        
        return result
    
    def get_capabilities(self) -> list:
        """Return company fit analysis capabilities."""
        return [
            "company_culture_assessment",
            "hiring_pattern_analysis",
            "positioning_strategy",
            "culture_alignment_evaluation",
            "multi_company_fit_analysis"
        ]
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate company fit analysis result structure."""
        required_fields = ["company_fit_scores", "overall_fit_analysis", "positioning_strategies"]
        return all(field in result for field in required_fields) and "company_fit_scores" in result
