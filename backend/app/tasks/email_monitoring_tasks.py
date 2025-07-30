import logging
import asyncio
from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.db.session import SessionLocal
from app.models.email_models import UserGmailConnection, EmailEvent
from app.services.email_processor import EmailProcessor
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task
def monitor_and_process_emails():
    """
    Background task to monitor Gmail accounts and process new emails automatically
    Runs every 5 minutes to check for new emails
    """
    logger.info("Starting email monitoring task")
    
    db = SessionLocal()
    try:
        # Get all authorized Gmail connections
        connections = db.query(UserGmailConnection).filter(
            UserGmailConnection.is_authorized == True
        ).all()
        
        logger.info(f"Found {len(connections)} authorized Gmail connections")
        
        total_processed = 0
        total_updates = 0
        
        for connection in connections:
            try:
                # Process emails for this user using asyncio
                processor = EmailProcessor()
                result = asyncio.run(processor.process_user_emails(
                    user_id=connection.user_id,
                    user_email=connection.gmail_email,
                    db=db
                ))
                
                if result.get('success'):
                    processed = result.get('emails_processed', 0)
                    updates = result.get('status_updates', 0)
                    total_processed += processed
                    total_updates += updates
                    
                    if processed > 0:
                        logger.info(f"User {connection.user_id}: Processed {processed} emails, {updates} status updates")
                else:
                    logger.warning(f"User {connection.user_id}: {result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error processing emails for user {connection.user_id}: {e}")
                continue
        
        logger.info(f"Email monitoring completed: {total_processed} emails processed, {total_updates} status updates")
        return {
            'success': True,
            'total_processed': total_processed,
            'total_updates': total_updates,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Email monitoring task failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        db.close()

@celery_app.task
def process_user_emails_async(user_id: str):
    """
    Process emails for a specific user asynchronously
    Can be triggered manually or by webhook
    """
    logger.info(f"Processing emails for user {user_id}")
    
    db = SessionLocal()
    try:
        processor = EmailProcessor()
        result = asyncio.run(processor.process_user_emails(user_id=user_id, db=db))
        
        logger.info(f"User {user_id} processing result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing emails for user {user_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()

@celery_app.task
def check_gmail_connections():
    """
    Check Gmail connection health and refresh tokens if needed
    Runs every hour
    """
    logger.info("Checking Gmail connection health")
    
    db = SessionLocal()
    try:
        connections = db.query(UserGmailConnection).filter(
            UserGmailConnection.is_authorized == True
        ).all()
        
        refreshed_count = 0
        failed_count = 0
        
        for connection in connections:
            try:
                # Check if token is expired
                if connection.is_token_expired and connection.refresh_token:
                    from app.services.gmail_service import GmailService
                    gmail_service = GmailService()
                    
                    refresh_result = gmail_service.refresh_access_token(connection.refresh_token)
                    
                    if refresh_result['status'] == 'success':
                        connection.access_token = refresh_result['access_token']
                        connection.token_expiry = refresh_result['token_expiry']
                        refreshed_count += 1
                        logger.info(f"Refreshed token for user {connection.user_id}")
                    else:
                        connection.is_authorized = False
                        failed_count += 1
                        logger.warning(f"Failed to refresh token for user {connection.user_id}")
                
            except Exception as e:
                logger.error(f"Error checking connection for user {connection.user_id}: {e}")
                failed_count += 1
                continue
        
        db.commit()
        
        logger.info(f"Gmail connection check completed: {refreshed_count} refreshed, {failed_count} failed")
        return {
            'success': True,
            'refreshed_count': refreshed_count,
            'failed_count': failed_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Gmail connection check failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        db.close()

# Schedule the tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic tasks for email monitoring"""
    
    # Monitor emails every 5 minutes
    sender.add_periodic_task(
        300.0,  # 5 minutes
        monitor_and_process_emails.s(),
        name='monitor-emails-every-5-minutes'
    )
    
    # Check Gmail connections every hour
    sender.add_periodic_task(
        3600.0,  # 1 hour
        check_gmail_connections.s(),
        name='check-gmail-connections-every-hour'
    )
    
    logger.info("Periodic tasks configured for email monitoring") 