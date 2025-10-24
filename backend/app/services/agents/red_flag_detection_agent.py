"""
Red Flag Detection Agent for resume evaluation.
Identifies potential issues that could prevent interviews or reduce competitiveness.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class RedFlagDetectionAgent(BaseAgent):
    """Agent specialized in identifying resume red flags and concerns."""
    
    def __init__(self, ai_service=None):
        super().__init__("RedFlagDetectionAgent", ai_service)
    
    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Detect red flags and potential issues in the resume.
        
        Args:
            resume_content: The resume text to analyze
            context: Additional context (target roles, user preferences, etc.)
            
        Returns:
            Dictionary containing red flag analysis results
        """
        context = context or {}
        target_roles = context.get('target_roles', [])
        
        current_date = context.get('current_date', 'October 2025')
        current_year = context.get('current_year', 2025)
        
        prompt = f"""
        You are a senior recruiter with 15+ years of experience who has reviewed thousands of resumes.
        Your expertise is in identifying red flags and potential issues that prevent interviews or reduce competitiveness.
        Analyze this resume for any concerning patterns or issues.

        CURRENT DATE CONTEXT: Today is {current_date} (Year: {current_year})
        When analyzing dates, remember that dates before {current_year} are in the past, and dates in {current_year} or earlier are valid.

        Resume Content:
        {resume_content}

        Target Roles: {', '.join(target_roles) if target_roles else 'General technical roles'}

        Look for these specific red flag categories:

        1. JOB HOPPING PATTERNS:
           - Multiple jobs under 1 year
           - Unexplained gaps between jobs
           - Inconsistent career progression
           - Industry switching without explanation

        2. EMPLOYMENT GAPS:
           - Unexplained time periods
           - Suspiciously long gaps
           - Inconsistent dates
           - Missing employment history

        3. SCALE INCONSISTENCIES:
           - Claiming to manage 1000+ people with 2 years experience
           - Revenue claims that don't match role level
           - Technical achievements beyond experience level
   - Company size vs. claimed responsibilities mismatch

        4. GRAMMAR & FORMATTING ERRORS:
           - Spelling mistakes
           - Inconsistent formatting
           - Poor grammar
           - Unprofessional language

        5. GENERIC TEMPLATE LANGUAGE:
           - Overused buzzwords without substance
           - Generic job descriptions
           - Copy-paste template phrases
           - Lack of specific achievements

        6. CREDIBILITY ISSUES:
           - Unverifiable claims
           - Inconsistent information
           - Missing contact information
           - Suspicious company names or roles

        7. TECHNICAL INCONSISTENCIES:
           - Skills that don't match experience
           - Technologies used before they existed
           - Impossible technical achievements
           - Inconsistent technical depth

        Return your analysis as JSON in this exact format:
        {{
            "red_flag_score": 0-10,
            "critical_red_flags": [
                {{
                    "issue": "Specific issue description",
                    "severity": "critical|high|medium",
                    "impact": "Prevents interviews|Reduces competitiveness|Minor concern",
                    "evidence": "Specific evidence from resume",
                    "fix_suggestion": "How to address this issue"
                }}
            ],
            "minor_concerns": [
                {{
                    "issue": "Specific concern description",
                    "severity": "low|minor",
                    "impact": "Reduces competitiveness|Minor concern",
                    "evidence": "Specific evidence from resume",
                    "fix_suggestion": "How to address this concern"
                }}
            ],
            "pattern_analysis": {{
                "job_hopping": {{
                    "detected": true/false,
                    "pattern": "description of pattern",
                    "severity": "high|medium|low",
                    "explanation_suggestions": ["suggestion1", "suggestion2"]
                }},
                "employment_gaps": {{
                    "detected": true/false,
                    "gaps": ["gap1", "gap2"],
                    "severity": "high|medium|low",
                    "explanation_suggestions": ["suggestion1", "suggestion2"]
                }},
                "scale_inconsistencies": {{
                    "detected": true/false,
                    "inconsistencies": ["issue1", "issue2"],
                    "severity": "high|medium|low",
                    "verification_suggestions": ["suggestion1", "suggestion2"]
                }}
            }},
            "quality_issues": {{
                "grammar_errors": ["error1", "error2"],
                "formatting_issues": ["issue1", "issue2"],
                "generic_language": ["phrase1", "phrase2"],
                "professionalism_concerns": ["concern1", "concern2"]
            }},
            "credibility_concerns": {{
                "unverifiable_claims": ["claim1", "claim2"],
                "inconsistent_info": ["inconsistency1", "inconsistency2"],
                "missing_information": ["info1", "info2"],
                "suspicious_elements": ["element1", "element2"]
            }},
            "technical_red_flags": {{
                "skill_mismatches": ["mismatch1", "mismatch2"],
                "impossible_achievements": ["achievement1", "achievement2"],
                "timeline_inconsistencies": ["inconsistency1", "inconsistency2"],
                "depth_inconsistencies": ["inconsistency1", "inconsistency2"]
            }},
            "overall_assessment": {{
                "interview_risk": "high|medium|low",
                "competitiveness_impact": "severe|moderate|minor",
                "priority_fixes": ["fix1", "fix2", "fix3"],
                "general_recommendations": ["rec1", "rec2", "rec3"]
            }}
        }}

        Be thorough but fair. Distinguish between genuine red flags and minor concerns.
        Provide specific, actionable recommendations for addressing each issue.
        Consider the context of the target roles when assessing severity.
        """

        result = await self.llm_call(prompt)
        
        # Add agent-specific metadata
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "red_flag_detection",
            "target_roles": target_roles
        })
        
        return result
    
    def get_capabilities(self) -> list:
        """Return red flag detection capabilities."""
        return [
            "job_hopping_detection",
            "employment_gap_analysis",
            "credibility_assessment",
            "quality_issue_identification",
            "pattern_recognition"
        ]
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate red flag analysis result structure."""
        required_fields = ["red_flag_score", "critical_red_flags", "minor_concerns", "overall_assessment"]
        return all(field in result for field in required_fields) and isinstance(result.get("red_flag_score"), (int, float))
