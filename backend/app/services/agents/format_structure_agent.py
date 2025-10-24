"""
Format Structure Agent for resume evaluation.
Analyzes resume formatting, structure, and visual presentation.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class FormatStructureAgent(BaseAgent):
    """Agent specialized in resume formatting and structure analysis."""
    
    def __init__(self, ai_service=None):
        super().__init__("FormatStructureAgent", ai_service)
    
    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze resume formatting and structure.
        
        Args:
            resume_content: The resume text to analyze
            context: Additional context (target roles, preferences, etc.)
            
        Returns:
            Dictionary containing format analysis results
        """
        context = context or {}
        target_roles = context.get('target_roles', [])
        
        prompt = f"""
        You are a resume formatting and design expert with expertise in visual presentation and structure.
        Analyze this resume focusing ONLY on formatting, structure, and visual presentation quality.

        Resume Content:
        {resume_content}

        Target Roles: {', '.join(target_roles) if target_roles else 'General professional roles'}

        Evaluate the following formatting aspects:

        1. TECHNICAL FORMATTING COMPLIANCE (0-10):
           - 1-inch margins compliance (top, bottom, left, right)
           - 10-12pt body text verification (proper font size for readability)
           - ATS parsing compatibility (no text boxes, tables, or complex formatting)
           - PDF format validation and file integrity
           - Font consistency throughout document
           - Proper line spacing (1.0-1.15 recommended)

        2. VISUAL HIERARCHY (0-10):
           - Clear section headers and organization
           - Consistent font usage and sizing
           - Proper spacing and alignment
           - Visual flow and readability

        3. SECTION ORGANIZATION (0-10):
           - Logical order of sections
           - Appropriate section lengths
           - Clear section boundaries
           - Professional section headers

        4. BULLET POINT FORMATTING (0-10):
           - Consistent bullet point style
           - Proper indentation and alignment
           - Appropriate length and density
           - Clear action verb usage

        5. CONTACT INFORMATION (0-10):
           - Complete and accurate contact details
           - Professional presentation
           - Appropriate placement
           - Easy to find and read

        6. LENGTH AND DENSITY (0-10):
           - Appropriate resume length
           - Optimal information density
           - White space usage
           - Readability balance

        7. PROFESSIONAL PRESENTATION (0-10):
           - Overall visual appeal
           - Professional appearance
           - Consistency throughout
           - Error-free presentation

        Return your analysis as JSON in this exact format:
        {{
            "format_score": 0-10,
            "technical_formatting": {{
                "score": 0-10,
                "margin_compliance": "excellent|good|fair|poor",
                "font_size_check": "10-12pt|too_small|too_large|inconsistent",
                "ats_compatibility": "excellent|good|fair|poor",
                "pdf_validation": "valid|issues|major_problems",
                "line_spacing": "optimal|too_tight|too_loose",
                "formatting_issues": ["Text boxes detected", "Tables used", "Complex formatting found"],
                "improvements": ["Use standard margins", "Adjust font size to 11pt", "Remove formatting barriers"]
            }},
            "visual_hierarchy": {{
                "score": 0-10,
                "header_consistency": "excellent|good|fair|poor",
                "font_usage": "excellent|good|fair|poor",
                "spacing_quality": "excellent|good|fair|poor",
                "visual_flow": "excellent|good|fair|poor",
                "improvements": ["improvement1", "improvement2"]
            }},
            "section_organization": {{
                "score": 0-10,
                "section_order": "optimal|good|needs_improvement|poor",
                "section_lengths": "balanced|some_issues|unbalanced",
                "section_headers": "clear|unclear|missing",
                "section_boundaries": "clear|unclear|confusing",
                "recommendations": ["rec1", "rec2"]
            }},
            "bullet_point_analysis": {{
                "score": 0-10,
                "consistency": "excellent|good|fair|poor",
                "indentation": "proper|inconsistent|poor",
                "length_balance": "optimal|too_long|too_short",
                "action_verbs": "strong|moderate|weak",
                "improvements": ["improvement1", "improvement2"]
            }},
            "contact_information": {{
                "score": 0-10,
                "completeness": "complete|mostly_complete|incomplete",
                "presentation": "professional|adequate|unprofessional",
                "placement": "optimal|good|poor",
                "readability": "excellent|good|fair|poor",
                "issues": ["issue1", "issue2"]
            }},
            "length_density": {{
                "score": 0-10,
                "overall_length": "optimal|too_long|too_short",
                "information_density": "balanced|too_dense|too_sparse",
                "white_space": "appropriate|too_much|too_little",
                "readability": "excellent|good|fair|poor",
                "adjustments": ["adjustment1", "adjustment2"]
            }},
            "professional_presentation": {{
                "score": 0-10,
                "overall_appeal": "excellent|good|fair|poor",
                "consistency": "excellent|good|fair|poor",
                "error_free": true/false,
                "professional_look": "excellent|good|fair|poor",
                "overall_impression": "strong|moderate|weak"
            }},
            "critical_format_issues": [
                {{
                    "issue": "Specific formatting issue",
                    "severity": "critical|high|medium|low",
                    "impact": "Prevents scanning|Reduces readability|Minor concern",
                    "fix": "Specific fix suggestion"
                }}
            ],
            "format_recommendations": [
                {{
                    "category": "Visual Hierarchy|Section Organization|Bullet Points|Contact Info|Length|Professional",
                    "priority": "high|medium|low",
                    "recommendation": "Specific recommendation",
                    "impact": "High|Medium|Low"
                }}
            ],
            "template_suggestions": {{
                "current_style": "modern|traditional|creative|basic",
                "recommended_style": "modern|traditional|creative|basic",
                "reasoning": "Why this style is recommended",
                "template_examples": ["example1", "example2"]
            }}
        }}

        Focus on actionable formatting improvements that will enhance readability and professional presentation.
        Consider both ATS compatibility and human readability in your recommendations.
        """

        result = await self.llm_call(prompt)
        
        # Add agent-specific metadata
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "format_structure",
            "target_roles": target_roles
        })
        
        return result
    
    def get_capabilities(self) -> list:
        """Return format structure analysis capabilities."""
        return [
            "visual_hierarchy_analysis",
            "section_organization_review",
            "bullet_point_formatting",
            "contact_information_audit",
            "professional_presentation_assessment"
        ]
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate format analysis result structure."""
        required_fields = ["format_score", "technical_formatting", "visual_hierarchy", "section_organization", "critical_format_issues"]
        return all(field in result for field in required_fields) and isinstance(result.get("format_score"), (int, float))
