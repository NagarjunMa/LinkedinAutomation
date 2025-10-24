"""
Email API endpoints for JobFlow Pro
Handles email notifications, welcome emails, and user communications using Resend
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.db.session import get_db
from app.models.user import User
from app.services.resend_email_service import resend_email_service as email_service
from app.core.auth import get_authenticated_user_id
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class SendWelcomeEmailRequest(BaseModel):
    """Request schema for sending welcome email"""
    user_email: EmailStr
    user_name: str
    user_id: Optional[str] = None

class SendFeatureUpdateRequest(BaseModel):
    """Request schema for sending feature update email"""
    user_email: EmailStr
    user_name: str
    update_title: str
    update_description: str
    features: Optional[List[Dict[str, str]]] = None
    cta_url: Optional[str] = None

class SendBulkNotificationRequest(BaseModel):
    """Request schema for sending bulk notifications"""
    recipients: List[Dict[str, str]]  # [{"email": "user@example.com", "name": "User Name"}]
    subject: str
    template_name: str
    template_data: Dict[str, Any]
    batch_size: Optional[int] = 50

class EmailTestRequest(BaseModel):
    """Request schema for testing email service"""
    test_email: EmailStr

class EmailResponse(BaseModel):
    """Response schema for email operations"""
    success: bool
    message: str
    email_sent: Optional[bool] = None

class BulkEmailResponse(BaseModel):
    """Response schema for bulk email operations"""
    success: bool
    message: str
    results: Dict[str, int]  # {"success": 10, "failed": 2}


@router.post("/send-welcome", response_model=EmailResponse)
async def send_welcome_email(
    request: SendWelcomeEmailRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """
    Send welcome email to a new user
    """
    try:
        # Add email sending to background tasks for better performance
        background_tasks.add_task(
            email_service.send_welcome_email,
            request.user_email,
            request.user_name,
            request.user_id
        )

        logger.info(f"Welcome email queued for {request.user_email}")

        return EmailResponse(
            success=True,
            message=f"Welcome email queued successfully for {request.user_email}",
            email_sent=True
        )

    except Exception as e:
        logger.error(f"Error queueing welcome email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue welcome email: {str(e)}")

@router.post("/send-feature-update", response_model=EmailResponse)
async def send_feature_update_email(
    request: SendFeatureUpdateRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """
    Send feature update email to a user
    """
    try:
        # Add email sending to background tasks
        background_tasks.add_task(
            email_service.send_feature_update_email,
            request.user_email,
            request.user_name,
            request.update_title,
            request.update_description,
            request.features,
            request.cta_url
        )

        logger.info(f"Feature update email queued for {request.user_email}")

        return EmailResponse(
            success=True,
            message=f"Feature update email queued successfully for {request.user_email}",
            email_sent=True
        )

    except Exception as e:
        logger.error(f"Error queueing feature update email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue feature update email: {str(e)}")

@router.post("/send-bulk-notification", response_model=BulkEmailResponse)
async def send_bulk_notification(
    request: SendBulkNotificationRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """
    Send bulk notification emails to multiple users
    """
    try:
        if len(request.recipients) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Maximum 1000 recipients allowed per batch"
            )

        # Add bulk email sending to background tasks
        background_tasks.add_task(
            email_service.send_bulk_notification,
            request.recipients,
            request.subject,
            request.template_name,
            request.template_data,
            request.batch_size
        )

        logger.info(f"Bulk notification queued for {len(request.recipients)} recipients")

        return BulkEmailResponse(
            success=True,
            message=f"Bulk notification queued successfully for {len(request.recipients)} recipients",
            results={"queued": len(request.recipients), "processing": 0}
        )

    except Exception as e:
        logger.error(f"Error queueing bulk notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue bulk notification: {str(e)}")

@router.post("/test-email-service", response_model=EmailResponse)
async def test_email_service_endpoint(
    request: EmailTestRequest,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """
    Test email service configuration by sending a test email
    """
    try:
        # Send test email synchronously for immediate feedback
        success = await email_service.test_email_service(request.test_email)

        if success:
            return EmailResponse(
                success=True,
                message=f"Test email sent successfully to {request.test_email}",
                email_sent=True
            )
        else:
            return EmailResponse(
                success=False,
                message="Test email failed to send. Check email service configuration.",
                email_sent=False
            )

    except Exception as e:
        logger.error(f"Error testing email service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email service test failed: {str(e)}")

@router.post("/send-job-alert", response_model=EmailResponse)
async def send_job_alert_email(
    user_email: EmailStr,
    user_name: str,
    job_matches: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    total_matches: Optional[int] = None,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """
    Send job alert email with matching opportunities
    """
    try:
        if len(job_matches) > 20:
            job_matches = job_matches[:20]  # Limit to 20 matches per email

        # Add email sending to background tasks
        background_tasks.add_task(
            email_service.send_job_alert_email,
            user_email,
            user_name,
            job_matches,
            total_matches
        )

        logger.info(f"Job alert email queued for {user_email} with {len(job_matches)} matches")

        return EmailResponse(
            success=True,
            message=f"Job alert email queued successfully for {user_email}",
            email_sent=True
        )

    except Exception as e:
        logger.error(f"Error queueing job alert email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue job alert email: {str(e)}")

@router.post("/send-weekly-summary", response_model=EmailResponse)
async def send_weekly_summary_email(
    user_email: EmailStr,
    user_name: str,
    stats: Dict[str, Any],
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """
    Send weekly summary of user's job search activity
    """
    try:
        # Add email sending to background tasks
        background_tasks.add_task(
            email_service.send_weekly_summary_email,
            user_email,
            user_name,
            stats
        )

        logger.info(f"Weekly summary email queued for {user_email}")

        return EmailResponse(
            success=True,
            message=f"Weekly summary email queued successfully for {user_email}",
            email_sent=True
        )

    except Exception as e:
        logger.error(f"Error queueing weekly summary email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue weekly summary email: {str(e)}")

@router.get("/email-service-status")
async def get_email_service_status(
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """
    Get Resend email service configuration status
    """
    try:
        # Get status from the Resend email service
        status = await email_service.get_email_stats()

        return {
            "success": True,
            "message": "Resend email service status retrieved successfully",
            "status": status
        }

    except Exception as e:
        logger.error(f"Error getting Resend email service status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get Resend email service status: {str(e)}")

# Utility endpoint for triggering welcome emails on user registration
async def trigger_welcome_email(user_email: str, user_name: str, user_id: str = None):
    """
    Utility function to be called from user registration endpoint
    """
    try:
        success = await email_service.send_welcome_email(user_email, user_name, user_id)
        logger.info(f"Welcome email triggered for new user: {user_email}, success: {success}")
        return success
    except Exception as e:
        logger.error(f"Failed to trigger welcome email for {user_email}: {str(e)}")
        return False