"""
Email Service for JobFlow Pro
Handles all email communications including registration, notifications, and updates
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import EmailStr

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Comprehensive email service for JobFlow Pro
    Handles user registration, notifications, updates, and marketing emails
    """

    def __init__(self):
        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=settings.USE_CREDENTIALS,
            VALIDATE_CERTS=settings.VALIDATE_CERTS,
            TEMPLATE_FOLDER=Path(__file__).parent / "email_templates"
        )

        # Initialize FastMail instance
        self.fast_mail = FastMail(self.config)

        # Setup Jinja2 template environment
        template_dir = Path(__file__).parent / "email_templates"
        template_dir.mkdir(exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    async def send_welcome_email(
        self,
        user_email: EmailStr,
        user_name: str,
        user_id: str = None
    ) -> bool:
        """
        Send welcome email to newly registered users
        """
        try:
            # Prepare template data
            template_data = {
                "user_name": user_name,
                "user_email": user_email,
                "dashboard_url": "http://localhost:3000/dashboard",
                "support_email": settings.MAIL_FROM,
                "current_year": datetime.now().year,
                "user_id": user_id or "new_user",
                "app_name": "JobFlow Pro"
            }

            # Get HTML content
            html_content = await self._render_template("welcome.html", template_data)

            # Create message
            message = MessageSchema(
                subject="🎉 Welcome to JobFlow Pro - Your AI-Powered Job Search Partner!",
                recipients=[user_email],
                body=html_content,
                subtype=MessageType.html
            )

            # Send email
            await self.fast_mail.send_message(message)

            logger.info(f"Welcome email sent successfully to {user_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send welcome email to {user_email}: {str(e)}")
            return False

    async def send_feature_update_email(
        self,
        user_email: EmailStr,
        user_name: str,
        update_title: str,
        update_description: str,
        features: List[Dict[str, str]] = None,
        cta_url: str = None
    ) -> bool:
        """
        Send feature update notifications to users
        """
        try:
            template_data = {
                "user_name": user_name,
                "update_title": update_title,
                "update_description": update_description,
                "features": features or [],
                "cta_url": cta_url or "http://localhost:3000/dashboard",
                "support_email": settings.MAIL_FROM,
                "current_year": datetime.now().year,
                "app_name": "JobFlow Pro"
            }

            html_content = await self._render_template("feature_update.html", template_data)

            message = MessageSchema(
                subject=f"🚀 {update_title} - JobFlow Pro Updates",
                recipients=[user_email],
                body=html_content,
                subtype=MessageType.html
            )

            await self.fast_mail.send_message(message)

            logger.info(f"Feature update email sent to {user_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send feature update email to {user_email}: {str(e)}")
            return False

    async def send_job_alert_email(
        self,
        user_email: EmailStr,
        user_name: str,
        job_matches: List[Dict[str, Any]],
        total_matches: int = None
    ) -> bool:
        """
        Send job alert emails with matching opportunities
        """
        try:
            template_data = {
                "user_name": user_name,
                "job_matches": job_matches,
                "total_matches": total_matches or len(job_matches),
                "dashboard_url": "http://localhost:3000/dashboard/jobs",
                "preferences_url": "http://localhost:3000/dashboard/settings",
                "support_email": settings.MAIL_FROM,
                "current_year": datetime.now().year,
                "app_name": "JobFlow Pro"
            }

            html_content = await self._render_template("job_alert.html", template_data)

            subject = f"💼 {len(job_matches)} New Job Matches Found!"
            if len(job_matches) == 1:
                subject = "💼 Perfect Job Match Found!"

            message = MessageSchema(
                subject=subject,
                recipients=[user_email],
                body=html_content,
                subtype=MessageType.html
            )

            await self.fast_mail.send_message(message)

            logger.info(f"Job alert email sent to {user_email} with {len(job_matches)} matches")
            return True

        except Exception as e:
            logger.error(f"Failed to send job alert email to {user_email}: {str(e)}")
            return False

    async def send_weekly_summary_email(
        self,
        user_email: EmailStr,
        user_name: str,
        stats: Dict[str, Any]
    ) -> bool:
        """
        Send weekly summary of user's job search activity
        """
        try:
            template_data = {
                "user_name": user_name,
                "stats": stats,
                "dashboard_url": "http://localhost:3000/dashboard",
                "analytics_url": "http://localhost:3000/dashboard/analytics",
                "support_email": settings.MAIL_FROM,
                "current_year": datetime.now().year,
                "app_name": "JobFlow Pro",
                "week_start": stats.get("week_start", "This week"),
                "week_end": stats.get("week_end", "")
            }

            html_content = await self._render_template("weekly_summary.html", template_data)

            message = MessageSchema(
                subject="📊 Your Weekly Job Search Summary - JobFlow Pro",
                recipients=[user_email],
                body=html_content,
                subtype=MessageType.html
            )

            await self.fast_mail.send_message(message)

            logger.info(f"Weekly summary email sent to {user_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send weekly summary email to {user_email}: {str(e)}")
            return False

    async def send_bulk_notification(
        self,
        recipients: List[Dict[str, str]],  # [{"email": "user@example.com", "name": "User Name"}]
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        batch_size: int = 50
    ) -> Dict[str, int]:
        """
        Send bulk notifications with rate limiting
        Returns success and failure counts
        """
        results = {"success": 0, "failed": 0}

        # Process in batches to avoid rate limiting
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]

            # Create tasks for concurrent sending
            tasks = []
            for recipient in batch:
                user_template_data = {
                    **template_data,
                    "user_name": recipient.get("name", "User"),
                    "user_email": recipient.get("email"),
                    "current_year": datetime.now().year,
                    "app_name": "JobFlow Pro"
                }

                task = self._send_single_notification(
                    recipient["email"],
                    subject,
                    template_name,
                    user_template_data
                )
                tasks.append(task)

            # Execute batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count results
            for result in batch_results:
                if isinstance(result, Exception):
                    results["failed"] += 1
                elif result:
                    results["success"] += 1
                else:
                    results["failed"] += 1

            # Rate limiting delay between batches
            if i + batch_size < len(recipients):
                await asyncio.sleep(2)  # 2 second delay between batches

        logger.info(f"Bulk notification completed: {results['success']} sent, {results['failed']} failed")
        return results

    async def _send_single_notification(
        self,
        email: EmailStr,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> bool:
        """
        Send a single notification email
        """
        try:
            html_content = await self._render_template(template_name, template_data)

            message = MessageSchema(
                subject=subject,
                recipients=[email],
                body=html_content,
                subtype=MessageType.html
            )

            await self.fast_mail.send_message(message)
            return True

        except Exception as e:
            logger.error(f"Failed to send notification to {email}: {str(e)}")
            return False

    async def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render email template with given context
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            # Return fallback HTML
            return await self._get_fallback_template(context)

    async def _get_fallback_template(self, context: Dict[str, Any]) -> str:
        """
        Generate fallback email template when template file is missing
        """
        user_name = context.get("user_name", "User")
        app_name = context.get("app_name", "JobFlow Pro")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{app_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{app_name}</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    <p>Thank you for using {app_name}. We're here to help you streamline your job search with AI-powered automation.</p>
                    <p>Visit your dashboard to get started: <a href="http://localhost:3000/dashboard">Dashboard</a></p>
                </div>
                <div class="footer">
                    <p>&copy; {context.get('current_year', 2024)} {app_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

    async def test_email_service(self, test_email: EmailStr) -> bool:
        """
        Test email service configuration
        """
        try:
            await self.send_welcome_email(test_email, "Test User", "test_user_123")
            return True
        except Exception as e:
            logger.error(f"Email service test failed: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()