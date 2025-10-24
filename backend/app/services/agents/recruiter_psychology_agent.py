"""
Recruiter Psychology Agent for resume evaluation.
Analyzes resume optimization for recruiter scanning patterns, cognitive processing, and decision-making psychology.
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class RecruiterPsychologyAgent(BaseAgent):
    """Agent specialized in recruiter psychology and scanning behavior optimization."""

    def __init__(self, ai_service=None):
        super().__init__("RecruiterPsychologyAgent", ai_service)

    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze resume for recruiter psychology optimization and scanning behavior.

        Args:
            resume_content: The resume text to analyze
            context: Additional context (target roles, seniority level, etc.)

        Returns:
            Dictionary containing recruiter psychology analysis results
        """
        context = context or {}
        target_roles = context.get('target_roles', [])
        target_seniority = context.get('target_seniority', 'mid-level')

        prompt = f"""
        You are a senior recruiting expert and organizational psychologist with deep expertise in recruiter scanning behavior, cognitive processing patterns, and hiring decision psychology.
        Analyze this resume for optimal recruiter psychology and scanning behavior compatibility.

        Resume Content:
        {resume_content}

        Target Roles: {', '.join(target_roles) if target_roles else 'General professional roles'}
        Target Seniority: {target_seniority}

        RECRUITER PSYCHOLOGY ANALYSIS AREAS:

        1. F-PATTERN READING OPTIMIZATION (0-10):
           - Left-side information density and power
           - Strategic placement of critical keywords
           - Horizontal scanning pathway optimization
           - Visual anchors for eye movement guidance
           - Section header prominence and scannability

        2. FIRST BULLET STRENGTH VALIDATION (0-10):
           - Impact and power of first bullet points
           - Achievement-focused opening statements
           - Quantified results in primary positions
           - Action verb strength and variety
           - Immediate value demonstration

        3. WHITE SPACE SCANNING FLOW (0-10):
           - Strategic white space usage for guidance
           - Information grouping and visual breathing room
           - Cognitive load management through spacing
           - Reading flow optimization
           - Visual hierarchy through space utilization

        4. STRATEGIC BOLD TEXT USAGE (0-10):
           - Critical information highlighting effectiveness
           - Company names and job titles prominence
           - Key achievements and metrics emphasis
           - Skills and technologies visibility
           - Overuse vs. underuse balance assessment

        5. COGNITIVE LOAD MANAGEMENT (0-10):
           - Information processing ease for time-pressed recruiters
           - Decision-making pathway clarity
           - Complexity reduction and simplification
           - Parallel processing optimization
           - Mental fatigue prevention strategies

        6. PATTERN RECOGNITION FACILITATION (0-10):
           - Familiar resume structure and conventions
           - Industry-standard formatting adherence
           - Predictable information placement
           - Recognition shortcuts for quick assessment
           - Template familiarity advantages

        Return your analysis as JSON in this exact format:
        {{
            "psychology_score": 0-10,
            "f_pattern_optimization": {{
                "score": 0-10,
                "left_side_power": "high|medium|low",
                "keyword_placement": "strategic|adequate|poor",
                "horizontal_scanning": "optimized|good|needs_improvement",
                "visual_anchors": "excellent|good|few|none",
                "section_header_prominence": "high|medium|low",
                "f_pattern_issues": [
                    "Critical info buried on right side",
                    "Weak left-aligned content",
                    "Poor horizontal eye flow"
                ],
                "f_pattern_improvements": [
                    "Move key achievements to left margin",
                    "Bold critical keywords in first words",
                    "Improve section header visibility",
                    "Optimize bullet point openings"
                ]
            }},
            "first_bullet_analysis": {{
                "score": 0-10,
                "impact_strength": "high|medium|low",
                "achievement_focus": "strong|moderate|weak",
                "quantification_usage": "excellent|good|minimal|none",
                "action_verb_power": "strong|moderate|weak",
                "value_demonstration": "immediate|delayed|unclear|missing",
                "first_bullets_evaluation": [
                    {{
                        "section": "Experience section name",
                        "current_first_bullet": "Exact text of first bullet point",
                        "strength_rating": "strong|moderate|weak",
                        "issues": ["Issue 1", "Issue 2"],
                        "improved_bullet": "Rewritten first bullet with impact",
                        "impact_increase": "High|Medium|Low"
                    }}
                ],
                "first_bullet_strategy": "Overall approach to strengthen openings"
            }},
            "white_space_flow": {{
                "score": 0-10,
                "strategic_usage": "excellent|good|fair|poor",
                "information_grouping": "clear|adequate|confusing",
                "cognitive_breathing_room": "optimal|adequate|cramped|excessive",
                "reading_flow": "smooth|adequate|choppy|confusing",
                "visual_hierarchy": "clear|somewhat_clear|unclear",
                "white_space_issues": [
                    "Too cramped in experience section",
                    "Inconsistent spacing between sections",
                    "Poor grouping of related information"
                ],
                "spacing_improvements": [
                    "Add consistent spacing between roles",
                    "Group related achievements together",
                    "Create visual breaks between sections",
                    "Optimize line spacing for readability"
                ]
            }},
            "bold_text_strategy": {{
                "score": 0-10,
                "usage_effectiveness": "optimal|good|overused|underused",
                "company_job_prominence": "excellent|good|fair|poor",
                "achievement_emphasis": "strong|moderate|weak|none",
                "skills_visibility": "high|medium|low",
                "balance_assessment": "perfect|good|too_much|too_little",
                "current_bold_usage": [
                    "Company names: Yes/No",
                    "Job titles: Yes/No",
                    "Key metrics: Yes/No",
                    "Skills: Yes/No",
                    "Achievements: Yes/No"
                ],
                "bold_recommendations": [
                    "Bold all company names for quick scanning",
                    "Emphasize key metrics and achievements",
                    "Highlight relevant technical skills",
                    "Bold job titles for hierarchy clarity"
                ],
                "overbolding_risks": ["Current overuse issues if any"]
            }},
            "cognitive_load_assessment": {{
                "score": 0-10,
                "processing_ease": "very_easy|easy|moderate|difficult|overwhelming",
                "decision_pathway_clarity": "clear|somewhat_clear|unclear|confusing",
                "complexity_level": "appropriate|slightly_high|too_complex|too_simple",
                "parallel_processing": "supported|somewhat_supported|not_supported",
                "fatigue_prevention": "excellent|good|fair|poor",
                "cognitive_load_factors": [
                    "Information density per section",
                    "Visual complexity level",
                    "Reading effort required",
                    "Decision points clarity"
                ],
                "load_reduction_strategies": [
                    "Simplify dense sections",
                    "Break up large text blocks",
                    "Use more visual hierarchy",
                    "Reduce cognitive switching"
                ]
            }},
            "pattern_recognition": {{
                "score": 0-10,
                "structure_familiarity": "highly_familiar|familiar|somewhat_familiar|unfamiliar",
                "industry_standard_adherence": "excellent|good|fair|poor",
                "information_predictability": "highly_predictable|predictable|somewhat_unpredictable|confusing",
                "recognition_shortcuts": "many|some|few|none",
                "template_advantages": "high|medium|low|none",
                "recognition_enhancers": [
                    "Use standard section headers",
                    "Follow conventional chronological order",
                    "Place contact info in expected location",
                    "Use familiar bullet point styles"
                ],
                "pattern_disruptions": [
                    "Unusual section ordering",
                    "Non-standard formatting",
                    "Unexpected information placement"
                ]
            }},
            "scanning_behavior_optimization": {{
                "attention_capture_seconds": "0-3|4-7|8-15|16+",
                "key_info_findability": "immediate|quick|requires_search|difficult",
                "scanning_pathway_clarity": "clear|somewhat_clear|unclear|confusing",
                "visual_stopping_points": "strategic|adequate|poor|none",
                "recruiter_efficiency_score": 0-10,
                "scanning_improvements": [
                    "Create stronger visual anchors",
                    "Improve information hierarchy",
                    "Add strategic visual breaks",
                    "Optimize keyword placement"
                ]
            }},
            "psychological_triggers": {{
                "authority_signals": "strong|moderate|weak|none",
                "social_proof_elements": "excellent|good|minimal|none",
                "scarcity_indicators": "present|subtle|none",
                "relevance_demonstration": "immediate|clear|unclear|missing",
                "trust_building_factors": "strong|moderate|weak|poor",
                "trigger_optimization": [
                    "Add more authority indicators",
                    "Include social proof elements",
                    "Demonstrate immediate relevance",
                    "Build trust through specificity"
                ]
            }},
            "critical_psychology_fixes": [
                {{
                    "priority": 1,
                    "psychological_principle": "F-pattern|Cognitive load|Pattern recognition|etc.",
                    "current_issue": "Specific psychology issue",
                    "recruiter_impact": "How this affects recruiter behavior",
                    "fix_action": "Specific action to take",
                    "before_example": "Current problematic text/layout",
                    "after_example": "Psychology-optimized version",
                    "expected_improvement": "Specific behavioral change expected"
                }}
            ],
            "recruiter_decision_facilitation": {{
                "yes_no_clarity": "crystal_clear|clear|unclear|very_unclear",
                "qualification_speed": "immediate|quick|slow|very_slow",
                "interest_generation": "high|medium|low|none",
                "next_step_motivation": "strong|moderate|weak|none",
                "overall_psychology_effectiveness": "excellent|good|fair|poor"
            }}
        }}

        Focus on evidence-based recruiter psychology principles and scanning behavior research.
        Prioritize changes that reduce cognitive load while maximizing information processing speed.
        Consider the time pressure and volume constraints that recruiters face daily.
        Ensure recommendations align with established patterns in recruitment psychology.
        """

        result = await self.llm_call(prompt)

        # Add agent-specific metadata
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "recruiter_psychology",
            "target_roles": target_roles,
            "target_seniority": target_seniority
        })

        return result

    def get_capabilities(self) -> list:
        """Return recruiter psychology analysis capabilities."""
        return [
            "f_pattern_reading_optimization",
            "first_bullet_strength_validation",
            "white_space_scanning_flow",
            "strategic_bold_text_usage",
            "cognitive_load_management",
            "pattern_recognition_facilitation",
            "scanning_behavior_optimization",
            "psychological_triggers_analysis",
            "recruiter_decision_facilitation"
        ]

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate recruiter psychology analysis result structure."""
        required_fields = ["psychology_score", "f_pattern_optimization", "first_bullet_analysis", "white_space_flow", "bold_text_strategy"]
        return all(field in result for field in required_fields) and isinstance(result.get("psychology_score"), (int, float))