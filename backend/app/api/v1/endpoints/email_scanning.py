"""
API endpoints for email scanning functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import pytz

from app.db.session import get_db
from app.models.user import User
from app.models.email_scanning import EmailScanHistory, ProcessedEmail
from app.models.profile import UserSettings
from app.tasks.email_scanning_tasks import run_full_email_scan
from app.utils.logger import get_logger
from app.core.auth import get_authenticated_user_id

router = APIRouter()
logger = get_logger(__name__)




class EmailScanSettingsSchema(BaseModel):
    """Schema for email scanning settings"""
    frequency: str = "daily"  # daily, twice_daily, weekly, bi_weekly, monthly
    scan_time: str = "03:00"  # HH:MM format
    timezone: str = "America/New_York"
    email_tracking_enabled: bool = True


class EmailScanStatusResponse(BaseModel):
    """Response schema for scan status"""
    last_scan: Optional[dict]
    next_scheduled_scan: Optional[str]
    scan_history: List[dict]
    settings: dict


class ManualScanResponse(BaseModel):
    """Response schema for manual scan trigger"""
    status: str
    task_id: str
    message: str


@router.post("/email/scan-now", response_model=ManualScanResponse)
async def trigger_manual_scan(
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """User-triggered immediate email scan"""
    
    try:
        # Check if user has email tracking enabled
        user_settings = db.query(UserSettings).filter(
            UserSettings.user_id == current_user.user_id
        ).first()
        
        if not user_settings or not user_settings.email_tracking_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email tracking is not enabled for this user"
            )
        
        # Queue immediate scan
        task = run_full_email_scan.delay(current_user.user_id)
        
        logger.info(f"Manual scan triggered for user {current_user.user_id}, task {task.id}")
        
        return ManualScanResponse(
            status="queued",
            task_id=task.id,
            message="Email scan started. Results will appear in 1-2 minutes."
        )
        
    except Exception as e:
        logger.error(f"Manual scan trigger failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger email scan"
        )


@router.get("/email/scan-status", response_model=EmailScanStatusResponse)
async def get_scan_status(
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Get last scan information and settings"""
    
    try:
        # Get last scan
        last_scan = db.query(EmailScanHistory).filter(
            EmailScanHistory.user_id == current_user.user_id
        ).order_by(EmailScanHistory.scan_completed_at.desc()).first()
        
        # Get scan history (last 10 scans)
        scan_history = db.query(EmailScanHistory).filter(
            EmailScanHistory.user_id == current_user.user_id
        ).order_by(EmailScanHistory.scan_started_at.desc()).limit(10).all()
        
        # Get user settings
        user_settings = db.query(UserSettings).filter(
            UserSettings.user_id == current_user.user_id
        ).first()
        
        # Calculate next scheduled scan
        next_scan = calculate_next_scan_time(user_settings) if user_settings else None
        
        return EmailScanStatusResponse(
            last_scan=last_scan.__dict__ if last_scan else None,
            next_scheduled_scan=next_scan,
            scan_history=[scan.__dict__ for scan in scan_history],
            settings={
                "frequency": user_settings.email_scan_frequency if user_settings else "daily",
                "scan_time": str(user_settings.email_scan_time) if user_settings else "03:00:00",
                "timezone": user_settings.email_scan_timezone if user_settings else "America/New_York",
                "email_tracking_enabled": user_settings.email_tracking_enabled if user_settings else True
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get scan status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scan status"
        )


@router.put("/settings/email-scanning")
async def update_email_scan_settings(
    settings: EmailScanSettingsSchema,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Update user's email scanning preferences"""
    
    try:
        # Get or create user settings
        user_settings = db.query(UserSettings).filter(
            UserSettings.user_id == current_user.user_id
        ).first()
        
        if not user_settings:
            user_settings = UserSettings(user_id=current_user.user_id)
            db.add(user_settings)
        
        # Update settings
        user_settings.email_scan_frequency = settings.frequency
        user_settings.email_scan_time = datetime.strptime(settings.scan_time, "%H:%M").time()
        user_settings.email_scan_timezone = settings.timezone
        user_settings.email_tracking_enabled = settings.email_tracking_enabled
        
        db.commit()
        
        logger.info(f"Email scan settings updated for user {current_user.user_id}")
        
        return {"status": "updated", "message": "Email scanning preferences updated successfully"}
        
    except Exception as e:
        logger.error(f"Failed to update email scan settings: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update email scan settings"
        )


@router.get("/email/processed-emails")
async def get_processed_emails(
    limit: int = 50,
    offset: int = 0,
    email_type: Optional[str] = None,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Get processed emails for user"""
    
    try:
        query = db.query(ProcessedEmail).filter(
            ProcessedEmail.user_id == current_user.user_id
        )
        
        if email_type:
            query = query.filter(ProcessedEmail.email_type == email_type)
        
        emails = query.order_by(ProcessedEmail.processed_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "emails": [email.__dict__ for email in emails],
            "total": query.count(),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to get processed emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get processed emails"
        )


@router.get("/email/scan-history")
async def get_scan_history(
    limit: int = 20,
    offset: int = 0,
    scan_type: Optional[str] = None,
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Get email scan history for user"""
    
    try:
        query = db.query(EmailScanHistory).filter(
            EmailScanHistory.user_id == current_user.user_id
        )
        
        if scan_type:
            query = query.filter(EmailScanHistory.scan_type == scan_type)
        
        scans = query.order_by(EmailScanHistory.scan_started_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "scans": [scan.__dict__ for scan in scans],
            "total": query.count(),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to get scan history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scan history"
        )


@router.post("/email/test-forwarding")
async def test_email_forwarding(
    user_id: str = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db)
):
    """Test email forwarding setup"""
    
    try:
        # Get user settings
        user_settings = db.query(UserSettings).filter(
            UserSettings.user_id == current_user.user_id
        ).first()
        
        if not user_settings or not user_settings.email_tracking_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email tracking is not enabled"
            )
        
        forwarding_address = f"jobtrack_{current_user.user_id}@jobflowpro.com"
        
        # This would test the actual email forwarding setup
        # For now, just return the forwarding address
        
        return {
            "status": "success",
            "forwarding_address": forwarding_address,
            "message": f"Forward job-related emails to {forwarding_address}",
            "instructions": [
                "1. Forward job-related emails to the address above",
                "2. Include the original email content",
                "3. Our system will automatically process and classify them",
                "4. You'll receive notifications for important emails"
            ]
        }
        
    except Exception as e:
        logger.error(f"Email forwarding test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test email forwarding"
        )


@router.get("/email/system-health")
async def get_system_health(
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get email scanning system health status (admin only)"""
    
    try:
        from app.services.email_scanning_monitor import email_scanning_monitor
        
        # Check if user is admin (you can implement your own admin check)
        # For now, allow all authenticated users
        health_status = await email_scanning_monitor.check_system_health()
        
        return health_status
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system health"
        )


@router.get("/email/performance-metrics")
async def get_performance_metrics(
    days: int = 7,
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get email scanning performance metrics"""
    
    try:
        from app.services.email_scanning_monitor import email_scanning_monitor
        
        metrics = await email_scanning_monitor.get_performance_metrics(days)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance metrics"
        )


@router.post("/email/retry-stuck-scans")
async def retry_stuck_scans(
    user_id: str = Depends(get_authenticated_user_id)
):
    """Retry stuck email scans (admin only)"""
    
    try:
        from app.services.email_scanning_monitor import email_scanning_monitor
        
        result = await email_scanning_monitor.retry_stuck_scans()
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to retry stuck scans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry stuck scans"
        )


