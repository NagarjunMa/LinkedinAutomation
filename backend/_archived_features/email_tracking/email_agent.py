from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from pydantic import BaseModel
from starlette.responses import RedirectResponse
import logging
from datetime import datetime

from app.db.session import get_db
from app.models.email_models import UserGmailConnection, EmailEvent
from app.models.job import JobListing, JobApplication
from app.services.gmail_service import GmailService
from app.services.email_processor import EmailProcessor

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models for request validation
class ConnectGmailRequest(BaseModel):
    user_id: str
    user_email: Optional[str] = None

class ProcessEmailsRequest(BaseModel):
    user_email: Optional[str] = None

@router.get("/config/status")
async def get_email_config_status():
    """Check if email configuration is properly set up"""
    try:
        from app.utils.email_helpers import validate_email_config
        config_status = validate_email_config()
        return config_status
    except Exception as e:
        return {
            "configured": False,
            "error": str(e)
        }

@router.post("/connect")
async def connect_gmail(
    request: ConnectGmailRequest,
    db: Session = Depends(get_db)
):
    """
    Start Google OAuth flow for Gmail connection
    """
    try:
        gmail_service = GmailService()
        
        # Check if user already has a connection
        connection = db.query(UserGmailConnection).filter(
            UserGmailConnection.user_id == request.user_id
        ).first()
        
        if connection and connection.is_authorized and not connection.is_token_expired:
            return {
                "status": "connected",
                "message": "Gmail already connected",
                "gmail_email": connection.gmail_email
            }
        
        # Get authorization URL
        auth_result = gmail_service.get_authorization_url(request.user_id)
        
        if auth_result['status'] == 'auth_required':
            return {
                "status": "auth_required",
                "auth_url": auth_result['auth_url'],
                "state": auth_result['state'],
                "message": auth_result['message']
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=auth_result['message']
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start Gmail connection: {str(e)}"
        )

