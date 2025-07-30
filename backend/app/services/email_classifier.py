import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import openai
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailClassifier:
    """AI-powered email classification for job application tracking"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAPI_KEY)
        self.model = settings.EMAIL_CLASSIFICATION_MODEL
        
    async def classify_email(self, email_content: str, subject: str, sender_email: str) -> Dict[str, Any]:
        """
        Classify email content and extract job-related information
        """
        try:
            # Prepare the email content for analysis
            full_content = f"Subject: {subject}\nFrom: {sender_email}\n\n{email_content}"
            
            # Create the classification prompt
            prompt = self._create_classification_prompt(full_content)
            
            # Call OpenAI API
            response = await self._call_openai(prompt)
            
            # Parse the response
            classification_result = self._parse_classification_response(response)
            
            logger.info(f"Email classified as: {classification_result['email_type']} with confidence: {classification_result['confidence_score']}")
            
            return classification_result
            
        except Exception as e:
            logger.error(f"Error classifying email: {e}")
            return {
                'email_type': 'unknown',
                'confidence_score': 0.0,
                'company_name': None,
                'job_title': None,
                'sentiment': 'neutral',
                'extracted_data': {},
                'error': str(e)
            }
    
    def _create_classification_prompt(self, email_content: str) -> str:
        """Create the prompt for email classification"""
        return f"""
Analyze this job application email and classify it accurately. Return a JSON response with the following structure:

{{
    "email_type": "application_confirmation|application_rejection|interview_invitation|offer_letter|status_update|not_job_related",
    "confidence_score": 0.0-1.0,
    "company_name": "extracted company name or null",
    "job_title": "extracted job title or null",
    "sentiment": "positive|negative|neutral",
    "extracted_data": {{
        "application_date": "date if mentioned or null",
        "position_details": "any position details mentioned",
        "next_steps": "next steps mentioned",
        "contact_info": "contact information if provided"
    }}
}}

Email Classification Guidelines:
- application_confirmation: Emails confirming job application received (e.g., "Thank you for your application", "We have received your application")
- application_rejection: Emails rejecting job application (e.g., "We regret to inform you", "Unfortunately", "We have selected other candidates")
- interview_invitation: Emails inviting for interview (e.g., "We'd like to invite you for an interview", "Schedule an interview")
- offer_letter: Emails with job offer (e.g., "We're pleased to offer you", "Congratulations", "Job offer")
- status_update: General application status updates (e.g., "Your application is under review", "We're still considering")
- not_job_related: Not related to job applications

Email Content:
{email_content}

Analyze carefully and return only the JSON response:
"""
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API for classification"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert email classifier for job application tracking. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _parse_classification_response(self, response: str) -> Dict[str, Any]:
        """Parse the OpenAI response into structured data"""
        try:
            # Clean the response (remove markdown if present)
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            data = json.loads(response.strip())
            
            # Validate required fields
            required_fields = ['email_type', 'confidence_score', 'company_name', 'job_title', 'sentiment']
            for field in required_fields:
                if field not in data:
                    data[field] = None if field in ['company_name', 'job_title'] else 'unknown'
            
            # Ensure extracted_data exists
            if 'extracted_data' not in data:
                data['extracted_data'] = {}
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            logger.error(f"Raw response: {response}")
            return {
                'email_type': 'unknown',
                'confidence_score': 0.0,
                'company_name': None,
                'job_title': None,
                'sentiment': 'neutral',
                'extracted_data': {},
                'error': f'JSON parsing error: {str(e)}'
            }
    
    def is_job_related(self, email_type: str, confidence_score: float) -> bool:
        """Determine if email is job-related based on classification"""
        job_related_types = [
            'application_confirmation',
            'application_rejection', 
            'interview_invitation',
            'offer_letter',
            'status_update'
        ]
        
        return email_type in job_related_types and confidence_score >= 0.6
    
    def should_update_job_status(self, email_type: str, confidence_score: float) -> bool:
        """Determine if this email should trigger a job status update"""
        status_update_types = [
            'application_confirmation',
            'application_rejection',
            'interview_invitation', 
            'offer_letter'
        ]
        
        return email_type in status_update_types and confidence_score >= 0.7 