"""
Above-Fold Impact Agent for resume evaluation.
Analyzes the top third of the resume for maximum recruiter impact within 7 seconds.
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class AboveFoldImpactAgent(BaseAgent):
    """Agent specialized in evaluating above-fold resume impact for recruiter attention."""

    def __init__(self, ai_service=None):
        super().__init__("AboveFoldImpactAgent", ai_service)

    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze resume above-fold impact and recruiter psychology factors.

        Args:
            resume_content: The resume text to analyze
            context: Additional context (target roles, seniority level, etc.)

        Returns:
            Dictionary containing above-fold impact analysis results
        """
        context = context or {}
        target_roles = context.get('target_roles', [])
        target_seniority = context.get('target_seniority', 'mid-level')

        prompt = f"""
        You are a senior recruiting expert and resume optimization specialist with deep knowledge of recruiter psychology and F-pattern reading behavior.
        Analyze this resume focusing on the ABOVE-FOLD IMPACT - the top third that recruiters see in their first 7-second scan.

        Resume Content:
        {resume_content}

        Target Roles: {', '.join(target_roles) if target_roles else 'General professional roles'}
        Target Seniority: {target_seniority}

        CRITICAL ANALYSIS AREAS:

        1. TOP-THIRD CONTENT EVALUATION (0-10):
           - Highest-value information placement in top third
           - Immediate role/level signal clarity
           - Key achievements visibility
           - Years of experience prominence
           - Skills relevance at first glance

        2. HEADLINE OPTIMIZATION (0-10):
           - Professional title clarity and impact
           - Role level signal strength (Junior/Mid/Senior/Lead)
           - Industry relevance and positioning
           - Value proposition immediacy
           - Keyword density for target roles

        3. 7-SECOND RECRUITER VALUE TEST (0-10):
           - Can recruiter determine fit in 7 seconds?
           - Clear value proposition visibility
           - Relevant experience years immediately apparent
           - Skills match for target role obvious
           - Professional level instantly recognizable

        4. F-PATTERN READING OPTIMIZATION (0-10):
           - Left-aligned key information placement
           - Strategic bolding of crucial details
           - Scannable first lines of sections
           - Horizontal eye movement optimization
           - Vertical scanning pathway efficiency

        5. CONTACT AND HEADER IMPACT (0-10):
           - Professional presentation and completeness
           - Geographic location clarity
           - LinkedIn/portfolio accessibility
           - Phone/email professionalism
           - Overall header visual impact

        6. SUMMARY/OBJECTIVE EFFECTIVENESS (0-10):
           - Immediate value proposition delivery
           - Target role alignment strength
           - Years of experience prominence
           - Key skills highlighting
           - Call-to-action effectiveness

        Return your analysis as JSON in this exact format:
        {{
            "above_fold_score": 0-10,
            "top_third_content": {{
                "score": 0-10,
                "highest_value_placement": "excellent|good|fair|poor",
                "role_level_clarity": "immediately_clear|somewhat_clear|unclear|missing",
                "key_achievements_visibility": "prominent|visible|buried|missing",
                "experience_years_prominence": "immediately_visible|somewhat_visible|unclear|missing",
                "skills_relevance_visibility": "excellent|good|fair|poor",
                "critical_improvements": [
                    "Move years of experience to header area",
                    "Highlight key achievement in summary",
                    "Improve role title prominence"
                ]
            }},
            "headline_optimization": {{
                "score": 0-10,
                "professional_title_impact": "strong|moderate|weak|missing",
                "role_level_signal": "clear_senior|clear_mid|clear_junior|unclear|missing",
                "industry_relevance": "highly_relevant|relevant|somewhat_relevant|irrelevant",
                "value_proposition_strength": "compelling|good|weak|missing",
                "keyword_optimization": "excellent|good|fair|poor",
                "current_headline": "Extract current headline from resume",
                "improved_headline": "Suggested improved headline with role level and value prop",
                "headline_issues": ["Issue 1", "Issue 2", "Issue 3"]
            }},
            "seven_second_test": {{
                "score": 0-10,
                "recruiter_fit_determination": "immediate|quick|slow|impossible",
                "value_proposition_visibility": "crystal_clear|clear|unclear|missing",
                "experience_years_clarity": "immediately_apparent|findable|buried|missing",
                "skills_match_obviousness": "obvious|apparent|requires_search|unclear",
                "professional_level_recognition": "instant|quick|slow|unclear",
                "seven_second_improvements": [
                    "Add years of experience to name line",
                    "Bold key skills in summary",
                    "Improve job title prominence",
                    "Highlight relevant achievements"
                ],
                "recruiter_questions_answered": [
                    "What is their experience level?",
                    "Do they have relevant skills?",
                    "Are they the right seniority?",
                    "What is their biggest achievement?"
                ],
                "recruiter_questions_unanswered": [
                    "Questions still unclear after 7 seconds"
                ]
            }},
            "f_pattern_optimization": {{
                "score": 0-10,
                "left_alignment_effectiveness": "excellent|good|fair|poor",
                "strategic_bolding_usage": "optimal|good|minimal|none",
                "scannable_first_lines": "excellent|good|fair|poor",
                "horizontal_eye_movement": "optimized|good|fair|poor",
                "vertical_scanning_pathway": "clear|somewhat_clear|unclear|confusing",
                "f_pattern_improvements": [
                    "Bold key achievements in left column",
                    "Improve section header prominence",
                    "Optimize bullet point first words",
                    "Enhance left-side information density"
                ]
            }},
            "contact_header_impact": {{
                "score": 0-10,
                "professional_presentation": "excellent|good|fair|poor",
                "completeness_check": "complete|mostly_complete|incomplete",
                "geographic_clarity": "clear|somewhat_clear|unclear|missing",
                "digital_presence_accessibility": "excellent|good|fair|poor",
                "contact_professionalism": "professional|adequate|unprofessional",
                "header_visual_impact": "strong|moderate|weak|poor",
                "header_improvements": [
                    "Add LinkedIn URL",
                    "Include city, state format",
                    "Use professional email format",
                    "Improve visual hierarchy"
                ]
            }},
            "summary_effectiveness": {{
                "score": 0-10,
                "value_proposition_delivery": "immediate|quick|slow|missing",
                "target_role_alignment": "perfect|good|fair|poor",
                "experience_years_prominence": "prominent|visible|unclear|missing",
                "key_skills_highlighting": "excellent|good|fair|poor",
                "call_to_action_strength": "strong|moderate|weak|missing",
                "current_summary": "Extract current summary/objective from resume",
                "improved_summary": "Rewritten summary optimized for above-fold impact",
                "summary_issues": [
                    "Too generic",
                    "Missing years of experience",
                    "No value proposition",
                    "Weak role targeting"
                ]
            }},
            "critical_above_fold_fixes": [
                {{
                    "priority": 1,
                    "issue": "Most critical above-fold issue",
                    "current_problem": "What's currently wrong",
                    "impact": "Why this hurts recruiter perception",
                    "fix": "Specific action to take",
                    "before_example": "Current text or layout",
                    "after_example": "Improved version",
                    "estimated_impact": "High|Medium|Low recruiter attention improvement"
                }}
            ],
            "recruiter_psychology_insights": {{
                "attention_span_optimization": "How well resume works with 7-second rule",
                "cognitive_load_assessment": "Information processing ease for recruiters",
                "pattern_recognition_support": "How well resume supports F-pattern reading",
                "decision_making_facilitation": "How easily recruiters can make yes/no decisions",
                "visual_hierarchy_effectiveness": "How well visual design guides attention"
            }},
            "competitive_positioning": {{
                "above_fold_strength": "How resume compares to typical candidates",
                "differentiation_factors": ["Factor 1", "Factor 2", "Factor 3"],
                "attention_grabbing_elements": ["Element 1", "Element 2"],
                "missed_opportunities": ["Opportunity 1", "Opportunity 2"],
                "positioning_recommendations": [
                    "Specific actions to improve competitive position"
                ]
            }}
        }}

        Focus on actionable improvements that maximize recruiter attention and decision-making speed.
        Prioritize changes that work within the first 7 seconds of resume scanning.
        Consider F-pattern reading behavior and visual hierarchy principles.
        Ensure recommendations align with target role and seniority level expectations.
        """

        result = await self.llm_call(prompt)

        # Add agent-specific metadata
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "above_fold_impact",
            "target_roles": target_roles,
            "target_seniority": target_seniority
        })

        return result

    def get_capabilities(self) -> list:
        """Return above-fold impact analysis capabilities."""
        return [
            "top_third_content_evaluation",
            "headline_optimization",
            "seven_second_recruiter_test",
            "f_pattern_reading_optimization",
            "contact_header_impact_analysis",
            "summary_effectiveness_evaluation",
            "recruiter_psychology_insights",
            "competitive_positioning_analysis"
        ]

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate above-fold impact analysis result structure."""
        required_fields = ["above_fold_score", "top_third_content", "headline_optimization", "seven_second_test", "critical_above_fold_fixes"]
        return all(field in result for field in required_fields) and isinstance(result.get("above_fold_score"), (int, float))