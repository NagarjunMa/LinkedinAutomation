"""
SendGrid Email Service for JobFlow Pro
Professional email service using SendGrid API for better deliverability and analytics
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent, PlainTextContent
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import EmailStr

from app.core.config import settings

logger = logging.getLogger(__name__)

class SendGridEmailService:
    """
    Professional email service using SendGrid API
    Provides better deliverability, analytics, and reliability than SMTP
    """

    def __init__(self):
        if not settings.SENDGRID_API_KEY:
            logger.warning("SendGrid API key not configured. Email service will use fallback mode.")
            self.client = None
        else:
            self.client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

        # Setup Jinja2 template environment
        template_dir = Path(__file__).parent / "email_templates"
        template_dir.mkdir(exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        self.from_email = From(settings.MAIL_FROM, settings.MAIL_FROM_NAME)

    async def send_welcome_email(
        self,
        user_email: EmailStr,
        user_name: str,
        user_id: str = None
    ) -> bool:
        """
        Send welcome email to newly registered users using SendGrid
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
            plain_text = await self._extract_plain_text(html_content)

            # Create SendGrid message
            message = Mail(
                from_email=self.from_email,
                to_emails=To(user_email),
                subject=Subject("🎉 Welcome to JobFlow Pro - Your AI-Powered Job Search Partner!"),
                html_content=HtmlContent(html_content),
                plain_text_content=PlainTextContent(plain_text)
            )

            # Add tracking and analytics
            message.tracking_settings = self._get_tracking_settings()

            # Send email
            if self.client:
                response = self.client.send(message)
                logger.info(f"Welcome email sent successfully to {user_email}. SendGrid response: {response.status_code}")
                return response.status_code == 202
            else:
                logger.warning(f"SendGrid client not configured. Email not sent to {user_email}")
                return False

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
        Send feature update notifications using SendGrid
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
            plain_text = await self._extract_plain_text(html_content)

            message = Mail(
                from_email=self.from_email,
                to_emails=To(user_email),
                subject=Subject(f"🚀 {update_title} - JobFlow Pro Updates"),
                html_content=HtmlContent(html_content),
                plain_text_content=PlainTextContent(plain_text)
            )

            message.tracking_settings = self._get_tracking_settings()

            if self.client:
                response = self.client.send(message)
                logger.info(f"Feature update email sent to {user_email}. Response: {response.status_code}")
                return response.status_code == 202
            else:
                logger.warning(f"SendGrid client not configured. Email not sent to {user_email}")
                return False

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

            # Create job alert template if it doesn't exist
            html_content = await self._render_template("job_alert.html", template_data)
            plain_text = await self._extract_plain_text(html_content)

            subject = f"💼 {len(job_matches)} New Job Matches Found!"
            if len(job_matches) == 1:
                subject = "💼 Perfect Job Match Found!"

            message = Mail(
                from_email=self.from_email,
                to_emails=To(user_email),
                subject=Subject(subject),
                html_content=HtmlContent(html_content),
                plain_text_content=PlainTextContent(plain_text)
            )

            message.tracking_settings = self._get_tracking_settings()

            if self.client:
                response = self.client.send(message)
                logger.info(f"Job alert email sent to {user_email} with {len(job_matches)} matches. Response: {response.status_code}")
                return response.status_code == 202
            else:
                logger.warning(f"SendGrid client not configured. Email not sent to {user_email}")
                return False

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
            plain_text = await self._extract_plain_text(html_content)

            message = Mail(
                from_email=self.from_email,
                to_emails=To(user_email),
                subject=Subject("📊 Your Weekly Job Search Summary - JobFlow Pro"),
                html_content=HtmlContent(html_content),
                plain_text_content=PlainTextContent(plain_text)
            )

            message.tracking_settings = self._get_tracking_settings()

            if self.client:
                response = self.client.send(message)
                logger.info(f"Weekly summary email sent to {user_email}. Response: {response.status_code}")
                return response.status_code == 202
            else:
                logger.warning(f"SendGrid client not configured. Email not sent to {user_email}")
                return False

        except Exception as e:
            logger.error(f"Failed to send weekly summary email to {user_email}: {str(e)}")
            return False

    async def send_bulk_notification(
        self,
        recipients: List[Dict[str, str]],  # [{"email": "user@example.com", "name": "User Name"}]
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        batch_size: int = 1000  # SendGrid allows up to 1000 per batch
    ) -> Dict[str, int]:
        """
        Send bulk notifications using SendGrid's batch sending
        """
        results = {"success": 0, "failed": 0}

        # Process in batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]

            try:
                # Create batch message
                message = Mail(
                    from_email=self.from_email,
                    subject=Subject(subject)
                )

                # Add all recipients to the batch
                for recipient in batch:
                    user_template_data = {
                        **template_data,
                        "user_name": recipient.get("name", "User"),
                        "user_email": recipient.get("email"),
                        "current_year": datetime.now().year,
                        "app_name": "JobFlow Pro"
                    }

                    html_content = await self._render_template(template_name, user_template_data)
                    plain_text = await self._extract_plain_text(html_content)

                    message.add_to(To(recipient["email"]))

                # Set content for the batch
                message.html_content = HtmlContent(html_content)
                message.plain_text_content = PlainTextContent(plain_text)
                message.tracking_settings = self._get_tracking_settings()

                # Send batch
                if self.client:
                    response = self.client.send(message)
                    if response.status_code == 202:
                        results["success"] += len(batch)
                        logger.info(f"Batch email sent successfully to {len(batch)} recipients")
                    else:
                        results["failed"] += len(batch)
                        logger.error(f"Batch email failed with status {response.status_code}")
                else:
                    results["failed"] += len(batch)
                    logger.warning("SendGrid client not configured")

                # Rate limiting delay between batches
                if i + batch_size < len(recipients):
                    await asyncio.sleep(1)  # 1 second delay between batches

            except Exception as e:
                logger.error(f"Failed to send batch email: {str(e)}")
                results["failed"] += len(batch)

        logger.info(f"Bulk notification completed: {results['success']} sent, {results['failed']} failed")
        return results

    async def test_email_service(self, test_email: EmailStr) -> bool:
        """
        Test SendGrid email service configuration
        """
        try:
            if not self.client:
                logger.error("SendGrid client not configured")
                return False

            await self.send_welcome_email(test_email, "Test User", "test_user_123")
            return True
        except Exception as e:
            logger.error(f"SendGrid email service test failed: {str(e)}")
            return False

    async def get_email_stats(self) -> Dict[str, Any]:
        """
        Get email statistics from SendGrid (requires additional setup)
        """
        try:
            if not self.client:
                return {"error": "SendGrid client not configured"}

            # Note: This requires SendGrid Email Activity API setup
            # For now, return basic status
            return {
                "service": "SendGrid",
                "status": "configured",
                "from_email": settings.MAIL_FROM,
                "from_name": settings.MAIL_FROM_NAME
            }

        except Exception as e:
            logger.error(f"Failed to get email stats: {str(e)}")
            return {"error": str(e)}

    def _get_tracking_settings(self) -> Dict[str, Any]:
        """
        Configure SendGrid tracking settings for analytics
        """
        from sendgrid.helpers.mail import (
            ClickTracking, OpenTracking, SubscriptionTracking
        )

        tracking_settings = {
            "click_tracking": ClickTracking(enable=True, enable_text=False),
            "open_tracking": OpenTracking(enable=True),
            "subscription_tracking": SubscriptionTracking(enable=False)
        }

        return tracking_settings

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

    async def _extract_plain_text(self, html_content: str) -> str:
        """
        Extract plain text from HTML content for better email compatibility
        """
        try:
            # Simple HTML to text conversion
            import re

            # Remove HTML tags
            clean = re.compile('<.*?>')
            plain_text = re.sub(clean, '', html_content)

            # Clean up whitespace
            plain_text = re.sub(r'\s+', ' ', plain_text).strip()

            # Add line breaks for better readability
            plain_text = plain_text.replace('Welcome to JobFlow Pro!', 'Welcome to JobFlow Pro!\n\n')
            plain_text = plain_text.replace('Thank you for joining', '\nThank you for joining')

            return plain_text

        except Exception as e:
            logger.error(f"Failed to extract plain text: {str(e)}")
            return "Thank you for using JobFlow Pro! Visit your dashboard to get started."

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
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 8px 8px;
                }}
                .button {{
                    display: inline-block;
                    background: #48bb78;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 14px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 {app_name}</h1>
                <p>AI-Powered Job Search Automation</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Thank you for using {app_name}! We're here to help you streamline your job search with AI-powered automation.</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:3000/dashboard" class="button">Open Dashboard →</a>
                </p>
                <p>Get started with:</p>
                <ul>
                    <li>🤖 AI Question Answering</li>
                    <li>📊 Smart Analytics</li>
                    <li>📝 Resume Analysis</li>
                    <li>🔗 Job Extraction</li>
                </ul>
            </div>
            <div class="footer">
                <p>&copy; {context.get('current_year', 2024)} {app_name}. All rights reserved.</p>
                <p>Need help? Contact us at {context.get('support_email', 'support@jobflowpro.com')}</p>
            </div>
        </body>
        </html>
        """


# Singleton instance
sendgrid_email_service = SendGridEmailService()