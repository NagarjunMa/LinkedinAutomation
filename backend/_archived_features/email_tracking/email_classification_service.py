"""
Email Classification Service for JobFlow Pro
Handles AI-powered classification and parsing of job-related emails
"""
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

from app.core.ai_service import get_ai_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailClassificationService:
    """Service for classifying and parsing job-related emails"""
    
    def __init__(self):
        self.ai_service = get_ai_service()
        
        # Email type patterns for quick classification
        self.email_patterns = {
            'interview_invitation': [
                r'interview.*schedule',
                r'phone.*screen',
                r'video.*interview',
                r'meeting.*schedule',
                r'next.*step.*interview',
                r'interview.*invitation',
                r'calendar.*invite'
            ],
            'application_confirmation': [
                r'application.*received',
                r'thank.*you.*application',
                r'we.*received.*your',
                r'application.*submitted',
                r'confirmation.*application'
            ],
            'rejection': [
                r'not.*moving.*forward',
                r'unfortunately.*not',
                r'not.*selected',
                r'other.*candidates',
                r'position.*filled',
                r'not.*proceed'
            ],
            'offer': [
                r'job.*offer',
                r'congratulations.*offer',
                r'pleased.*offer',
                r'offer.*letter',
                r'welcome.*team'
            ],
            'request_info': [
                r'additional.*information',
                r'please.*provide',
                r'need.*more.*info',
                r'clarification.*needed',
                r'follow.*up.*questions'
            ]
        }
    
    async def classify_email_type(self, email_content: Dict) -> str:
        """Classify job-related email type using AI and pattern matching"""
        
        try:
            # First try pattern matching for quick classification
            pattern_result = self._classify_by_patterns(email_content)
            if pattern_result != 'general':
                return pattern_result
            
            # Use AI for more complex classification
            ai_result = await self._classify_with_ai(email_content)
            return ai_result
            
        except Exception as e:
            logger.error(f"Email classification failed: {e}")
            return 'general'
    
    def _classify_by_patterns(self, email_content: Dict) -> str:
        """Quick classification using regex patterns"""
        
        subject = email_content.get('subject', '').lower()
        body = email_content.get('body', '').lower()
        combined_text = f"{subject} {body}"
        
        for email_type, patterns in self.email_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    return email_type
        
        return 'general'
    
    async def _classify_with_ai(self, email_content: Dict) -> str:
        """Use AI for email classification"""
        
        prompt = f"""
        Classify this job-related email into one category:
        
        Subject: {email_content.get('subject', '')}
        From: {email_content.get('from', '')}
        Body Preview: {email_content.get('body', '')[:500]}
        
        Categories:
        1. application_confirmation - "We received your application", "Thank you for applying"
        2. interview_invitation - Scheduling phone screen, video interview, or in-person interview
        3. interview_reminder - Upcoming interview confirmation, calendar reminder
        4. rejection - Application not moving forward, not selected, position filled
        5. offer - Job offer extended, congratulations, welcome to the team
        6. request_info - Requesting additional materials, clarification, follow-up questions
        7. general - Other job-related communication that doesn't fit above categories
        
        Return only the category name, nothing else.
        """
        
        try:
            response = await self.ai_service.generate_response(prompt)
            result = response.strip().lower()
            
            # Validate result
            valid_types = [
                'application_confirmation', 'interview_invitation', 'interview_reminder',
                'rejection', 'offer', 'request_info', 'general'
            ]
            
            if result in valid_types:
                return result
            else:
                logger.warning(f"AI returned invalid email type: {result}")
                return 'general'
                
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return 'general'
    
    async def parse_email_content(self, email: Dict, email_type: str) -> Dict:
        """Extract relevant information from email based on type"""
        
        try:
            if email_type == 'interview_invitation':
                return await self._parse_interview_email(email)
            elif email_type == 'offer':
                return await self._parse_offer_email(email)
            elif email_type == 'rejection':
                return await self._parse_rejection_email(email)
            elif email_type == 'application_confirmation':
                return await self._parse_confirmation_email(email)
            else:
                return await self._parse_general_email(email)
                
        except Exception as e:
            logger.error(f"Email parsing failed: {e}")
            return {}
    
    async def _parse_interview_email(self, email: Dict) -> Dict:
        """Parse interview invitation email"""
        
        prompt = f"""
        Extract key information from this interview invitation email:
        
        Subject: {email.get('subject', '')}
        Body: {email.get('body', '')}
        
        Extract and return JSON with these fields:
        {{
            "company": "Company name",
            "job_title": "Job title/role if mentioned",
            "interview_date": "Interview date (YYYY-MM-DD format if found)",
            "interview_time": "Interview time (HH:MM format if found)",
            "interview_type": "phone, video, in-person, or unknown",
            "interviewer_name": "Interviewer name if mentioned",
            "interviewer_email": "Interviewer email if mentioned",
            "action_required": "What the candidate needs to do",
            "deadline": "Response deadline if mentioned",
            "meeting_link": "Video call link if provided",
            "location": "Interview location if in-person"
        }}
        
        Return only valid JSON, no other text.
        """
        
        try:
            response = await self.ai_service.generate_response(prompt)
            parsed_data = json.loads(response)
            
            # Validate and clean the data
            return self._validate_parsed_data(parsed_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse interview email JSON: {e}")
            return self._extract_basic_info(email)
        except Exception as e:
            logger.error(f"Interview email parsing failed: {e}")
            return self._extract_basic_info(email)
    
    async def _parse_offer_email(self, email: Dict) -> Dict:
        """Parse job offer email"""
        
        prompt = f"""
        Extract key information from this job offer email:
        
        Subject: {email.get('subject', '')}
        Body: {email.get('body', '')}
        
        Extract and return JSON with these fields:
        {{
            "company": "Company name",
            "job_title": "Job title/position",
            "salary": "Salary amount if mentioned",
            "start_date": "Proposed start date",
            "offer_deadline": "Deadline to respond to offer",
            "benefits": "Benefits mentioned",
            "next_steps": "What the candidate needs to do next",
            "contact_person": "Contact person for questions"
        }}
        
        Return only valid JSON, no other text.
        """
        
        try:
            response = await self.ai_service.generate_response(prompt)
            parsed_data = json.loads(response)
            return self._validate_parsed_data(parsed_data)
            
        except Exception as e:
            logger.error(f"Offer email parsing failed: {e}")
            return self._extract_basic_info(email)
    
    async def _parse_rejection_email(self, email: Dict) -> Dict:
        """Parse rejection email"""
        
        prompt = f"""
        Extract key information from this rejection email:
        
        Subject: {email.get('subject', '')}
        Body: {email.get('body', '')}
        
        Extract and return JSON with these fields:
        {{
            "company": "Company name",
            "job_title": "Job title if mentioned",
            "reason": "Reason for rejection if provided",
            "feedback": "Any feedback provided",
            "future_opportunities": "Mention of future opportunities",
            "contact_for_feedback": "Contact person for feedback"
        }}
        
        Return only valid JSON, no other text.
        """
        
        try:
            response = await self.ai_service.generate_response(prompt)
            parsed_data = json.loads(response)
            return self._validate_parsed_data(parsed_data)
            
        except Exception as e:
            logger.error(f"Rejection email parsing failed: {e}")
            return self._extract_basic_info(email)
    
    async def _parse_confirmation_email(self, email: Dict) -> Dict:
        """Parse application confirmation email"""
        
        prompt = f"""
        Extract key information from this application confirmation email:
        
        Subject: {email.get('subject', '')}
        Body: {email.get('body', '')}
        
        Extract and return JSON with these fields:
        {{
            "company": "Company name",
            "job_title": "Job title if mentioned",
            "application_id": "Application ID or reference number",
            "next_steps": "What happens next",
            "timeline": "Expected timeline for response",
            "contact_info": "Contact information for questions"
        }}
        
        Return only valid JSON, no other text.
        """
        
        try:
            response = await self.ai_service.generate_response(prompt)
            parsed_data = json.loads(response)
            return self._validate_parsed_data(parsed_data)
            
        except Exception as e:
            logger.error(f"Confirmation email parsing failed: {e}")
            return self._extract_basic_info(email)
    
    async def _parse_general_email(self, email: Dict) -> Dict:
        """Parse general job-related email"""
        
        prompt = f"""
        Extract key information from this job-related email:
        
        Subject: {email.get('subject', '')}
        Body: {email.get('body', '')}
        
        Extract and return JSON with these fields:
        {{
            "company": "Company name",
            "job_title": "Job title if mentioned",
            "action_required": "What the candidate needs to do",
            "deadline": "Any deadlines mentioned",
            "important_info": "Any important information",
            "contact_person": "Contact person if mentioned"
        }}
        
        Return only valid JSON, no other text.
        """
        
        try:
            response = await self.ai_service.generate_response(prompt)
            parsed_data = json.loads(response)
            return self._validate_parsed_data(parsed_data)
            
        except Exception as e:
            logger.error(f"General email parsing failed: {e}")
            return self._extract_basic_info(email)
    
    def _validate_parsed_data(self, parsed_data: Dict) -> Dict:
        """Validate and clean parsed data"""
        
        # Ensure all values are strings or None
        cleaned_data = {}
        for key, value in parsed_data.items():
            if isinstance(value, str) and value.strip():
                cleaned_data[key] = value.strip()
            else:
                cleaned_data[key] = None
        
        return cleaned_data
    
    def _extract_basic_info(self, email: Dict) -> Dict:
        """Extract basic information when AI parsing fails"""
        
        # Extract company from email domain
        from_email = email.get('from', '')
        company = self._extract_company_from_email(from_email)
        
        # Extract job title from subject
        subject = email.get('subject', '')
        job_title = self._extract_job_title_from_subject(subject)
        
        return {
            'company': company,
            'job_title': job_title,
            'action_required': None,
            'deadline': None,
            'important_info': None,
            'contact_person': None
        }
    
    def _extract_company_from_email(self, email: str) -> Optional[str]:
        """Extract company name from email address"""
        
        if '@' in email:
            domain = email.split('@')[1]
            # Remove common email providers
            if domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']:
                # Extract company name from domain
                company = domain.split('.')[0]
                return company.title()
        
        return None
    
    def _extract_job_title_from_subject(self, subject: str) -> Optional[str]:
        """Extract job title from email subject"""
        
        # Common patterns for job titles in subjects
        patterns = [
            r'(.+?)\s*-\s*(?:Software Engineer|Developer|Engineer)',
            r'(?:Software Engineer|Developer|Engineer)\s*-\s*(.+)',
            r'(.+?)\s*Position',
            r'(.+?)\s*Role'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def is_urgent_email(self, email_type: str, parsed_data: Dict) -> bool:
        """Determine if email requires urgent attention"""
        
        urgent_types = ['interview_invitation', 'offer']
        
        if email_type in urgent_types:
            return True
        
        # Check for urgent keywords in parsed data
        urgent_keywords = ['urgent', 'asap', 'immediately', 'deadline', 'respond quickly']
        
        for key, value in parsed_data.items():
            if isinstance(value, str):
                for keyword in urgent_keywords:
                    if keyword.lower() in value.lower():
                        return True
        
        return False
    
    def get_email_priority(self, email_type: str, parsed_data: Dict) -> str:
        """Get email priority level"""
        
        if self.is_urgent_email(email_type, parsed_data):
            return 'high'
        elif email_type in ['offer', 'interview_invitation']:
            return 'medium'
        else:
            return 'low'
    
    def generate_notification_message(self, email_type: str, parsed_data: Dict) -> Tuple[str, str]:
        """Generate notification title and message"""
        
        company = parsed_data.get('company', 'Unknown Company')
        
        if email_type == 'interview_invitation':
            title = "🎤 Interview Invitation"
            message = f"Interview request from {company} - respond ASAP"
        elif email_type == 'offer':
            title = "🎉 Job Offer Received"
            message = f"Congratulations! You received an offer from {company}"
        elif email_type == 'rejection':
            title = "📧 Application Update"
            message = f"Update from {company} regarding your application"
        elif email_type == 'application_confirmation':
            title = "✅ Application Confirmed"
            message = f"Application confirmed by {company}"
        else:
            title = "📧 New Email"
            message = f"New email from {company}"
        
        return title, message


# Global instance
email_classification_service = EmailClassificationService()