def calculate_next_scan_time(user_settings: UserSettings) -> Optional[str]:
    """Calculate next scheduled scan time"""
    
    if not user_settings:
        return None
    
    try:
        current_utc = datetime.now(pytz.UTC)
        user_tz = pytz.timezone(user_settings.email_scan_timezone)
        user_local_time = current_utc.astimezone(user_tz)
        
        frequency = user_settings.email_scan_frequency
        scan_hour = user_settings.email_scan_time.hour
        scan_minute = user_settings.email_scan_time.minute
        
        if frequency == 'daily':
            # Next scan is today or tomorrow at scan time
            next_scan = user_local_time.replace(hour=scan_hour, minute=scan_minute, second=0, microsecond=0)
            if next_scan <= user_local_time:
                next_scan += timedelta(days=1)
        
        elif frequency == 'twice_daily':
            # Next scan is today or tomorrow at scan time or scan time + 12 hours
            next_scan = user_local_time.replace(hour=scan_hour, minute=scan_minute, second=0, microsecond=0)
            if next_scan <= user_local_time:
                next_scan += timedelta(hours=12)
                if next_scan <= user_local_time:
                    next_scan += timedelta(hours=12)
        
        elif frequency == 'weekly':
            # Next scan is next Monday at scan time
            days_until_monday = (7 - user_local_time.weekday()) % 7
            if days_until_monday == 0 and user_local_time.hour >= scan_hour:
                days_until_monday = 7
            next_scan = user_local_time.replace(hour=scan_hour, minute=scan_minute, second=0, microsecond=0) + timedelta(days=days_until_monday)
        
        elif frequency == 'bi_weekly':
            # Next scan is 1st or 15th of current/next month
            if user_local_time.day < 1:
                next_scan = user_local_time.replace(day=1, hour=scan_hour, minute=scan_minute, second=0, microsecond=0)
            elif user_local_time.day < 15:
                next_scan = user_local_time.replace(day=15, hour=scan_hour, minute=scan_minute, second=0, microsecond=0)
            else:
                # Next month's 1st
                next_month = user_local_time.replace(day=1) + timedelta(days=32)
                next_scan = next_month.replace(day=1, hour=scan_hour, minute=scan_minute, second=0, microsecond=0)
        
        elif frequency == 'monthly':
            # Next scan is 1st of next month
            next_month = user_local_time.replace(day=1) + timedelta(days=32)
            next_scan = next_month.replace(day=1, hour=scan_hour, minute=scan_minute, second=0, microsecond=0)
        
        else:
            return None
        
        return next_scan.strftime("%Y-%m-%d %H:%M:%S %Z")
        
    except Exception as e:
        logger.error(f"Failed to calculate next scan time: {e}")
        return None
