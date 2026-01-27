"""
Simplified Referral Service.
Paste-and-parse functionality for extracting contacts from LinkedIn profiles.
Replaces complex referral management system with basic contact extraction and template generation.
"""

import re
import logging
import signal
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.core.ai_service import AIService

logger = logging.getLogger(__name__)


class SimpleReferralService:
    """Simplified referral service with paste-and-parse functionality."""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.regex_timeout = 2  # 2 seconds max for regex operations

    @contextmanager
    def _regex_timeout(self, seconds: int = 2):
        """Context manager for regex timeout protection against ReDoS."""
        def timeout_handler(signum, frame):
            raise TimeoutError("Regex operation timed out - potential ReDoS detected")

        # Only works on Unix-based systems
        try:
            # Set the signal handler and alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                # Restore previous handler and cancel alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        except (AttributeError, ValueError):
            # Windows doesn't support SIGALRM, fallback to no timeout
            logger.warning("Regex timeout not supported on this platform")
            yield

    async def parse_linkedin_profile(self, profile_text: str) -> Dict[str, Any]:
        """
        Parse LinkedIn profile text to extract contact information.

        Args:
            profile_text: Raw text copied from LinkedIn profile

        Returns:
            Extracted contact information
        """
        try:
            logger.info("Parsing LinkedIn profile text")

            # Use AI to extract structured data from profile text
            extraction_prompt = f"""
Extract contact information from this LinkedIn profile text:

{profile_text}

Extract the following information in JSON format:
- name: Full name of the person
- title: Current job title
- company: Current company name
- location: Location/city
- industry: Industry sector
- experience_summary: Brief summary of their experience (1-2 sentences)
- skills: List of key skills mentioned
- education: Educational background if mentioned
- mutual_connections: Any mutual connections mentioned
- years_experience: Estimated years of experience (number only)

If any information is not available, use null for that field.
Return only valid JSON.
"""

            response = await self.ai_service.create_completion(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting contact information from LinkedIn profiles. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": extraction_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=600,
                response_format={"type": "json_object"}
            )

            import json
            extracted_data = json.loads(response.choices[0].message.content)

            # Add metadata
            extracted_data["extracted_at"] = datetime.now(timezone.utc).isoformat()
            extracted_data["source"] = "linkedin_profile"

            # Clean and validate data
            return self._validate_extracted_data(extracted_data)

        except Exception as e:
            logger.error(f"Error parsing LinkedIn profile: {str(e)}")
            # Return basic extracted data using regex fallbacks
            return self._extract_basic_info(profile_text)

    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted contact data."""

        # Ensure required fields are present
        validated_data = {
            "name": data.get("name") or "Unknown",
            "title": data.get("title") or "",
            "company": data.get("company") or "",
            "location": data.get("location") or "",
            "industry": data.get("industry") or "",
            "experience_summary": data.get("experience_summary") or "",
            "skills": data.get("skills") or [],
            "education": data.get("education") or "",
            "mutual_connections": data.get("mutual_connections") or "",
            "years_experience": data.get("years_experience") or 0,
            "extracted_at": data.get("extracted_at"),
            "source": data.get("source", "linkedin_profile")
        }

        # Clean skills list
        if isinstance(validated_data["skills"], list):
            validated_data["skills"] = [skill.strip() for skill in validated_data["skills"][:10]]
        else:
            validated_data["skills"] = []

        # Validate years of experience
        try:
            validated_data["years_experience"] = int(validated_data["years_experience"])
            if validated_data["years_experience"] < 0:
                validated_data["years_experience"] = 0
        except (ValueError, TypeError):
            validated_data["years_experience"] = 0

        return validated_data

    def _extract_basic_info(self, profile_text: str) -> Dict[str, Any]:
        """Fallback extraction using regex patterns with ReDoS protection."""

        # Limit input size to prevent excessive processing
        if len(profile_text) > 10000:
            profile_text = profile_text[:10000]

        # Simplified regex patterns to prevent ReDoS
        # Removed nested quantifiers and complex backtracking patterns
        name_pattern = r'^([A-Z][a-z]+ [A-Z][a-z]+)'
        title_pattern = r'(Senior|Lead|Principal|Staff|Director|Manager|Engineer|Developer|Analyst|Specialist|Coordinator)[\s\w]{1,50}'
        company_pattern = r'at ([A-Z][A-Za-z\s]{1,50})'
        location_pattern = r'([A-Z][a-z]{2,20},\s*[A-Z]{2,3})'

        # Extract using patterns with timeout protection
        name = None
        title = None
        company = None
        location = None

        try:
            with self._regex_timeout(1):  # 1 second timeout for each regex
                name_match = re.search(name_pattern, profile_text[:500], re.MULTILINE)
                if name_match:
                    name = name_match.group(1).strip()[:100]  # Limit name length

            with self._regex_timeout(1):
                title_match = re.search(title_pattern, profile_text[:1000], re.IGNORECASE)
                if title_match:
                    title = title_match.group(0).strip()[:150]  # Limit title length

            with self._regex_timeout(1):
                company_match = re.search(company_pattern, profile_text[:1000], re.IGNORECASE)
                if company_match:
                    company = company_match.group(1).strip()[:100]  # Limit company length

            with self._regex_timeout(1):
                location_match = re.search(location_pattern, profile_text[:1000])
                if location_match:
                    location = location_match.group(1).strip()[:100]  # Limit location length

        except TimeoutError:
            logger.warning("Regex timeout occurred - using defaults")
        except Exception as e:
            logger.error(f"Error in regex extraction: {e}")

        return {
            "name": name or "Unknown Contact",
            "title": title or "",
            "company": company or "",
            "location": location or "",
            "industry": "",
            "experience_summary": "",
            "skills": [],
            "education": "",
            "mutual_connections": "",
            "years_experience": 0,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "source": "linkedin_profile_regex"
        }

    async def generate_referral_message(
        self,
        contact_info: Dict[str, Any],
        job_info: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
        message_type: str = "linkedin"
    ) -> Dict[str, Any]:
        """
        Generate a personalized referral message.

        Args:
            contact_info: Extracted contact information
            job_info: Optional job information for context
            user_context: Optional user context for personalization
            message_type: Type of message ("linkedin", "email", "informal")

        Returns:
            Generated referral message with subject and body
        """
        try:
            logger.info(f"Generating {message_type} referral message")

            # Build context for message generation
            context_parts = []

            # Contact context
            context_parts.append(f"CONTACT INFORMATION:")
            context_parts.append(f"- Name: {contact_info['name']}")
            context_parts.append(f"- Title: {contact_info['title']}")
            context_parts.append(f"- Company: {contact_info['company']}")
            context_parts.append(f"- Location: {contact_info['location']}")
            if contact_info['mutual_connections']:
                context_parts.append(f"- Mutual Connections: {contact_info['mutual_connections']}")

            # Job context if provided
            if job_info:
                context_parts.append(f"\nJOB INFORMATION:")
                context_parts.append(f"- Position: {job_info.get('title', 'Not specified')}")
                context_parts.append(f"- Company: {job_info.get('company', 'Not specified')}")
                context_parts.append(f"- Location: {job_info.get('location', 'Not specified')}")

            # User context if provided
            if user_context:
                context_parts.append(f"\nYOUR BACKGROUND:")
                context_parts.append(f"- Current Title: {user_context.get('current_title', 'Professional')}")
                context_parts.append(f"- Experience: {user_context.get('years_experience', 'Several')} years")
                if user_context.get('skills'):
                    context_parts.append(f"- Key Skills: {', '.join(user_context['skills'][:5])}")

            context = "\n".join(context_parts)

            # Message type specific prompts
            message_prompts = {
                "linkedin": """
