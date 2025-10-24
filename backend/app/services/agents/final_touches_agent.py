"""
Final Touches Agent for resume evaluation.
Performs final validation checks for LinkedIn consistency, filename format, and personal information security.
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class FinalTouchesAgent(BaseAgent):
    """Agent specialized in final touches and validation checks for resume completeness."""

    def __init__(self, ai_service=None):
        super().__init__("FinalTouchesAgent", ai_service)

    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze resume for final touches and validation checks.

        Args:
            resume_content: The resume text to analyze
            context: Additional context (filename, LinkedIn profile, etc.)

        Returns:
            Dictionary containing final touches analysis results
        """
        context = context or {}
        filename = context.get('filename', 'resume.pdf')
        linkedin_profile = context.get('linkedin_profile', '')
        target_roles = context.get('target_roles', [])

        prompt = f"""
        You are a senior career services professional and resume finalization expert with expertise in professional presentation standards and security best practices.
        Perform final validation checks and ensure resume is ready for professional submission.

        Resume Content:
        {resume_content}

        Additional Context:
        - Filename: {filename}
        - LinkedIn Profile: {linkedin_profile if linkedin_profile else 'Not provided'}
        - Target Roles: {', '.join(target_roles) if target_roles else 'General professional roles'}

        FINAL VALIDATION AREAS:

        1. LINKEDIN CONSISTENCY CHECK (0-10):
           - Resume content alignment with LinkedIn profile
           - Job titles and dates consistency
           - Company names and descriptions matching
           - Skills section alignment
           - Education details consistency
           - Achievement consistency across platforms

        2. FILENAME FORMAT VALIDATION (0-10):
           - Professional filename structure
           - Name inclusion in filename
           - File extension appropriateness (.pdf recommended)
           - Version control considerations
           - ATS-friendly filename format
           - Special character avoidance

        3. PERSONAL INFORMATION SECURITY (0-10):
           - Removal of sensitive personal data
           - Social Security Number absence
           - Personal address privacy considerations
           - Birth date and age information removal
           - Family/personal details elimination
           - Reference contact information security

        4. PROFESSIONAL PRESENTATION POLISH (0-10):
           - Overall document professionalism
           - Consistent formatting throughout
           - Error-free presentation (spelling, grammar)
           - Professional language tone
           - Industry-appropriate presentation style
           - Visual polish and attention to detail

        5. SUBMISSION READINESS (0-10):
           - ATS compatibility final check
           - PDF format optimization
           - File size appropriateness
           - Print-friendly formatting
           - Digital accessibility compliance
           - Multi-platform compatibility

        6. COMPLETENESS VERIFICATION (0-10):
           - All required sections present
           - Contact information completeness
           - Experience section thoroughness
           - Education section completeness
           - Skills section comprehensiveness
           - Missing critical information identification

        Return your analysis as JSON in this exact format:
        {{
            "final_touches_score": 0-10,
            "linkedin_consistency": {{
                "score": 0-10,
                "profile_alignment": "excellent|good|fair|poor|unknown",
                "job_titles_match": "consistent|minor_differences|major_differences|unknown",
                "dates_consistency": "consistent|minor_discrepancies|major_discrepancies|unknown",
                "company_descriptions": "aligned|somewhat_aligned|misaligned|unknown",
                "skills_alignment": "excellent|good|fair|poor|unknown",
                "education_consistency": "consistent|minor_differences|major_differences|unknown",
                "consistency_issues": [
                    "Job title mismatch at Company X",
                    "Date discrepancy for Role Y",
                    "Skills missing from LinkedIn"
                ],
                "consistency_recommendations": [
                    "Update LinkedIn job title for current role",
                    "Align dates between platforms",
                    "Add missing skills to LinkedIn profile",
                    "Sync company descriptions"
                ]
            }},
            "filename_validation": {{
                "score": 0-10,
                "current_filename": "{filename}",
                "filename_assessment": "professional|adequate|needs_improvement|poor",
                "name_inclusion": "present|partial|missing",
                "extension_appropriateness": "optimal|good|poor",
                "ats_friendliness": "excellent|good|fair|poor",
                "special_characters": "none|minimal|problematic",
                "filename_issues": [
                    "Missing candidate name",
                    "Poor file extension",
                    "Special characters present",
                    "Version info missing"
                ],
                "recommended_filename": "FirstName_LastName_Resume_2024.pdf",
                "filename_best_practices": [
                    "Include full name",
                    "Use underscores not spaces",
                    "Add current year",
                    "Use .pdf extension",
                    "Avoid special characters"
                ]
            }},
            "personal_info_security": {{
                "score": 0-10,
                "security_level": "excellent|good|fair|poor",
                "sensitive_data_present": "none|minimal|concerning|high_risk",
                "ssn_check": "absent|present",
                "address_privacy": "appropriate|oversharing|concerning",
                "age_info_check": "absent|present",
                "family_details": "absent|minimal|present",
                "reference_security": "secure|adequate|concerning",
                "security_violations": [
                    "Full home address provided",
                    "Birth date included",
                    "Personal family details mentioned"
                ],
                "security_recommendations": [
                    "Remove full home address, use city/state only",
                    "Remove birth date and age references",
                    "Eliminate personal family information",
                    "Secure reference contact information"
                ]
            }},
            "professional_polish": {{
                "score": 0-10,
                "overall_professionalism": "excellent|good|fair|poor",
                "formatting_consistency": "perfect|good|minor_issues|major_issues",
                "error_free_presentation": "perfect|minor_errors|several_errors|many_errors",
                "language_tone": "professional|mostly_professional|casual|inappropriate",
                "industry_appropriateness": "excellent|good|fair|poor",
                "visual_polish": "excellent|good|fair|poor",
                "polish_issues": [
                    "Inconsistent bullet point formatting",
                    "Minor spelling errors detected",
                    "Casual language in summary"
                ],
                "polish_improvements": [
                    "Standardize bullet point formatting",
                    "Proofread for spelling errors",
                    "Formalize language in summary section",
                    "Improve visual consistency"
                ]
            }},
            "submission_readiness": {{
                "score": 0-10,
                "ats_final_check": "fully_compatible|mostly_compatible|some_issues|major_issues",
                "pdf_optimization": "excellent|good|fair|poor",
                "file_size": "optimal|acceptable|too_large|too_small",
                "print_compatibility": "excellent|good|fair|poor",
                "digital_accessibility": "compliant|mostly_compliant|some_issues|non_compliant",
                "platform_compatibility": "universal|high|medium|low",
                "readiness_issues": [
                    "Large file size may cause upload issues",
                    "Some ATS compatibility concerns",
                    "Print formatting could be improved"
                ],
                "readiness_enhancements": [
                    "Optimize PDF file size",
                    "Test ATS parsing",
                    "Verify print layout",
                    "Check mobile viewing"
                ]
            }},
            "completeness_check": {{
                "score": 0-10,
                "required_sections": "all_present|mostly_present|some_missing|many_missing",
                "contact_completeness": "complete|mostly_complete|incomplete",
                "experience_thoroughness": "comprehensive|adequate|basic|insufficient",
                "education_completeness": "complete|mostly_complete|incomplete",
                "skills_comprehensiveness": "comprehensive|adequate|basic|insufficient",
                "missing_elements": [
                    "LinkedIn URL missing",
                    "Portfolio link absent",
                    "Relevant certifications missing"
                ],
                "completeness_recommendations": [
                    "Add LinkedIn profile URL",
                    "Include portfolio website",
                    "Add relevant certifications",
                    "Expand skills section"
                ]
            }},
            "critical_final_fixes": [
                {{
                    "priority": 1,
                    "category": "LinkedIn|Filename|Security|Polish|Submission|Completeness",
                    "issue": "Critical final issue",
                    "impact": "How this affects professional presentation",
                    "fix": "Specific action required",
                    "urgency": "critical|high|medium|low",
                    "estimated_time": "Minutes to fix"
                }}
            ],
            "submission_checklist": {{
                "technical_checks": [
                    "PDF format confirmed",
                    "File size under 5MB",
                    "ATS parsing tested",
                    "Print format verified"
                ],
                "content_checks": [
                    "All contact info updated",
                    "LinkedIn profile synced",
                    "No sensitive info present",
                    "Professional tone throughout"
                ],
                "presentation_checks": [
                    "Consistent formatting",
                    "Error-free content",
                    "Professional filename",
                    "Visual polish complete"
                ],
                "final_approval": "ready|needs_minor_fixes|needs_major_revisions|not_ready"
            }},
            "quality_assurance": {{
                "peer_review_recommended": true/false,
                "professional_review_suggested": true/false,
                "industry_specific_check_needed": true/false,
                "final_proofreading_required": true/false,
                "overall_quality_rating": "excellent|good|fair|needs_improvement",
                "submission_confidence": "high|medium|low",
                "quality_concerns": [
                    "Specific areas needing attention"
                ]
            }}
        }}

        Focus on actionable final improvements that ensure professional readiness.
        Prioritize critical issues that could prevent successful application submission.
        Consider both technical compatibility and professional presentation standards.
        Ensure all recommendations align with modern resume best practices and security guidelines.
        """

        result = await self.llm_call(prompt)

        # Add agent-specific metadata
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "final_touches",
            "filename": filename,
            "linkedin_profile": linkedin_profile,
            "target_roles": target_roles
        })

        return result

    def get_capabilities(self) -> list:
        """Return final touches analysis capabilities."""
        return [
            "linkedin_consistency_check",
            "filename_format_validation",
            "personal_information_security",
            "professional_presentation_polish",
            "submission_readiness_assessment",
            "completeness_verification",
            "quality_assurance_review",
            "submission_checklist_generation"
        ]

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate final touches analysis result structure."""
        required_fields = ["final_touches_score", "linkedin_consistency", "filename_validation", "personal_info_security", "submission_checklist"]
        return all(field in result for field in required_fields) and isinstance(result.get("final_touches_score"), (int, float))