"""
Referral Template Service with AI Learning
Handles template generation, effectiveness tracking, and learning
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4

import openai
from sqlalchemy import text, and_, desc, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

class ReferralTemplateService:
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_referral_template(
        self,
        db: AsyncSession,
        user_id: UUID,
        contact_info: Dict[str, Any],
        job_info: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a personalized referral email template using AI with learning
        """
        try:
            # Get user preferences
            if not user_preferences:
                user_preferences = await self._get_user_preferences(db, user_id)

            # Get best performing patterns for this context
            success_patterns = await self._get_relevant_success_patterns(
                db, job_info.get('industry'), job_info.get('level'), contact_info.get('company_size')
            )

            # Build generation context
            generation_context = {
                'contact_info': contact_info,
                'job_info': job_info,
                'user_preferences': user_preferences,
                'success_patterns': success_patterns,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Generate template using AI
            template_result = await self._generate_with_ai(generation_context)

            # Store template in database
            template_id = await self._store_template(
                db, user_id, template_result, generation_context
            )

            # Store analytics
            await self._store_generation_analytics(
                db, template_id, user_id, generation_context, template_result.get('confidence_score', 0.8)
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

    async def _generate_with_ai(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use OpenAI to generate the referral email template
        """
        contact = context['contact_info']
        job = context['job_info']
        prefs = context['user_preferences']
        patterns = context['success_patterns']

        # Build the prompt
        system_prompt = self._build_system_prompt(patterns)
        user_prompt = self._build_user_prompt(contact, job, prefs)

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            # Parse the response
            content = response.choices[0].message.content
            return self._parse_ai_response(content)

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            # Fallback to template-based generation
            return self._generate_fallback_template(contact, job, prefs)

    def _build_system_prompt(self, success_patterns: List[Dict]) -> str:
        """Build the system prompt for AI generation"""
        patterns_text = ""
        if success_patterns:
            patterns_text = "\n\nSuccessful patterns to consider:\n"
            for pattern in success_patterns[:3]:  # Top 3 patterns
                patterns_text += f"- {pattern['pattern_name']}: {pattern['pattern_description']} (Success rate: {pattern['success_rate']:.2%})\n"

        return f"""You are an expert at writing personalized referral emails that get responses.
        Your goal is to create professional, engaging emails that lead to meaningful connections.

        Guidelines:
        1. Keep it concise (150-250 words)
        2. Be genuine and specific
        3. Include a clear value proposition
        4. Make it easy to respond with a simple ask
        5. Use professional but warm tone
        6. Mention specific details when available

        {patterns_text}

        Return your response in JSON format with these fields:
        - "subject_line": The email subject (50 chars max)
        - "email_body": The complete email body
        - "style": professional/casual/direct
        - "personalization_level": low/medium/high
        - "confidence_score": 0.0-1.0 based on how confident you are
        - "follow_up_days": recommended days to follow up (7-30)
        """

    def _build_user_prompt(self, contact: Dict, job: Dict, prefs: Dict) -> str:
        """Build the user prompt with specific details"""
        return f"""
        Create a referral email for:

        Contact: {contact.get('name', 'N/A')} at {contact.get('company', 'N/A')}
        Position: {contact.get('position', 'N/A')}

        Job I'm interested in:
        Title: {job.get('title', 'N/A')}
        Company: {job.get('company', 'N/A')}
        Industry: {job.get('industry', 'N/A')}

        My background:
        - {job.get('user_background', 'Professional with relevant experience')}

        Preferences:
        - Tone: {prefs.get('preferred_tone', 'professional')}
        - Length: {prefs.get('preferred_length', 'medium')}
        - Include resume: {prefs.get('include_resume', True)}

        Make it specific to this person and opportunity.
        """

    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response and extract JSON"""
        try:
            # Try to find JSON in the response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                return json.loads(json_str)
        except:
            pass

        # Fallback parsing
        return {
            'subject_line': 'Referral Request - [Job Title]',
            'email_body': content,
            'style': 'professional',
            'personalization_level': 'medium',
            'confidence_score': 0.6,
            'follow_up_days': 15
        }

    def _generate_fallback_template(self, contact: Dict, job: Dict, prefs: Dict) -> Dict[str, Any]:
        """Fallback template generation when AI fails"""
        contact_name = contact.get('name', 'there')
        job_title = job.get('title', 'the position')
        company = job.get('company', 'your company')

        subject = f"Referral Request - {job_title}"

        body = f"""Hi {contact_name},

I hope this message finds you well. I'm reaching out because I'm very interested in the {job_title} position at {company}.

I have relevant experience and believe I would be a strong fit for this role. I was hoping you might be able to provide some insights about the position or potentially refer me to the hiring team.

I'd be happy to share my resume and would greatly appreciate any guidance you can offer. Would you have a few minutes for a brief conversation this week?

Thank you for your time and consideration.

Best regards"""

        return {
            'subject_line': subject,
            'email_body': body,
            'style': prefs.get('preferred_tone', 'professional'),
            'personalization_level': 'low',
            'confidence_score': 0.5,
            'follow_up_days': 15
        }

    async def _store_template(
        self,
        db: AsyncSession,
        user_id: UUID,
        template_result: Dict[str, Any],
        generation_context: Dict[str, Any]
    ) -> UUID:
        """Store the generated template in database"""
        template_id = uuid4()

        query = text("""
            INSERT INTO referral_templates (
                id, user_id, job_id, contact_name, contact_email, contact_company,
                contact_position, subject_line, email_body, template_style,
                personalization_level, effectiveness_score
            ) VALUES (
                :id, :user_id, :job_id, :contact_name, :contact_email, :contact_company,
                :contact_position, :subject_line, :email_body, :template_style,
                :personalization_level, :effectiveness_score
            )
        """)

        contact = generation_context['contact_info']

        await db.execute(query, {
            'id': template_id,
            'user_id': user_id,
            'job_id': generation_context['job_info'].get('job_id'),
            'contact_name': contact.get('name'),
            'contact_email': contact.get('email'),
            'contact_company': contact.get('company'),
            'contact_position': contact.get('position'),
            'subject_line': template_result['subject_line'],
            'email_body': template_result['email_body'],
            'template_style': template_result.get('style', 'professional'),
            'personalization_level': template_result.get('personalization_level', 'medium'),
            'effectiveness_score': template_result.get('confidence_score', 0.8)
        })

        await db.commit()
        return template_id

    async def _store_generation_analytics(
        self,
        db: AsyncSession,
        template_id: UUID,
        user_id: UUID,
        generation_context: Dict[str, Any],
        confidence_score: float
    ):
        """Store analytics about the template generation"""
        query = text("""
            INSERT INTO template_analytics (
                template_id, user_id, generation_context, ai_confidence_score
            ) VALUES (:template_id, :user_id, :generation_context, :ai_confidence_score)
        """)

        await db.execute(query, {
            'template_id': template_id,
            'user_id': user_id,
            'generation_context': json.dumps(generation_context),
            'ai_confidence_score': confidence_score
        })

        await db.commit()

    async def _get_user_preferences(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        """Get user referral preferences"""
        query = text("""
            SELECT preferred_tone, preferred_length, include_resume, include_portfolio,
                   auto_follow_up, follow_up_days, max_templates_per_day
            FROM user_referral_preferences
            WHERE user_id = :user_id
        """)

        result = await db.execute(query, {'user_id': user_id})
        row = result.fetchone()

        if row:
            return {
                'preferred_tone': row.preferred_tone,
                'preferred_length': row.preferred_length,
                'include_resume': row.include_resume,
                'include_portfolio': row.include_portfolio,
                'auto_follow_up': row.auto_follow_up,
                'follow_up_days': row.follow_up_days,
                'max_templates_per_day': row.max_templates_per_day
            }

        # Return defaults
        return {
            'preferred_tone': 'professional',
            'preferred_length': 'medium',
            'include_resume': True,
            'include_portfolio': False,
            'auto_follow_up': True,
            'follow_up_days': 15,
            'max_templates_per_day': 5
        }

    async def _get_relevant_success_patterns(
        self,
        db: AsyncSession,
        industry: Optional[str],
        job_level: Optional[str],
        company_size: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get relevant success patterns based on context"""
        query = text("""
            SELECT pattern_name, pattern_description, success_rate, pattern_data,
                   industry_tags, job_level_tags, company_size_tags
            FROM template_success_patterns
            WHERE (
                :industry = ANY(industry_tags) OR
                :job_level = ANY(job_level_tags) OR
                :company_size = ANY(company_size_tags) OR
                (industry_tags IS NULL AND job_level_tags IS NULL AND company_size_tags IS NULL)
            )
            ORDER BY success_rate DESC
            LIMIT 5
        """)

        result = await db.execute(query, {
            'industry': industry or '',
            'job_level': job_level or '',
            'company_size': company_size or ''
        })

        patterns = []
        for row in result.fetchall():
            patterns.append({
                'pattern_name': row.pattern_name,
                'pattern_description': row.pattern_description,
                'success_rate': row.success_rate,
                'pattern_data': row.pattern_data,
                'industry_tags': row.industry_tags,
                'job_level_tags': row.job_level_tags,
                'company_size_tags': row.company_size_tags
            })

        return patterns

    async def record_template_feedback(
        self,
        db: AsyncSession,
        template_id: UUID,
        user_id: UUID,
        feedback_data: Dict[str, Any]
    ):
        """Record user feedback about template effectiveness"""
        query = text("""
            INSERT INTO template_feedback (
                template_id, user_id, got_response, response_type,
                response_quality_score, user_satisfaction_score, feedback_notes
            ) VALUES (
                :template_id, :user_id, :got_response, :response_type,
                :response_quality_score, :user_satisfaction_score, :feedback_notes
            )
        """)

        await db.execute(query, {
            'template_id': template_id,
            'user_id': user_id,
            'got_response': feedback_data.get('got_response', False),
            'response_type': feedback_data.get('response_type'),
            'response_quality_score': feedback_data.get('response_quality_score'),
            'user_satisfaction_score': feedback_data.get('user_satisfaction_score'),
            'feedback_notes': feedback_data.get('feedback_notes')
        })

        await db.commit()

        # Update template effectiveness score
        await self._update_template_effectiveness(db, template_id)

        # Update success patterns based on feedback
        await self._update_success_patterns(db, template_id, feedback_data)

    async def _update_template_effectiveness(self, db: AsyncSession, template_id: UUID):
        """Update template effectiveness score based on feedback"""
        query = text("""
            UPDATE referral_templates
            SET effectiveness_score = (
                SELECT AVG(
                    CASE WHEN tf.got_response THEN 1.0 ELSE 0.0 END * 0.6 +
                    COALESCE(tf.response_quality_score, 3) / 5.0 * 0.2 +
                    COALESCE(tf.user_satisfaction_score, 3) / 5.0 * 0.2
                )
                FROM template_feedback tf
                WHERE tf.template_id = :template_id
            )
            WHERE id = :template_id
        """)

        await db.execute(query, {'template_id': template_id})
        await db.commit()

    async def _update_success_patterns(
        self,
        db: AsyncSession,
        template_id: UUID,
        feedback_data: Dict[str, Any]
    ):
        """Update success patterns based on template feedback"""
        # Get template details
        template_query = text("""
            SELECT template_style, personalization_level, effectiveness_score
            FROM referral_templates
            WHERE id = :template_id
        """)

        result = await db.execute(template_query, {'template_id': template_id})
        template = result.fetchone()

        if not template:
            return

        # Update relevant patterns
        got_response = feedback_data.get('got_response', False)

        update_query = text("""
            UPDATE template_success_patterns
            SET
                total_uses = total_uses + 1,
                successful_uses = successful_uses + :success_increment,
                success_rate = (successful_uses + :success_increment) / (total_uses + 1.0),
                updated_at = NOW()
            WHERE pattern_name = :pattern_name
        """)

        pattern_name = f"{template.template_style.title()} {template.personalization_level.title()}"
        success_increment = 1 if got_response else 0

        await db.execute(update_query, {
            'success_increment': success_increment,
            'pattern_name': pattern_name
        })

        await db.commit()

    async def get_user_templates(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's referral templates with stats"""
        query = text("""
            SELECT rt.id, rt.contact_name, rt.contact_company, rt.subject_line,
                   rt.email_body, rt.template_style, rt.was_sent, rt.sent_at,
                   rt.got_response, rt.response_type, rt.effectiveness_score,
                   rt.created_at,
                   tf.response_quality_score, tf.user_satisfaction_score
            FROM referral_templates rt
            LEFT JOIN template_feedback tf ON rt.id = tf.template_id
            WHERE rt.user_id = :user_id
            ORDER BY rt.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await db.execute(query, {
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
                'was_sent': row.was_sent,
                'sent_at': row.sent_at.isoformat() if row.sent_at else None,
                'got_response': row.got_response,
                'response_type': row.response_type,
                'effectiveness_score': row.effectiveness_score,
                'created_at': row.created_at.isoformat(),
                'user_feedback': {
                    'response_quality_score': row.response_quality_score,
                    'user_satisfaction_score': row.user_satisfaction_score
                } if row.response_quality_score else None
            })

        return templates

    async def get_template_stats(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        """Get user's template statistics"""
        query = text("""
            SELECT
                COUNT(*) as total_templates,
                COUNT(CASE WHEN was_sent THEN 1 END) as sent_count,
                COUNT(CASE WHEN got_response THEN 1 END) as response_count,
                AVG(effectiveness_score) as avg_effectiveness,
                COUNT(CASE WHEN was_sent = false THEN 1 END) as draft_count
            FROM referral_templates
            WHERE user_id = :user_id
        """)

        result = await db.execute(query, {'user_id': user_id})
        row = result.fetchone()

        return {
            'total_templates': row.total_templates,
            'sent_count': row.sent_count,
            'response_count': row.response_count,
            'response_rate': (row.response_count / max(row.sent_count, 1)) * 100,
            'avg_effectiveness': float(row.avg_effectiveness or 0),
            'draft_count': row.draft_count
        }

# Create singleton instance
referral_template_service = ReferralTemplateService()