Generate a professional LinkedIn message for requesting a referral.

REQUIREMENTS:
- Keep it under 300 characters (LinkedIn connection message limit)
- Be direct but polite
- Mention specific job or company if provided
- Include a clear ask for referral or connection
- Professional yet personable tone

Format: Return only the message text (no subject line needed for LinkedIn)
""",
                "email": """
Generate a professional email for requesting a referral.

REQUIREMENTS:
- Include both subject line and email body
- Keep email body under 200 words
- Professional tone but warm and authentic
- Clear ask for referral or informational chat
- Thank them for their time

Format: Return JSON with "subject" and "body" fields
""",
                "informal": """
Generate a casual message for requesting a referral (for text or informal platforms).

REQUIREMENTS:
- Conversational tone
- Keep it brief (under 150 words)
- Mention mutual connection if available
- Direct but friendly ask

Format: Return only the message text
"""
            }

            prompt = f"""
{context}

{message_prompts.get(message_type, message_prompts['linkedin'])}

Be authentic, avoid overly formal language, and make it feel like a genuine human connection request.
"""

            response = await self.ai_service.create_completion(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at writing professional networking messages. Create authentic, engaging referral requests."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=400,
                response_format={"type": "json_object" if message_type == "email" else None}
            )

            message_content = response.choices[0].message.content.strip()

            if message_type == "email":
                import json
                email_data = json.loads(message_content)
                return {
                    "type": "email",
                    "subject": email_data.get("subject", "Referral Request"),
                    "body": email_data.get("body", message_content),
                    "contact_name": contact_info["name"],
                    "contact_company": contact_info["company"],
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "type": message_type,
                    "message": message_content,
                    "contact_name": contact_info["name"],
                    "contact_company": contact_info["company"],
                    "character_count": len(message_content),
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }

        except Exception as e:
            logger.error(f"Error generating referral message: {str(e)}")
            return self._generate_fallback_message(contact_info, job_info, message_type)

    def _generate_fallback_message(
        self,
        contact_info: Dict[str, Any],
        job_info: Optional[Dict[str, Any]],
        message_type: str
    ) -> Dict[str, Any]:
        """Generate simple fallback message when AI fails."""

        contact_name = contact_info.get("name", "there")
        company = contact_info.get("company", "your company")
        job_title = job_info.get("title", "a role") if job_info else "opportunities"

        if message_type == "email":
            return {
                "type": "email",
                "subject": f"Referral inquiry - {job_title}",
                "body": f"""Hi {contact_name},

