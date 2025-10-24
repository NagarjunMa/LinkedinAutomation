"""
Email scanning tasks for automated job email processing
"""
from celery import shared_task
from datetime import datetime, timedelta
import pytz
import logging
import json
import uuid
from typing import Dict, List, Optional

from app.db.session import get_db
from app.models.email_scanning import EmailScanHistory, ProcessedEmail
from app.models.job import JobListing
from app.models.profile import UserSettings
from app.core.ai_service import get_ai_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=3)
def check_urgent_emails(self):
    """Check for urgent emails every 2 hours - CRITICAL TASK"""
    
    logger.info("Starting urgent email check")
    
    try:
        db = next(get_db())
        
        # Get all users with email tracking enabled
        users = db.query(UserSettings).filter(
            UserSettings.email_tracking_enabled == True
        ).all()
        
        total_urgent = 0
        
        for user_settings in users:
            try:
                # Scan only for urgent email types
                urgent_emails = scan_forwarded_emails(
                    user_settings.user_id,
                    scan_type='urgent',
                    email_types=['interview_invitation', 'offer', 'urgent_request']
                )
                
                for email in urgent_emails:
                    process_urgent_email(user_settings.user_id, email)
                    total_urgent += 1
                
                # Update timestamp
                user_settings.last_urgent_scan = datetime.now(pytz.UTC)
                db.commit()
                
            except Exception as e:
                logger.error(f"Urgent scan failed for user {user_settings.user_id}: {e}")
                continue
        
        db.close()
        logger.info(f"Urgent email check completed. Found {total_urgent} urgent emails")
        
    except Exception as e:
        logger.error(f"Urgent email check task failed: {e}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes


@shared_task
def process_scheduled_scans():
    """Check which users need full email scans and process them"""
    
    current_utc = datetime.now(pytz.UTC)
    
    try:
        db = next(get_db())
        
        # Get all users with email tracking enabled
        users = db.query(UserSettings).filter(
            UserSettings.email_tracking_enabled == True
        ).all()
        
        for user_settings in users:
            try:
                if should_scan_user_now(user_settings, current_utc):
                    run_full_email_scan.delay(user_settings.user_id)
            except Exception as e:
                logger.error(f"Schedule check failed for user {user_settings.user_id}: {e}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Scheduled scan processing failed: {e}")


def should_scan_user_now(user_settings: UserSettings, current_utc: datetime) -> bool:
    """Determine if this user should be scanned now"""
    
    # Convert current time to user's timezone
    user_tz = pytz.timezone(user_settings.email_scan_timezone)
    user_local_time = current_utc.astimezone(user_tz)
    
    # Check if current hour matches user's preferred scan time
    scan_hour = user_settings.email_scan_time.hour
    current_hour = user_local_time.hour
    
    if current_hour != scan_hour:
        return False
    
    # Check frequency constraints
    frequency = user_settings.email_scan_frequency
    last_scan = user_settings.last_full_scan
    
    if frequency == 'daily':
        return True
    
    elif frequency == 'twice_daily':
        # Scan at user's time AND 12 hours later
        return current_hour in [scan_hour, (scan_hour + 12) % 24]
    
    elif frequency == 'weekly':
        # Only on Mondays
        return user_local_time.weekday() == 0
    
    elif frequency == 'bi_weekly':
        # 1st and 15th of month
        return user_local_time.day in [1, 15]
    
    elif frequency == 'monthly':
        # 1st of month only
        return user_local_time.day == 1
    
    return False


@shared_task(bind=True, max_retries=2)
def run_full_email_scan(self, user_id: str):
    """Execute complete email scan for a user"""
    
    scan_id = str(uuid.uuid4())
    logger.info(f"Starting full email scan {scan_id} for user {user_id}")
    
    try:
        db = next(get_db())
        
        # Create scan history record
        scan_history = EmailScanHistory(
            id=scan_id,
            user_id=user_id,
            scan_type='full',
            scan_started_at=datetime.now(pytz.UTC)
        )
        db.add(scan_history)
        db.commit()
        
        # Get user's forwarded emails
        emails = fetch_forwarded_emails_since_last_scan(user_id)
        
        results = {
            'processed': 0,
            'status_updates': 0,
            'urgent_found': 0,
            'errors': []
        }
        
        for email in emails:
            try:
                # Classify email
                email_type = classify_email_type(email)
                
                # Parse content
                parsed = parse_email_content(email, email_type)
                
                # Update application status
                updated = update_application_from_email(user_id, parsed, email_type)
                if updated:
                    results['status_updates'] += 1
                
                # Store email
                store_processed_email(user_id, email, email_type, parsed)
                
                results['processed'] += 1
                
                # Count urgent emails
                if email_type in ['interview_invitation', 'offer']:
                    results['urgent_found'] += 1
                    send_notification(user_id, email, email_type)
                
            except Exception as e:
                logger.error(f"Error processing email for user {user_id}: {e}")
                results['errors'].append(str(e))
                continue
        
        # Update scan history
        scan_history.emails_processed = results['processed']
        scan_history.status_updates_made = results['status_updates']
        scan_history.urgent_emails_found = results['urgent_found']
        scan_history.scan_completed_at = datetime.now(pytz.UTC)
        scan_history.errors = json.dumps(results['errors']) if results['errors'] else None
        
        # Update user settings
        user_settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()
        if user_settings:
            user_settings.last_full_scan = datetime.now(pytz.UTC)
        
        db.commit()
        db.close()
        
        logger.info(f"Scan {scan_id} completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Full scan {scan_id} failed: {e}")
        raise self.retry(exc=e, countdown=600)  # Retry after 10 minutes


def scan_forwarded_emails(user_id: str, scan_type: str = 'full', email_types: List[str] = None) -> List[Dict]:
    """Fetch forwarded emails for a user"""
    
    # This is a placeholder implementation
    # In production, this would integrate with your email service provider
    # (Resend, Mailgun, etc.) to fetch emails sent to jobtrack_{user_id}@jobflowpro.com
    
    forwarding_address = f"jobtrack_{user_id}@jobflowpro.com"
    
    # Production implementation - no emails returned until actual integration is implemented
    # TODO: Implement actual email service provider integration
    return []


def fetch_forwarded_emails_since_last_scan(user_id: str) -> List[Dict]:
    """Fetch emails received since last scan"""
    
    db = next(get_db())
    
    # Get last scan time
    user_settings = db.query(UserSettings).filter(
        UserSettings.user_id == user_id
    ).first()
    
    since_time = user_settings.last_full_scan if user_settings else (datetime.now(pytz.UTC) - timedelta(days=1))
    
    # Fetch from email service
    forwarding_address = f"jobtrack_{user_id}@jobflowpro.com"
    
    # Mock implementation - replace with actual email fetching
    emails = scan_forwarded_emails(user_id, 'full')
    
    # Filter by time
    filtered_emails = [
        email for email in emails 
        if email['received_at'] > since_time
    ]
    
    db.close()
    return filtered_emails


def classify_email_type(email: Dict) -> str:
    """AI classifies job-related email type"""
    
    ai_service = get_ai_service()
    
    prompt = f"""
    Classify this job-related email into one category:
    
    Subject: {email['subject']}
    From: {email['from']}
    Body Preview: {email['body'][:500]}
    
    Categories:
    1. application_confirmation - "We received your application"
    2. interview_invitation - Scheduling phone screen or interview
    3. interview_reminder - Upcoming interview confirmation
    4. rejection - Application not moving forward
    5. offer - Job offer extended
    6. request_info - Requesting additional materials
    7. general - Other job-related communication
    
    Return only the category name, nothing else.
    """
    
    try:
        response = ai_service.generate_response(prompt)
        return response.strip().lower()
    except Exception as e:
        logger.error(f"Email classification failed: {e}")
        return 'general'


def parse_email_content(email: Dict, email_type: str) -> Dict:
    """Extract relevant information from email"""
    
    ai_service = get_ai_service()
    
    prompt = f"""
    Extract key information from this {email_type} email:
    
    Subject: {email['subject']}
    Body: {email['body']}
    
    Extract:
    - Company name
    - Job title/role (if mentioned)
    - Interview date/time (if scheduling)
    - Action required from candidate
    - Deadline (if any)
    
    Return JSON with extracted fields.
    """
    
    try:
        response = ai_service.generate_response(prompt)
        # Parse JSON response
        import json
        return json.loads(response)
    except Exception as e:
        logger.error(f"Email parsing failed: {e}")
        return {}


def update_application_from_email(user_id: str, parsed_data: Dict, email_type: str) -> bool:
    """Update job application status based on email"""
    
    db = next(get_db())
    
    try:
        # Find matching job application
        job = find_job_by_company_and_title(
            user_id,
            parsed_data.get('company', ''),
            parsed_data.get('job_title', '')
        )
        
        if not job:
            return False
        
        # Update status based on email type
        status_mapping = {
            'application_confirmation': 'application_received',
            'interview_invitation': 'interview_scheduled',
            'rejection': 'rejected',
            'offer': 'offer_received',
            'request_info': 'awaiting_info'
        }
        
        new_status = status_mapping.get(email_type)
        
        if new_status:
            job.application_status = new_status
            job.applied_date = datetime.now(pytz.UTC)
            db.commit()
            
            # Create notification for user
            create_notification(user_id, job.id, email_type, parsed_data)
            
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Application update failed: {e}")
        return False
    finally:
        db.close()


def find_job_by_company_and_title(user_id: str, company: str, job_title: str) -> Optional[JobListing]:
    """Find job application by company and title"""
    
    db = next(get_db())
    
    try:
        # Try exact match first
        job = db.query(JobListing).filter(
            JobListing.user_id == user_id,
            JobListing.company.ilike(f"%{company}%"),
            JobListing.title.ilike(f"%{job_title}%") if job_title else True
        ).first()
        
        if not job and company:
            # Try company match only
            job = db.query(JobListing).filter(
                JobListing.user_id == user_id,
                JobListing.company.ilike(f"%{company}%")
            ).first()
        
        return job
        
    except Exception as e:
        logger.error(f"Job lookup failed: {e}")
        return None
    finally:
        db.close()


def store_processed_email(user_id: str, email: Dict, email_type: str, parsed_data: Dict):
    """Store processed email in database"""
    
    db = next(get_db())
    
    try:
        processed_email = ProcessedEmail(
            user_id=user_id,
            email_from=email['from'],
            email_subject=email['subject'],
            email_body=email['body'],
            email_type=email_type,
            received_at=email['received_at'],
            parsed_data=parsed_data
        )
        
        db.add(processed_email)
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to store processed email: {e}")
    finally:
        db.close()


def process_urgent_email(user_id: str, email: Dict):
    """Handle time-sensitive emails immediately"""
    
    try:
        # Classify and parse email
        email_type = classify_email_type(email)
        parsed = parse_email_content(email, email_type)
        
        # Update application status
        update_application_from_email(user_id, parsed, email_type)
        
        # Store email
        store_processed_email(user_id, email, email_type, parsed)
        
        # Send notifications
        send_notification(user_id, email, email_type)
        
    except Exception as e:
        logger.error(f"Urgent email processing failed: {e}")


def send_notification(user_id: str, email: Dict, email_type: str):
    """Send notification to user about important email"""
    
    # This would integrate with your notification system
    # (push notifications, email alerts, etc.)
    
    notification_data = {
        'user_id': user_id,
        'type': email_type,
        'title': f"New {email_type.replace('_', ' ').title()}",
        'message': f"Email from {email['from']}: {email['subject']}",
        'priority': 'high' if email_type in ['interview_invitation', 'offer'] else 'normal'
    }
    
    logger.info(f"Notification sent: {notification_data}")


def create_notification(user_id: str, job_id: int, email_type: str, parsed_data: Dict):
    """Create notification for user"""
    
    # This would create a notification record in your notification system
    logger.info(f"Created notification for user {user_id}, job {job_id}, type {email_type}")


@shared_task
def monitor_email_scanning_health():
    """Check if email scanning is working properly"""
    
    try:
        from app.services.email_scanning_monitor import email_scanning_monitor
        
        # Run comprehensive health check
        health_status = email_scanning_monitor.check_system_health()
        
        # Log health status
        if health_status['overall_status'] == 'critical':
            logger.critical(f"Email scanning system critical: {health_status}")
        elif health_status['overall_status'] == 'warning':
            logger.warning(f"Email scanning system warning: {health_status}")
        else:
            logger.info(f"Email scanning system healthy: {health_status}")
        
        # Retry stuck scans if any
        if health_status['checks'].get('stuck_scans', {}).get('status') == 'critical':
            retry_result = email_scanning_monitor.retry_stuck_scans()
            logger.info(f"Retry stuck scans result: {retry_result}")
        
    except Exception as e:
        logger.error(f"Health monitoring failed: {e}")