@router.get("/oauth/callback")
async def oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback
    """
    try:
        gmail_service = GmailService()
        
        # Exchange code for tokens
        token_result = gmail_service.exchange_code_for_tokens(code, state)
        
        if token_result['status'] != 'success':
            # Redirect to frontend with error
            error_message = token_result['message'].replace(' ', '%20')
            return RedirectResponse(
                url=f"http://localhost:3000/email-agent?error={error_message}",
                status_code=302
            )
        
        # Get or create connection
        connection = db.query(UserGmailConnection).filter(
            UserGmailConnection.user_id == state
        ).first()
        
        if not connection:
            connection = UserGmailConnection(
                user_id=state,
                google_user_id=token_result['google_user_id'],
                gmail_email=token_result['gmail_email'],
                access_token=token_result['access_token'],
                refresh_token=token_result['refresh_token'],
                token_expiry=token_result['token_expiry'],
                is_authorized=True
            )
            db.add(connection)
        else:
            connection.google_user_id = token_result['google_user_id']
            connection.gmail_email = token_result['gmail_email']
            connection.access_token = token_result['access_token']
            connection.refresh_token = token_result['refresh_token']
            connection.token_expiry = token_result['token_expiry']
            connection.is_authorized = True
        
        db.commit()
        
        # Redirect to frontend with success
        gmail_email = token_result['gmail_email'].replace('@', '%40')
        return RedirectResponse(
            url=f"http://localhost:3000/email-agent?success=true&gmail_email={gmail_email}",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        error_message = str(e).replace(' ', '%20')
        return RedirectResponse(
            url=f"http://localhost:3000/email-agent?error={error_message}",
            status_code=302
        )

@router.get("/status/{user_id}")
async def get_gmail_status(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get Gmail connection status for user"""
    try:
        connection = db.query(UserGmailConnection).filter(
            UserGmailConnection.user_id == user_id
        ).first()
        
        if not connection:
            return {
                "connected": False,
                "message": "No Gmail connection found"
            }
        
        # Check if token is expired
        if connection.is_token_expired and connection.refresh_token:
            gmail_service = GmailService()
            refresh_result = gmail_service.refresh_access_token(connection.refresh_token)
            
            if refresh_result['status'] == 'success':
                connection.access_token = refresh_result['access_token']
                connection.token_expiry = refresh_result['token_expiry']
                db.commit()
            else:
                connection.is_authorized = False
                db.commit()
        
        # Get recent email events
        recent_events = db.query(EmailEvent).filter(
            EmailEvent.user_id == user_id
        ).order_by(EmailEvent.created_at.desc()).limit(5).all()
        
        return {
            "connected": connection.is_authorized,
            "gmail_email": connection.gmail_email,
            "last_sync": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
            "total_emails_processed": connection.total_emails_processed,
            "recent_events": [
                {
                    "id": event.id,
                    "sender_email": event.sender_email,
                    "subject": event.subject,
                    "email_type": event.email_type,
                    "confidence_score": event.confidence_score,
                    "created_at": event.created_at.isoformat()
                }
                for event in recent_events
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Gmail status: {str(e)}"
        )

@router.get("/summary/{user_id}")
async def get_email_summary(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get email processing summary for user"""
    try:
        # Get connection status
        connection = db.query(UserGmailConnection).filter(
            UserGmailConnection.user_id == user_id
        ).first()
        
        if not connection:
            return {
                "connected": False,
                "message": "No Gmail connection found"
            }
        
        # Get email statistics
        total_events = db.query(EmailEvent).filter(
            EmailEvent.user_id == user_id
        ).count()
        
        recent_events = db.query(EmailEvent).filter(
            EmailEvent.user_id == user_id
        ).order_by(EmailEvent.created_at.desc()).limit(10).count()
        
        needs_review = db.query(EmailEvent).filter(
            EmailEvent.user_id == user_id,
            EmailEvent.confidence_score < 0.8,
            EmailEvent.user_reviewed == False
        ).count()
        
        # Get events by type
        events_by_type = db.query(
            EmailEvent.email_type,
            func.count(EmailEvent.id).label('count')
        ).filter(
            EmailEvent.user_id == user_id
        ).group_by(EmailEvent.email_type).all()
        
        by_type = {event.email_type: event.count for event in events_by_type}
        
        return {
            "connected": connection.is_authorized,
            "last_sync": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
            "total_processed": total_events,
            "recent_count": recent_events,
            "needs_review": needs_review,
            "by_type": by_type
        }
        
    except Exception as e:
        logger.error(f"Error in get_email_summary for user {user_id}: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email summary: {str(e)}"
        )

@router.get("/events/{user_id}")
async def get_email_events(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    email_type: str = None,
    db: Session = Depends(get_db)
):
    """Get email events for user"""
    try:
        query = db.query(EmailEvent).filter(EmailEvent.user_id == user_id)
        
        if email_type and email_type != 'all':
            query = query.filter(EmailEvent.email_type == email_type)
        
        events = query.order_by(EmailEvent.created_at.desc()).offset(offset).limit(limit).all()
        
        return [
            {
                "id": event.id,
                "sender_email": event.sender_email,
                "sender_name": event.sender_name,
                "subject": event.subject,
                "email_type": event.email_type,
                "confidence_score": event.confidence_score,
                "company_name": event.company_name,
                "email_received_at": event.email_received_at.isoformat() if event.email_received_at else None,
                "created_at": event.created_at.isoformat(),
                "needs_review": event.needs_review,
                "status_updated": event.status_updated,
                "matched_job_id": event.matched_job_listing_id,
                "ai_data": event.ai_data
            }
            for event in events
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email events: {str(e)}"
        )

@router.post("/events/{event_id}/review")
async def mark_event_reviewed(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Mark email event as reviewed by user"""
    try:
        event = db.query(EmailEvent).filter(EmailEvent.id == event_id).first()
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email event not found"
            )
        
        event.user_reviewed = True
        db.commit()
        
        return {"success": True, "message": "Event marked as reviewed"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark event as reviewed: {str(e)}"
        )

@router.post("/process/{user_id}")
async def process_emails(
    user_id: str,
    request: ProcessEmailsRequest,
    db: Session = Depends(get_db)
):
    """Process emails for user with AI classification and job status updates"""
    try:
        processor = EmailProcessor()
        result = await processor.process_user_emails(user_id, request.user_email, db)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process emails: {str(e)}"
        )