I hope this message finds you well! I saw that you're at {company} and wanted to reach out about {job_title}.

I'm actively exploring opportunities in this space and would love to learn more about your experience at {company}. Would you be comfortable providing a referral or sharing any insights about the role?

I completely understand if this isn't possible - no pressure at all!

Thanks for considering, and I hope to hear from you soon.

Best regards""",
                "contact_name": contact_name,
                "contact_company": company,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        elif message_type == "linkedin":
            return {
                "type": "linkedin",
                "message": f"Hi {contact_name}! I'm interested in {job_title} and saw you're at {company}. Would love to connect and learn about your experience there. Thanks!",
                "contact_name": contact_name,
                "contact_company": company,
                "character_count": len(f"Hi {contact_name}! I'm interested in {job_title} and saw you're at {company}. Would love to connect and learn about your experience there. Thanks!"),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "type": "informal",
                "message": f"Hey {contact_name}! Hope you're doing well at {company}. I'm looking into {job_title} - would you be open to chatting about it?",
                "contact_name": contact_name,
                "contact_company": company,
                "character_count": len(f"Hey {contact_name}! Hope you're doing well at {company}. I'm looking into {job_title} - would you be open to chatting about it?"),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

    def extract_multiple_contacts(self, profile_text: str) -> List[Dict[str, Any]]:
        """
        Extract multiple contacts from text (e.g., search results, company directory).

        Args:
            profile_text: Text containing multiple profiles or contact info

        Returns:
            List of extracted contact information
        """
        try:
            # Split text into potential profile sections
            # Look for common delimiters or patterns
            sections = []

            # Split by double newlines or common separators
            potential_sections = re.split(r'\n\n+|\n-{3,}\n|\n={3,}\n', profile_text)

            for section in potential_sections:
                section = section.strip()
                if len(section) > 50:  # Minimum length for a profile
                    sections.append(section)

            # If no clear sections, try to extract from the whole text
            if len(sections) <= 1:
                # Simplified name pattern to prevent ReDoS
                name_pattern = r'(?:^|\n)([A-Z][a-z]+ [A-Z][a-z]+)\s*\n'

                try:
                    with self._regex_timeout(2):
                        names = re.findall(name_pattern, profile_text[:5000], re.MULTILINE)

                    if len(names) > 1:
                        with self._regex_timeout(2):
                            # Split by name patterns with limited text
                            sections = re.split(name_pattern, profile_text[:5000])[1:]  # Remove first empty element
                        # Pair names with their content
                        paired_sections = []
                        for i in range(0, len(sections), 2):
                            if i + 1 < len(sections):
                                paired_sections.append(sections[i] + "\n" + sections[i + 1])
                        sections = paired_sections
                except TimeoutError:
                    logger.warning("Regex timeout in multiple contact extraction")
                    sections = []

            # Extract contacts from each section
            contacts = []
            for i, section in enumerate(sections[:10]):  # Limit to 10 contacts max
                try:
                    contact = self._extract_basic_info(section)
                    if contact["name"] != "Unknown Contact":
                        contact["section_index"] = i
                        contacts.append(contact)
                except Exception as e:
                    logger.warning(f"Failed to extract contact from section {i}: {e}")
                    continue

            logger.info(f"Extracted {len(contacts)} contacts from profile text")
            return contacts

        except Exception as e:
            logger.error(f"Error extracting multiple contacts: {str(e)}")
            return []

    def get_message_templates(self) -> Dict[str, Any]:
        """Get available message templates and their descriptions."""
        return {
            "templates": {
                "linkedin": {
                    "name": "LinkedIn Connection Request",
                    "description": "Brief message for LinkedIn connection requests (under 300 characters)",
                    "character_limit": 300,
                    "use_case": "Sending connection requests on LinkedIn"
                },
                "email": {
                    "name": "Professional Email",
                    "description": "Formal email with subject line for referral requests",
                    "word_limit": 200,
                    "use_case": "Direct email outreach to contacts"
                },
                "informal": {
                    "name": "Casual Message",
                    "description": "Friendly, conversational message for texts or casual platforms",
                    "word_limit": 150,
                    "use_case": "Text messages, Slack, or informal outreach"
                }
            },
            "tips": [
                "Mention mutual connections when available",
                "Be specific about the role or company you're interested in",
                "Keep messages concise and respectful of their time",
                "Always include a clear but polite ask",
                "Personalize based on their background and experience"
            ]
        }