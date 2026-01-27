import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.email_models import UserGmailConnection, EmailEvent
from app.models.job import JobListing, JobApplication
from app.services.gmail_service import GmailService
from app.services.email_classifier import EmailClassifier
from app.services.job_matcher import JobMatcher
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailProcessor:
    """Enhanced email processor with AI classification and job status updates"""
    
    def __init__(self):
        self.gmail_service = GmailService()
        self.email_classifier = EmailClassifier()
        self.job_matcher = JobMatcher()
        self.debug = settings.DEBUG_EMAIL_PROCESSING
        
    async def process_user_emails(self, user_id: str, user_email: str = None, db: Session = None) -> Dict[str, Any]:
        """
        Process emails for a user with AI classification and job status updates
        """
        try:
            # Get user's Gmail connection
            connection = db.query(UserGmailConnection).filter(
                UserGmailConnection.user_id == user_id
            ).first()
            
            if not connection or not connection.is_authorized:
                return {
                    "success": False,
                    "message": "Gmail not connected or authorized",
                    "emails_processed": 0,
                    "status_updates": 0
                }
            
            # Check if token needs refresh
            if connection.is_token_expired:
                refresh_result = self.gmail_service.refresh_access_token(connection.refresh_token)
                if refresh_result['status'] != 'success':
                    return {
                        "success": False,
                        "message": "Failed to refresh Gmail token",
                        "emails_processed": 0,
                        "status_updates": 0
                    }
                
                # Update connection with new tokens
                connection.access_token = refresh_result['access_token']
                connection.token_expiry = refresh_result['token_expiry']
                db.commit()
            
            # Fetch recent emails
            emails = await self.gmail_service.fetch_job_emails(user_id, user_email, days_back=7)
            
            if not emails:
                return {
                    "success": True,
                    "message": "No new emails found",
                    "emails_processed": 0,
                    "status_updates": 0
                }
            
            # Process each email
            processed_count = 0
            status_updates = 0
            
            for email in emails:
                try:
                    result = await self._process_single_email(email, user_id, db)
                    if result['processed']:
                        processed_count += 1
                    if result['status_updated']:
                        status_updates += 1
                        
                except Exception as e:
                    logger.error(f"Error processing email {email.get('id')}: {e}")
                    continue
            
            # Update connection stats
            connection.last_sync_at = datetime.utcnow()
            connection.total_emails_processed += processed_count
            db.commit()
            
            return {
                "success": True,
                "message": f"Processed {processed_count} emails, updated {status_updates} job statuses",
                "emails_processed": processed_count,
                "status_updates": status_updates
            }
            
        except Exception as e:
            logger.error(f"Error processing emails for user {user_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to process emails: {str(e)}",
                "emails_processed": 0,
                "status_updates": 0
            }
    
    async def _process_single_email(self, email: Dict[str, Any], user_id: str, db: Session) -> Dict[str, Any]:
        """
        Process a single email with AI classification and job matching
        """
        try:
            # Check if email already processed
            existing_event = db.query(EmailEvent).filter(
                EmailEvent.email_message_id == email['id']
            ).first()
            
            if existing_event:
                logger.info(f"Email {email['id']} already processed")
                return {"processed": False, "status_updated": False}
            
            # Extract email content
            subject = email.get('subject', '')
            sender_email = email.get('sender_email', '')
            content = email.get('content', '')
            received_date = email.get('received_date', datetime.utcnow())
            
            # AI Classification
            classification = await self.email_classifier.classify_email(
                content, subject, sender_email
            )
            
            # Check if job-related
            if not self.email_classifier.is_job_related(
                classification['email_type'], 
                classification['confidence_score']
            ):
                logger.info(f"Email {email['id']} not job-related, skipping")
                return {"processed": False, "status_updated": False}
            
            # Create email event
            email_event = EmailEvent(
                user_id=user_id,
                gmail_connection_id=1,  # Assuming single connection per user
                email_message_id=email['id'],
                sender_email=sender_email,
                sender_name=email.get('sender_name', ''),
                subject=subject,
                email_received_at=received_date,
                email_type=classification['email_type'],
                confidence_score=classification['confidence_score'],
                company_name=classification['company_name'],
                ai_data=classification
            )
            
            db.add(email_event)
            db.flush()  # Get the ID
            
            # Job matching and status update
            status_updated = False
            if self.email_classifier.should_update_job_status(
                classification['email_type'], 
                classification['confidence_score']
            ):
                status_updated = await self._update_job_status(
                    email_event, classification, user_id, db
                )
            
            # Mark as processed
            email_event.processed_at = datetime.utcnow()
            email_event.status_updated = status_updated
            db.commit()
            
            logger.info(f"Processed email {email['id']}: {classification['email_type']} (confidence: {classification['confidence_score']:.2f})")
            
            return {
                "processed": True,
                "status_updated": status_updated,
                "email_type": classification['email_type'],
                "confidence": classification['confidence_score']
            }
            
        except Exception as e:
            logger.error(f"Error processing single email: {e}")
            db.rollback()
            return {"processed": False, "status_updated": False}
    
    async def _update_job_status(
        self, 
        email_event: EmailEvent, 
        classification: Dict[str, Any], 
        user_id: str, 
        db: Session
    ) -> bool:
        """
        Update job status based on email classification
        """
        try:
            # Find matching job
            match_result = self.job_matcher.find_matching_job(
                db=db,
                user_id=user_id,
                company_name=classification['company_name'],
                job_title=classification['job_title'],
                email_received_date=email_event.email_received_at
            )
            
            if not match_result:
                logger.info(f"No job match found for email {email_event.id}")
                return False
            
            job_id, confidence_score = match_result
            
            # Log match attempt
            self.job_matcher.log_match_attempt(
                db=db,
                user_id=user_id,
                email_event_id=email_event.id,
                matched_job_id=job_id,
                confidence_score=confidence_score,
                email_type=classification['email_type']
            )
            
            # Check if should auto-update
            if not self.job_matcher.should_auto_update_status(confidence_score):
                logger.info(f"Confidence {confidence_score:.2f} below threshold for auto-update")
                return False
            
            # Get new status
            new_status = self.job_matcher.get_status_update_mapping(classification['email_type'])
            if not new_status:
                logger.info(f"No status mapping for email type: {classification['email_type']}")
                return False
            
            # Update job application status
            job_application = db.query(JobApplication).filter(
                JobApplication.user_id == user_id,
                JobApplication.job_id == job_id
            ).first()
            
            if not job_application:
                logger.error(f"Job application not found for user {user_id} and job {job_id}")
                return False
            
            old_status = job_application.application_status
            job_application.application_status = new_status
            job_application.updated_at = datetime.utcnow()
            
            # Update email event with job match
            email_event.matched_job_id = job_id
            
            db.commit()
            
            logger.info(f"Updated job application {job_application.id} status: {old_status} → {new_status} (confidence: {confidence_score:.2f})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            db.rollback()
            return False
    
    async def process_specific_email(self, email_event_id: int, db: Session) -> Dict[str, Any]:
        """
        Process a specific email event (for manual processing)
        """
        try:
            email_event = db.query(EmailEvent).filter(EmailEvent.id == email_event_id).first()
            if not email_event:
                return {"success": False, "message": "Email event not found"}
            
            # Re-run classification if needed
            if not email_event.ai_data or 'email_type' not in email_event.ai_data:
                classification = await self.email_classifier.classify_email(
                    email_event.subject,  # Assuming content is in subject for now
                    email_event.subject,
                    email_event.sender_email
                )
                
                email_event.email_type = classification['email_type']
                email_event.confidence_score = classification['confidence_score']
                email_event.ai_data = classification
                db.commit()
            
            # Try job matching and status update
            status_updated = await self._update_job_status(
                email_event, 
                email_event.ai_data, 
                email_event.user_id, 
                db
            )
            
            return {
                "success": True,
                "status_updated": status_updated,
                "email_type": email_event.email_type,
                "confidence": email_event.confidence_score
            }
            
        except Exception as e:
            logger.error(f"Error processing specific email: {e}")
            return {"success": False, "message": str(e)} 