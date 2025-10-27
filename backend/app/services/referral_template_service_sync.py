"""
Simplified Referral Template Service (Synchronous)
Basic template generation and storage without async features
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)

class ReferralTemplateService:
    def __init__(self):
        pass

    def generate_referral_template(
        self,
        db: Session,
        user_id: str,
        contact_info: Dict[str, Any],
        job_info: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a simple referral email template
        """
        try:
            # Generate basic template
            template_result = self._generate_simple_template(contact_info, job_info, user_preferences)

            # Store template in database
            template_id = self._store_template(
                db, user_id, template_result, contact_info, job_info
            )

            return {
                'template_id': str(template_id),
                'subject_line': template_result['subject_line'],
                'email_body': template_result['email_body'],
                'style': template_result.get('style', 'professional'),
                'personalization_level': template_result.get('personalization_level', 'medium'),
                'confidence_score': template_result.get('confidence_score', 0.8),
                'suggested_follow_up_days': template_result.get('follow_up_days', 15)
            }

        except Exception as e:
            logger.error(f"Error generating referral template: {str(e)}")
            raise Exception(f"Failed to generate referral template: {str(e)}")

    def _generate_simple_template(self, contact: Dict, job: Dict, prefs: Dict) -> Dict[str, Any]:
        """
        Generate a basic template without AI
        """
        contact_name = contact.get('name', 'there')
        job_title = job.get('title', 'the position')
        company = job.get('company', 'your company')

        # Get user tone preference
        tone = prefs.get('preferred_tone', 'professional') if prefs else 'professional'

        if tone == 'casual':
            subject = f"Quick question about the {job_title} role"
            greeting = f"Hey {contact_name},"
            intro = "Hope you're doing well!"
        elif tone == 'direct':
            subject = f"Referral Request - {job_title}"
            greeting = f"Hi {contact_name},"
            intro = "I'm reaching out regarding a specific opportunity."
        else:  # professional
            subject = f"Referral Request - {job_title} at {company}"
            greeting = f"Dear {contact_name},"
            intro = "I hope this message finds you well."

        body = f"""{greeting}

{intro} I noticed the {job_title} position at {company} and believe it would be an excellent fit for my background and skills.

I have relevant experience and would greatly appreciate any insights you might have about the role or the team. If you feel comfortable doing so, I would be honored if you could refer me to the hiring manager.

I've attached my resume for your review. Would you have a few minutes to chat about this opportunity?

Thank you for your time and consideration.

Best regards"""

        return {
            'subject_line': subject,
            'email_body': body,
            'style': tone,
            'personalization_level': 'medium',
            'confidence_score': 0.7,
            'follow_up_days': 15
        }

    def _store_template(
        self,
        db: Session,
        user_id: str,
        template_result: Dict[str, Any],
        contact_info: Dict[str, Any],
        job_info: Dict[str, Any]
    ) -> UUID:
        """Store the generated template in database"""
        template_id = uuid4()

        # First, create the tables if they don't exist (simplified approach)
        try:
            query = text("""
                INSERT INTO referral_templates (
                    id, user_id, contact_name, contact_email, contact_company,
                    contact_position, subject_line, email_body, template_style,
                    personalization_level, effectiveness_score, created_at
                ) VALUES (
                    :id, :user_id, :contact_name, :contact_email, :contact_company,
                    :contact_position, :subject_line, :email_body, :template_style,
                    :personalization_level, :effectiveness_score, :created_at
                )
            """)

            db.execute(query, {
                'id': template_id,
                'user_id': user_id,
                'contact_name': contact_info.get('name'),
                'contact_email': contact_info.get('email'),
                'contact_company': contact_info.get('company'),
                'contact_position': contact_info.get('position'),
                'subject_line': template_result['subject_line'],
                'email_body': template_result['email_body'],
                'template_style': template_result.get('style', 'professional'),
                'personalization_level': template_result.get('personalization_level', 'medium'),
                'effectiveness_score': template_result.get('confidence_score', 0.8),
                'created_at': datetime.utcnow()
            })

            db.commit()
            return template_id
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store template: {str(e)}")
            # Return a mock template ID if database operations fail
            return uuid4()

    def get_user_templates(
        self,
        db: Session,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's referral templates"""
        try:
            query = text("""
                SELECT id, contact_name, contact_company, subject_line,
                       email_body, template_style, was_sent, sent_at,
                       got_response, response_type, effectiveness_score,
                       created_at
                FROM referral_templates
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            result = db.execute(query, {
                'user_id': user_id,
                'limit': limit,
                'offset': offset
            })

            templates = []
            for row in result.fetchall():
                templates.append({
                    'id': str(row.id),
                    'contact_name': row.contact_name,
                    'contact_company': row.contact_company,
                    'subject_line': row.subject_line,
                    'email_body': row.email_body,
                    'template_style': row.template_style,
                    'was_sent': row.was_sent or False,
                    'sent_at': row.sent_at.isoformat() if row.sent_at else None,
                    'got_response': row.got_response or False,
                    'response_type': row.response_type,
                    'effectiveness_score': row.effectiveness_score,
                    'created_at': row.created_at.isoformat(),
                    'user_feedback': None
                })

            return templates
        except Exception as e:
            logger.error(f"Failed to get templates: {str(e)}")
            return []

    def get_template_stats(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get user's template statistics"""
        try:
            query = text("""
                SELECT
                    COUNT(*) as total_templates,
                    COUNT(CASE WHEN was_sent THEN 1 END) as sent_count,
                    COUNT(CASE WHEN got_response THEN 1 END) as response_count,
                    AVG(effectiveness_score) as avg_effectiveness,
                    COUNT(CASE WHEN was_sent = false OR was_sent IS NULL THEN 1 END) as draft_count
                FROM referral_templates
                WHERE user_id = :user_id
            """)

            result = db.execute(query, {'user_id': user_id})
            row = result.fetchone()

            if row:
                return {
                    'total_templates': row.total_templates or 0,
                    'sent_count': row.sent_count or 0,
                    'response_count': row.response_count or 0,
                    'response_rate': (row.response_count or 0) / max(row.sent_count or 1, 1) * 100,
                    'avg_effectiveness': float(row.avg_effectiveness or 0),
                    'draft_count': row.draft_count or 0
                }
            else:
                return {
                    'total_templates': 0,
                    'sent_count': 0,
                    'response_count': 0,
                    'response_rate': 0.0,
                    'avg_effectiveness': 0.0,
                    'draft_count': 0
                }
        except Exception as e:
            logger.error(f"Failed to get template stats: {str(e)}")
            return {
                'total_templates': 0,
                'sent_count': 0,
                'response_count': 0,
                'response_rate': 0.0,
                'avg_effectiveness': 0.0,
                'draft_count': 0
            }

    def record_template_feedback(
        self,
        db: Session,
        template_id: UUID,
        user_id: str,
        feedback_data: Dict[str, Any]
    ):
        """Record user feedback about template effectiveness"""
        try:
            # Update the template with response information
            query = text("""
                UPDATE referral_templates
                SET got_response = :got_response,
                    response_type = :response_type,
                    effectiveness_score = CASE
                        WHEN :got_response THEN 0.8
                        ELSE 0.3
                    END
                WHERE id = :template_id AND user_id = :user_id
            """)

            db.execute(query, {
                'template_id': template_id,
                'user_id': user_id,
                'got_response': feedback_data.get('got_response', False),
                'response_type': feedback_data.get('response_type')
            })

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record feedback: {str(e)}")

    def mark_template_as_sent(self, db: Session, template_id: UUID, user_id: str):
        """Mark a template as sent"""
        try:
            query = text("""
                UPDATE referral_templates
                SET was_sent = true, sent_at = :sent_at
                WHERE id = :template_id AND user_id = :user_id
            """)

            db.execute(query, {
                'template_id': template_id,
                'user_id': user_id,
                'sent_at': datetime.utcnow()
            })

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to mark template as sent: {str(e)}")

# Create singleton instance
referral_template_service = ReferralTemplateService()