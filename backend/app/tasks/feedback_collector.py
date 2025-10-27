"""
Feedback Collection Tasks
Automated tasks for collecting template effectiveness feedback
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID

from celery import Celery
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.config import settings
from app.services.email_service import send_email

logger = logging.getLogger(__name__)

# Initialize Celery (you'll need to configure this based on your setup)
celery_app = Celery(
    'feedback_collector',
    broker=settings.redis_url or 'redis://localhost:6379/0',
    backend=settings.redis_url or 'redis://localhost:6379/0'
)

class FeedbackCollector:
    def __init__(self):
        self.session_factory = get_async_session

    async def schedule_feedback_collection(
        self,
        template_id: UUID,
        user_id: UUID,
        days_after_sent: int = 15
    ):
        """
        Schedule feedback collection for a template
        """
        collection_date = datetime.utcnow() + timedelta(days=days_after_sent)

        # Schedule the task
        collect_template_feedback_task.apply_async(
            args=[str(template_id), str(user_id)],
            eta=collection_date
        )

        logger.info(f"Scheduled feedback collection for template {template_id} on {collection_date}")

    async def collect_overdue_feedback(self):
        """
        Collect feedback for templates that are overdue for follow-up
        """
        async with self.session_factory() as db:
            # Find templates that were sent but haven't received feedback
            query = text("""
                SELECT rt.id, rt.user_id, rt.contact_name, rt.contact_company,
                       rt.subject_line, rt.sent_at, u.email, u.first_name
                FROM referral_templates rt
                JOIN users u ON rt.user_id = u.id
                LEFT JOIN template_feedback tf ON rt.id = tf.template_id
                WHERE rt.was_sent = true
                AND rt.sent_at <= NOW() - INTERVAL '15 days'
                AND tf.id IS NULL
                AND rt.sent_at >= NOW() - INTERVAL '60 days'  -- Don't collect for very old templates
                ORDER BY rt.sent_at DESC
            """)

            result = await db.execute(query)
            overdue_templates = result.fetchall()

            for template in overdue_templates:
                await self._send_feedback_request_email(
                    db=db,
                    template_data={
                        'id': template.id,
                        'user_id': template.user_id,
                        'contact_name': template.contact_name,
                        'contact_company': template.contact_company,
                        'subject_line': template.subject_line,
                        'sent_at': template.sent_at,
                        'user_email': template.email,
                        'user_name': template.first_name
                    }
                )

    async def _send_feedback_request_email(self, db: AsyncSession, template_data: Dict[str, Any]):
        """
        Send an email requesting feedback about template effectiveness
        """
        try:
            user_name = template_data['user_name']
            contact_name = template_data['contact_name']
            contact_company = template_data['contact_company']
            template_id = template_data['id']

            # Create feedback URL (you'll need to implement the frontend route)
            feedback_url = f"{settings.frontend_url}/dashboard/referrals/feedback/{template_id}"

            email_content = f"""
            Hi {user_name},

            It's been about 15 days since you generated a referral email template for {contact_name} at {contact_company}.

            Could you please take a moment to let us know how it went? Your feedback helps improve our AI for future templates.

            Quick Feedback Questions:
            • Did {contact_name} respond to your email?
            • If yes, what type of response did you receive?
            • How satisfied were you with the generated template?

            Click here to provide feedback: {feedback_url}

            This will only take 30 seconds and helps us learn what works best.

            Thanks!
            The JobSync Team
            """

            await send_email(
                to_email=template_data['user_email'],
                subject=f"Quick feedback: How did your referral to {contact_name} go?",
                content=email_content,
                content_type="text/plain"
            )

            # Mark that we've sent a feedback request
            await self._mark_feedback_requested(db, template_data['id'])

            logger.info(f"Sent feedback request email for template {template_id}")

        except Exception as e:
            logger.error(f"Error sending feedback request email: {str(e)}")

    async def _mark_feedback_requested(self, db: AsyncSession, template_id: UUID):
        """
        Mark that we've requested feedback for this template
        """
        query = text("""
            INSERT INTO template_feedback (template_id, user_id, follow_up_scheduled)
            SELECT id, user_id, NOW()
            FROM referral_templates
            WHERE id = :template_id
            ON CONFLICT (template_id, user_id) DO UPDATE SET
                follow_up_scheduled = NOW()
        """)

        await db.execute(query, {'template_id': template_id})
        await db.commit()

    async def analyze_feedback_patterns(self):
        """
        Analyze collected feedback to update success patterns
        """
        async with self.session_factory() as db:
            # Get feedback data for pattern analysis
            query = text("""
                SELECT rt.template_style, rt.personalization_level,
                       tf.got_response, tf.response_type, tf.response_quality_score,
                       tf.user_satisfaction_score, rt.effectiveness_score,
                       ta.generation_context
                FROM referral_templates rt
                JOIN template_feedback tf ON rt.id = tf.template_id
                LEFT JOIN template_analytics ta ON rt.id = ta.template_id
                WHERE tf.feedback_date >= NOW() - INTERVAL '30 days'
                AND tf.got_response IS NOT NULL
            """)

            result = await db.execute(query)
            feedback_data = result.fetchall()

            # Analyze patterns
            patterns = self._analyze_success_patterns(feedback_data)

            # Update success patterns in database
            for pattern_name, pattern_data in patterns.items():
                await self._update_pattern_data(db, pattern_name, pattern_data)

    def _analyze_success_patterns(self, feedback_data: List) -> Dict[str, Dict]:
        """
        Analyze feedback data to identify successful patterns
        """
        patterns = {}

        # Group by style and personalization level
        style_groups = {}
        for row in feedback_data:
            key = f"{row.template_style}_{row.personalization_level}"
            if key not in style_groups:
                style_groups[key] = []
            style_groups[key].append(row)

        # Calculate success metrics for each group
        for group_key, group_data in style_groups.items():
            if len(group_data) < 5:  # Need minimum data points
                continue

            total_responses = len(group_data)
            successful_responses = sum(1 for row in group_data if row.got_response)
            high_quality_responses = sum(
                1 for row in group_data
                if row.response_quality_score and row.response_quality_score >= 4
            )
            high_satisfaction = sum(
                1 for row in group_data
                if row.user_satisfaction_score and row.user_satisfaction_score >= 4
            )

            success_rate = successful_responses / total_responses
            quality_rate = high_quality_responses / max(successful_responses, 1)
            satisfaction_rate = high_satisfaction / total_responses

            # Calculate composite score
            composite_score = (success_rate * 0.5 + quality_rate * 0.25 + satisfaction_rate * 0.25)

            patterns[group_key] = {
                'success_rate': success_rate,
                'quality_rate': quality_rate,
                'satisfaction_rate': satisfaction_rate,
                'composite_score': composite_score,
                'total_uses': total_responses,
                'successful_uses': successful_responses
            }

        return patterns

    async def _update_pattern_data(self, db: AsyncSession, pattern_name: str, pattern_data: Dict):
        """
        Update success pattern data in the database
        """
        query = text("""
            UPDATE template_success_patterns
            SET
                success_rate = :success_rate,
                total_uses = total_uses + :total_uses,
                successful_uses = successful_uses + :successful_uses,
                pattern_data = COALESCE(pattern_data, '{}'::jsonb) || :pattern_data::jsonb,
                updated_at = NOW()
            WHERE pattern_name = :pattern_name
        """)

        await db.execute(query, {
            'pattern_name': pattern_name,
            'success_rate': pattern_data['success_rate'],
            'total_uses': pattern_data['total_uses'],
            'successful_uses': pattern_data['successful_uses'],
            'pattern_data': str(pattern_data)  # Convert to JSON string
        })

        await db.commit()

    async def send_weekly_insights_digest(self):
        """
        Send weekly digest of insights to users who have opted in
        """
        async with self.session_factory() as db:
            # Get users who want weekly digests
            query = text("""
                SELECT u.id, u.email, u.first_name
                FROM users u
                JOIN user_referral_preferences urp ON u.id = urp.user_id
                WHERE urp.weekly_digest = true
                AND urp.learning_enabled = true
            """)

            result = await db.execute(query)
            users = result.fetchall()

            for user in users:
                await self._send_user_insights_digest(db, user)

    async def _send_user_insights_digest(self, db: AsyncSession, user_data):
        """
        Send personalized insights digest to a user
        """
        try:
            user_id = user_data.id
            user_email = user_data.email
            user_name = user_data.first_name

            # Get user's template performance from last week
            query = text("""
                SELECT COUNT(*) as total_templates,
                       COUNT(CASE WHEN was_sent THEN 1 END) as sent_count,
                       COUNT(CASE WHEN got_response THEN 1 END) as response_count,
                       AVG(effectiveness_score) as avg_effectiveness
                FROM referral_templates
                WHERE user_id = :user_id
                AND created_at >= NOW() - INTERVAL '7 days'
            """)

            result = await db.execute(query, {'user_id': user_id})
            stats = result.fetchone()

            if stats.total_templates == 0:
                return  # Skip if no activity

            response_rate = (stats.response_count / max(stats.sent_count, 1)) * 100

            # Get top performing pattern for this user
            pattern_query = text("""
                SELECT template_style, personalization_level,
                       AVG(effectiveness_score) as avg_score
                FROM referral_templates
                WHERE user_id = :user_id
                AND effectiveness_score > 0
                GROUP BY template_style, personalization_level
                ORDER BY avg_score DESC
                LIMIT 1
            """)

            result = await db.execute(pattern_query, {'user_id': user_id})
            best_pattern = result.fetchone()

            email_content = f"""
            Hi {user_name},

            Here's your weekly referral insights:

            📊 This Week's Performance:
            • Templates Generated: {stats.total_templates}
            • Templates Sent: {stats.sent_count}
            • Response Rate: {response_rate:.1f}%
            • Avg Effectiveness: {(stats.avg_effectiveness or 0) * 100:.1f}%

            🎯 Best Performing Style:
            {best_pattern.template_style.title() if best_pattern else 'Professional'} tone with {best_pattern.personalization_level if best_pattern else 'medium'} personalization

            💡 Tip of the Week:
            Templates with specific company research and personal connections have 40% higher response rates.

            Keep up the great work!
            The JobSync Team
            """

            await send_email(
                to_email=user_email,
                subject="Your Weekly Referral Insights",
                content=email_content,
                content_type="text/plain"
            )

            logger.info(f"Sent weekly insights digest to user {user_id}")

        except Exception as e:
            logger.error(f"Error sending insights digest: {str(e)}")

# Celery tasks
@celery_app.task
def collect_template_feedback_task(template_id: str, user_id: str):
    """
    Celery task to collect feedback for a specific template
    """
    async def _collect():
        collector = FeedbackCollector()
        async with collector.session_factory() as db:
            await collector._send_feedback_request_email(
                db, {'id': UUID(template_id), 'user_id': UUID(user_id)}
            )

    asyncio.run(_collect())

@celery_app.task
def collect_overdue_feedback_task():
    """
    Celery task to collect all overdue feedback
    """
    async def _collect():
        collector = FeedbackCollector()
        await collector.collect_overdue_feedback()

    asyncio.run(_collect())

@celery_app.task
def analyze_feedback_patterns_task():
    """
    Celery task to analyze feedback patterns
    """
    async def _analyze():
        collector = FeedbackCollector()
        await collector.analyze_feedback_patterns()

    asyncio.run(_analyze())

@celery_app.task
def send_weekly_insights_digest_task():
    """
    Celery task to send weekly insights digest
    """
    async def _send():
        collector = FeedbackCollector()
        await collector.send_weekly_insights_digest()

    asyncio.run(_send())

# Schedule periodic tasks (you can also configure this in your Celery beat scheduler)
celery_app.conf.beat_schedule = {
    'collect-overdue-feedback': {
        'task': 'app.tasks.feedback_collector.collect_overdue_feedback_task',
        'schedule': 86400.0,  # Daily
    },
    'analyze-feedback-patterns': {
        'task': 'app.tasks.feedback_collector.analyze_feedback_patterns_task',
        'schedule': 604800.0,  # Weekly
    },
    'send-weekly-insights': {
        'task': 'app.tasks.feedback_collector.send_weekly_insights_digest_task',
        'schedule': 604800.0,  # Weekly (Sundays)
    },
}

# Create instance for direct usage
feedback_collector = FeedbackCollector()