@router.post("/process-email/{email_event_id}")
async def process_specific_email(
    email_event_id: int,
    db: Session = Depends(get_db)
):
    """Process a specific email event with AI classification and job matching"""
    try:
        processor = EmailProcessor()
        result = await processor.process_specific_email(email_event_id, db)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process email: {str(e)}"
        )

@router.get("/analytics/{user_id}")
async def get_email_analytics(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed email analytics and job status updates"""
    try:
        # Get connection status
        connection = db.query(UserGmailConnection).filter(
            UserGmailConnection.user_id == user_id
        ).first()
        
        if not connection:
            return {
                "connected": False,
                "message": "No Gmail connection found"
            }
        
        # Get email events with job matches
        email_events = db.query(EmailEvent).filter(
            EmailEvent.user_id == user_id
        ).order_by(EmailEvent.created_at.desc()).limit(100).all()
        
        # Get job status updates
        status_updates = []
        for event in email_events:
            if event.status_updated and event.matched_job_id:
                job_application = db.query(JobApplication).filter(
                    JobApplication.user_id == user_id,
                    JobApplication.job_id == event.matched_job_id
                ).first()
                
                if job_application:
                    job = db.query(JobListing).filter(JobListing.id == event.matched_job_id).first()
                    if job:
                        status_updates.append({
                            "email_event_id": event.id,
                            "job_id": event.matched_job_id,
                            "job_title": job.title,
                            "company": job.company,
                            "old_status": "unknown",  # Could be enhanced to track status history
                            "new_status": job_application.application_status,
                            "email_type": event.email_type,
                            "confidence_score": event.confidence_score,
                            "updated_at": event.processed_at.isoformat() if event.processed_at else None
                        })
        
        # Calculate analytics
        total_emails = len(email_events)
        job_related_emails = len([e for e in email_events if e.email_type != 'not_job_related'])
        status_updates_count = len(status_updates)
        
        # Email type distribution
        email_types = {}
        for event in email_events:
            email_type = event.email_type
            email_types[email_type] = email_types.get(email_type, 0) + 1
        
        # Confidence score distribution
        high_confidence = len([e for e in email_events if e.confidence_score >= 0.8])
        medium_confidence = len([e for e in email_events if 0.6 <= e.confidence_score < 0.8])
        low_confidence = len([e for e in email_events if e.confidence_score < 0.6])
        
        return {
            "connected": connection.is_authorized,
            "last_sync": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
            "total_emails_processed": total_emails,
            "job_related_emails": job_related_emails,
            "status_updates_count": status_updates_count,
            "email_type_distribution": email_types,
            "confidence_distribution": {
                "high": high_confidence,
                "medium": medium_confidence,
                "low": low_confidence
            },
            "recent_status_updates": status_updates[:10],  # Last 10 updates
            "processing_stats": {
                "success_rate": (job_related_emails / total_emails * 100) if total_emails > 0 else 0,
                "auto_update_rate": (status_updates_count / job_related_emails * 100) if job_related_emails > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting email analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email analytics: {str(e)}"
        )

@router.get("/test-classification")
async def test_email_classification(
    subject: str,
    content: str,
    sender_email: str = "test@example.com"
):
    """Test email classification with sample content"""
    try:
        from app.services.email_classifier import EmailClassifier
        
        classifier = EmailClassifier()
        result = await classifier.classify_email(content, subject, sender_email)
        
        return {
            "classification": result,
            "is_job_related": classifier.is_job_related(
                result['email_type'], 
                result['confidence_score']
            ),
            "should_update_status": classifier.should_update_job_status(
                result['email_type'], 
                result['confidence_score']
            )
        }
        
    except Exception as e:
        logger.error(f"Error testing classification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test classification: {str(e)}"
        )

@router.get("/test-job-matching/{user_id}")
async def test_job_matching(
    user_id: str,
    company_name: str,
    job_title: str = None,
    db: Session = Depends(get_db)
):
    """Test job matching with sample company and job title"""
    try:
        from app.services.job_matcher import JobMatcher
        
        matcher = JobMatcher()
        result = matcher.find_matching_job(
            db=db,
            user_id=user_id,
            company_name=company_name,
            job_title=job_title
        )
        
        if result:
            job_id, confidence_score = result
            job = db.query(JobListing).filter(JobListing.id == job_id).first()
            
            return {
                "matched": True,
                "job_id": job_id,
                "confidence_score": confidence_score,
                "job_details": {
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "status": job.status
                },
                "should_auto_update": matcher.should_auto_update_status(confidence_score)
            }
        else:
            return {
                "matched": False,
                "message": "No matching job found"
            }
        
    except Exception as e:
        logger.error(f"Error testing job matching: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test job matching: {str(e)}"
        )

@router.delete("/disconnect/{user_id}")
async def disconnect_gmail(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Disconnect Gmail account"""
    try:
        connection = db.query(UserGmailConnection).filter(
            UserGmailConnection.user_id == user_id
        ).first()
        
        if connection:
            # Clear tokens and mark as unauthorized
            connection.access_token = None
            connection.refresh_token = None
            connection.token_expiry = None
            connection.is_authorized = False
            db.commit()
        
        return {"status": "success", "message": "Gmail disconnected"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect Gmail: {str(e)}"
        ) 

@router.post("/trigger-processing/{user_id}")
async def trigger_email_processing(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Manually trigger email processing for a user"""
    try:
        from app.tasks.email_monitoring_tasks import process_user_emails_async
        
        # Trigger async processing
        task = process_user_emails_async.delay(user_id)
        
        return {
            "success": True,
            "message": "Email processing triggered",
            "task_id": task.id,
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"Error triggering email processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger email processing: {str(e)}"
        )

@router.get("/monitoring-status")
async def get_monitoring_status():
    """Get the status of email monitoring tasks"""
    try:
        from app.core.celery_app import celery_app
        
        # Get active tasks
        inspector = celery_app.control.inspect()
        active_tasks = inspector.active()
        scheduled_tasks = inspector.scheduled()
        
        # Get task statistics
        stats = inspector.stats()
        
        return {
            "monitoring_active": True,
            "active_tasks": active_tasks or {},
            "scheduled_tasks": scheduled_tasks or {},
            "worker_stats": stats or {},
            "last_check": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        return {
            "monitoring_active": False,
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }

@router.post("/test-glean-email")
async def test_glean_email_processing():
    """Test processing with the Glean email example"""
    try:
        from app.services.email_classifier import EmailClassifier
        
        classifier = EmailClassifier()
        
        # Test with the Glean email
        glean_email = {
            "subject": "Thank you for applying to Glean",
            "content": """Hi nagarjun,
 
Thank you for your interest in Glean! We wanted to let you know we received your application for Software Engineer, Backend, and we are delighted that you would consider joining our team.
 
Our team will review your application and will be in touch if your qualifications match our needs for the role. If you are not selected for this position, keep an eye on our jobs page as we're growing and adding openings.
 
Best,
The Glean Team""",
            "sender": "no-reply@us.greenhouse-mail.io"
        }
        
        # Classify the email
        classification = await classifier.classify_email(
            glean_email["content"],
            glean_email["subject"],
            glean_email["sender"]
        )
        
        return {
            "email": glean_email,
            "classification": classification,
            "is_job_related": classifier.is_job_related(
                classification['email_type'], 
                classification['confidence_score']
            ),
            "should_update_status": classifier.should_update_job_status(
                classification['email_type'], 
                classification['confidence_score']
            ),
            "expected_status": "applied" if classification['email_type'] == 'application_confirmation' else None
        }
        
    except Exception as e:
        logger.error(f"Error testing Glean email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test Glean email: {str(e)}"
        ) 