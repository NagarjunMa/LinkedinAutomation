"""
Detailed Analysis Agent for resume evaluation.
Provides comprehensive, actionable feedback with specific changes needed.
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class DetailedAnalysisAgent(BaseAgent):
    """Agent specialized in providing detailed, actionable resume feedback."""
    
    def __init__(self, ai_service=None):
        super().__init__("DetailedAnalysisAgent", ai_service)
    
    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze resume and provide detailed, actionable feedback.
        
        Args:
            resume_content: The resume text to analyze
            context: Additional context (target roles, etc.)
            
        Returns:
            Dictionary containing detailed analysis results
        """
        context = context or {}
        target_roles = context.get('target_roles', [])
        target_seniority = context.get('target_seniority', 'mid-level')
        
        # Limit resume content length to prevent overly long prompts
        max_content_length = 12000  # Increased for more detailed analysis
        if len(resume_content) > max_content_length:
            resume_content = resume_content[:max_content_length] + "... [truncated]"
            self.logger.warning(f"Resume content truncated to {max_content_length} characters")
        
        current_date = context.get('current_date', 'October 2025')
        current_year = context.get('current_year', 2025)
        
        prompt = f"""
        You are a senior resume optimization expert and career coach with 20+ years of experience.
        Analyze this resume LINE BY LINE and provide detailed, actionable feedback with SPECIFIC changes needed.

        IMPORTANT: Use the EXACT text from the resume in your analysis. Quote the actual sentences and bullet points that need improvement.

        CURRENT DATE CONTEXT: Today is {current_date} (Year: {current_year})
        When analyzing dates, remember that dates before {current_year} are in the past, and dates in {current_year} or earlier are valid.

        Resume Content:
        {resume_content}

        Target Roles: {', '.join(target_roles) if target_roles else 'General'}
        Target Seniority Level: {target_seniority}

        SENIORITY-SPECIFIC EVALUATION CRITERIA:
        For Fresh Graduates/Entry-Level: Focus on education, internships, projects, potential, and learning ability
        For Mid-Level (2-5 years): Focus on skill development, project ownership, and increasing responsibilities
        For Senior Level (5+ years): Focus on leadership, architecture decisions, mentoring, and strategic impact
        For Principal/Staff Level (8+ years): Focus on technical vision, cross-team influence, and business impact

        Provide a comprehensive analysis that includes:

        1. EXECUTIVE SUMMARY (2-3 sentences):
           - Overall assessment and positioning
           - Key strengths and critical issues
           - Market competitiveness level

        2. DETAILED SCORE BREAKDOWN (0-10 each):
           - ATS Compatibility
           - Content Quality
           - Format & Structure
           - Keyword Optimization
           - Experience Presentation
           - Skills Organization
           - Education & Certifications
           - Overall Market Appeal

        3. TIMELINE CONSISTENCY ANALYSIS:
           - Check for date conflicts and gaps (remember current date is {current_date})
           - Verify experience duration claims
           - Identify timeline inconsistencies
           - Flag overlapping employment periods
           - IMPORTANT: Only flag dates as "future" if they are after {current_year}
           - Dates in {current_year} or earlier are valid and should not be flagged as future dates

        4. ATS OPTIMIZATION ISSUES:
           - Formatting problems that break ATS parsing
           - Missing critical keywords
           - Section organization issues
           - Contact information problems

        5. CONTENT IMPROVEMENTS:
           - Weak or missing summary
           - Poor experience bullet points
           - Skills section issues
           - Education formatting problems

        6. SPECIFIC FIXES WITH EXAMPLES:
           - Quote exact text from the resume that needs to be changed
           - Provide specific before/after examples using actual resume content
           - Give specific formatting improvements with real examples
           - Show exact keyword additions/removals with context

        7. MARKET POSITIONING:
           - Competitive level assessment
           - Salary range estimation
           - Target company recommendations
           - Role level suggestions

        Return your analysis as JSON in this exact format:
        {{
            "executive_summary": "2-3 sentence summary of overall assessment, key strengths, critical issues, and market position",
            "overall_score": 0-100,
            "score_breakdown": {{
                "ats_compatibility": 0-10,
                "content_quality": 0-10,
                "format_structure": 0-10,
                "keyword_optimization": 0-10,
                "experience_presentation": 0-10,
                "skills_organization": 0-10,
                "education_certifications": 0-10,
                "market_appeal": 0-10
            }},
            "timeline_analysis": {{
                "consistency_score": 0-10,
                "issues_found": [
                    {{
                        "issue": "Specific timeline issue",
                        "location": "Where in resume",
                        "current": "What it currently shows",
                        "should_be": "What it should be",
                        "impact": "Why this matters"
                    }}
                ],
                "experience_duration_claims": {{
                    "claimed_years": "X years",
                    "actual_years": "Y years",
                    "discrepancy": "Explanation of difference"
                }}
            }},
            "ats_issues": {{
                "critical_fixes": [
                    {{
                        "issue": "Critical ATS parsing issue",
                        "location": "Section/area affected",
                        "current_problem": "What's wrong",
                        "fix": "Specific fix needed",
                        "example": "Before/after example"
                    }}
                ],
                "formatting_problems": [
                    {{
                        "problem": "Formatting issue",
                        "impact": "How it affects ATS",
                        "solution": "How to fix it"
                    }}
                ],
                "missing_keywords": [
                    {{
                        "keyword": "Missing keyword",
                        "importance": "Why it's important",
                        "where_to_add": "Where to add it",
                        "example": "How to add it naturally"
                    }}
                ]
            }},
            "content_improvements": {{
                "summary_issues": {{
                    "current_summary": "Current summary text",
                    "problems": ["Problem 1", "Problem 2"],
                    "improved_summary": "Better summary with specific examples",
                    "reasoning": "Why this is better"
                }},
                "experience_issues": [
                    {{
                        "job_title": "Exact job title from resume",
                        "company": "Exact company name from resume",
                        "current_bullets": ["EXACT bullet point text from resume", "EXACT bullet point text from resume"],
                        "problems": ["Specific issue with first bullet", "Specific issue with second bullet"],
                        "improved_bullets": ["Rewritten first bullet with metrics and impact", "Rewritten second bullet with specific achievements"],
                        "reasoning": "Detailed explanation of why the improvements work better"
                    }}
                ],
                "skills_issues": {{
                    "current_organization": "How skills are currently organized",
                    "problems": ["Problem 1", "Problem 2"],
                    "improved_organization": "Better way to organize",
                    "missing_skills": ["Skill 1", "Skill 2"],
                    "reasoning": "Why this is better"
                }},
                "education_issues": {{
                    "current_format": "Current education format",
                    "problems": ["Problem 1", "Problem 2"],
                    "improved_format": "Better format",
                    "reasoning": "Why this is better"
                }}
            }},
            "specific_fixes": {{
                "immediate_fixes": [
                    {{
                        "priority": 1,
                        "category": "Timeline|ATS|Content|Format",
                        "issue": "Specific issue to fix",
                        "current_text": "EXACT TEXT FROM RESUME that needs to be changed",
                        "new_text": "SPECIFIC REPLACEMENT TEXT with improvements",
                        "location": "Exact section and position in resume",
                        "impact": "Why this specific change improves recruiter perception",
                        "estimated_points": "+X points"
                    }}
                ],
                "strategic_improvements": [
                    {{
                        "priority": 2,
                        "category": "Content|Format|Keywords",
                        "improvement": "What to improve",
                        "action": "Specific action to take",
                        "example": "Before/after example",
                        "impact": "How this helps",
                        "estimated_points": "+X points"
                    }}
                ],
                "nice_to_have": [
                    {{
                        "priority": 3,
                        "enhancement": "Nice-to-have improvement",
                        "action": "What to do",
                        "impact": "Minor improvement",
                        "estimated_points": "+X points"
                    }}
                ]
            }},
            "market_positioning": {{
                "competitive_level": "Senior|Mid|Entry|Mixed",
                "salary_range": "Estimated salary range",
                "target_roles": ["role1", "role2", "role3"],
                "company_fit": {{
                    "best_fit": "maang|startups|enterprise|consulting|mixed",
                    "fit_score": 0-10,
                    "explanation": "Why this is the best fit",
                    "positioning_advice": "How to position for target companies"
                }},
                "differentiation_factors": ["factor1", "factor2", "factor3"],
                "market_competitiveness": "high|medium|low"
            }},
            "action_plan": {{
                "phase_1_immediate": [
                    {{
                        "action": "Specific action to take",
                        "timeline": "1-2 days",
                        "impact": "Expected impact",
                        "steps": ["Step 1", "Step 2"]
                    }}
                ],
                "phase_2_short_term": [
                    {{
                        "action": "Specific action to take",
                        "timeline": "1-2 weeks",
                        "impact": "Expected impact",
                        "steps": ["Step 1", "Step 2", "Step 3"]
                    }}
                ],
                "phase_3_long_term": [
                    {{
                        "action": "Specific action to take",
                        "timeline": "1-3 months",
                        "impact": "Expected impact",
                        "steps": ["Step 1", "Step 2", "Step 3", "Step 4"]
                    }}
                ]
            }},
            "priority_order": [
                "Fix timeline inconsistencies",
                "Resolve ATS parsing issues", 
                "Improve summary section",
                "Enhance experience bullets",
                "Optimize skills organization",
                "Add missing keywords",
                "Polish formatting"
            ]
        }}

        Focus on providing specific, actionable feedback with exact text changes needed.
        Prioritize fixes that prevent interviews over nice-to-have improvements.
        Include before/after examples for all major changes.
        Consider the target roles and industry in all recommendations.
        """

        result = await self.llm_call(prompt)
        
        # Add agent-specific metadata
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "detailed_analysis",
            "target_roles": target_roles,
            "target_seniority": target_seniority
        })
        
        return result
    
    def get_capabilities(self) -> list:
        """Return detailed analysis capabilities."""
        return [
            "timeline_consistency_analysis",
            "ats_optimization_detailed",
            "content_improvement_specific",
            "market_positioning_analysis",
            "action_plan_generation",
            "before_after_examples",
            "priority_ordering"
        ]
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate detailed analysis result structure."""
        required_fields = ["executive_summary", "overall_score", "score_breakdown", "specific_fixes", "market_positioning"]
        return all(field in result for field in required_fields) and isinstance(result.get("overall_score"), (int, float))
