#!/usr/bin/env python3
"""
Email Agent Demo Script
Demonstrates the email agent functionality with mock data
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.email_classifier import EmailClassifier
from app.db.session import SessionLocal
from app.models.email_models import UserGmailConnection, EmailEvent, EmailSyncLog
from datetime import datetime

async def demo_email_classification():
    """Demo email classification with sample emails"""
    print("🎯 Email Classification Demo")
    print("=" * 50)
    
    classifier = EmailClassifier()
    
    # Sample job application emails
    sample_emails = [
        {
            'sender': 'careers@google.com',
            'subject': 'Thank you for your application - Software Engineer',
            'content': 'Dear John, Thank you for your interest in the Software Engineer position at Google. We have received your application and our team will review it carefully. We will get back to you within 2-3 weeks with next steps.'
        },
        {
            'sender': 'recruiting@microsoft.com',
            'subject': 'Interview Invitation - Microsoft',
            'content': 'Hello! We are pleased to invite you for a technical interview for the Senior Software Engineer position. Please let us know your availability for next week. The interview will include coding challenges and system design discussions.'
        },
        {
            'sender': 'hr@startup.com',
            'subject': 'Application Update',
            'content': 'Unfortunately, after careful consideration, we have decided to move forward with other candidates for this position. We appreciate your interest in our company and wish you the best in your job search.'
        },
        {
            'sender': 'talent@amazon.com',
            'subject': 'Congratulations - Job Offer',
            'content': 'We are excited to extend you an offer for the Software Engineer position at Amazon! Please review the attached offer letter and let us know if you have any questions. We look forward to having you join our team.'
        },
        {
            'sender': 'noreply@linkedin.com',
            'subject': 'Application Submitted Successfully',
            'content': 'Your application for the Data Scientist position has been submitted successfully. You will receive a confirmation email shortly. Thank you for using LinkedIn Jobs.'
        }
    ]
    
    print(f"Classifying {len(sample_emails)} sample emails...\n")
    
    for i, email in enumerate(sample_emails, 1):
        print(f"📧 Email {i}: {email['subject']}")
        print(f"   From: {email['sender']}")
        
        try:
            result = await classifier.classify_email(
                email['sender'],
                email['subject'],
                email['content']
            )
            
            print(f"   Type: {result.email_type}")
            print(f"   Confidence: {result.confidence:.1%}")
            print(f"   Company: {result.company_name}")
            print(f"   Action: {result.suggested_action}")
            
        except Exception as e:
            print(f"   Error: {str(e)}")
        
        print()

def demo_database_operations():
    """Demo database operations with mock data"""
    print("🗄️ Database Operations Demo")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        
        # Create a test Gmail connection
        connection = UserGmailConnection(
            user_id="demo_user",
            arcade_user_id="demo_arcade_123",
            gmail_email="demo@example.com",
            is_authorized=True,
            last_sync_at=datetime.utcnow(),
            total_emails_processed=5
        )
        
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        print(f"✅ Created Gmail connection for user: {connection.user_id}")
        
        # Create sample email events
        sample_events = [
            {
                'sender_email': 'careers@google.com',
                'subject': 'Application Received',
                'email_type': 'confirmation',
                'confidence_score': 0.95,
                'company_name': 'Google'
            },
            {
                'sender_email': 'recruiting@microsoft.com',
                'subject': 'Interview Scheduled',
                'email_type': 'interview',
                'confidence_score': 0.92,
                'company_name': 'Microsoft'
            },
            {
                'sender_email': 'hr@startup.com',
                'subject': 'Application Status',
                'email_type': 'rejection',
                'confidence_score': 0.88,
                'company_name': 'Startup Inc'
            }
        ]
        
        for event_data in sample_events:
            event = EmailEvent(
                user_id="demo_user",
                gmail_connection_id=connection.id,
                email_message_id=f"demo_msg_{event_data['sender_email']}",
                sender_email=event_data['sender_email'],
                subject=event_data['subject'],
                email_received_at=datetime.utcnow(),
                email_type=event_data['email_type'],
                confidence_score=event_data['confidence_score'],
                company_name=event_data['company_name'],
                ai_data={
                    'reasoning': 'Demo classification',
                    'key_phrases': ['demo', 'test'],
                    'suggested_action': 'Review email'
                }
            )
            
            db.add(event)
            db.commit()
            db.refresh(event)
            
            print(f"✅ Created email event: {event.email_type} from {event.company_name}")
        
        # Query and display events
        events = db.query(EmailEvent).filter(
            EmailEvent.user_id == "demo_user"
        ).all()
        
        print(f"\n📊 Found {len(events)} email events:")
        for event in events:
            print(f"   • {event.email_type} from {event.company_name} ({event.confidence_score:.1%} confidence)")
        
        # Create sync log
        sync_log = EmailSyncLog(
            user_id="demo_user",
            emails_found=3,
            emails_processed=3,
            status='completed'
        )
        
        db.add(sync_log)
        db.commit()
        
        print(f"✅ Created sync log: {sync_log.status} with {sync_log.emails_processed} emails processed")
        
        # Clean up demo data
        db.query(EmailEvent).filter(EmailEvent.user_id == "demo_user").delete()
        db.query(EmailSyncLog).filter(EmailSyncLog.user_id == "demo_user").delete()
        db.query(UserGmailConnection).filter(UserGmailConnection.user_id == "demo_user").delete()
        db.commit()
        
        print("🧹 Cleaned up demo data")
        
    except Exception as e:
        print(f"❌ Database demo failed: {e}")
    finally:
        db.close()

def demo_api_endpoints():
    """Demo API endpoint structure"""
    print("\n🌐 API Endpoints Demo")
    print("=" * 50)
    
    endpoints = [
        ("GET", "/api/v1/email-agent/config/status", "Check configuration status"),
        ("POST", "/api/v1/email-agent/connect", "Connect Gmail account"),
        ("GET", "/api/v1/email-agent/status/{user_id}", "Get connection status"),
        ("POST", "/api/v1/email-agent/process/{user_id}", "Process emails"),
        ("GET", "/api/v1/email-agent/summary/{user_id}", "Get processing summary"),
        ("GET", "/api/v1/email-agent/events/{user_id}", "Get email events"),
        ("POST", "/api/v1/email-agent/events/{event_id}/review", "Mark event as reviewed"),
        ("GET", "/api/v1/email-agent/sync-logs/{user_id}", "Get sync logs"),
        ("DELETE", "/api/v1/email-agent/disconnect/{user_id}", "Disconnect Gmail")
    ]
    
    for method, endpoint, description in endpoints:
        print(f"{method:6} {endpoint}")
        print(f"       {description}")
        print()

def main():
    """Run the email agent demo"""
    print("🚀 Email Agent Demo")
    print("=" * 60)
    print("This demo shows the email agent functionality without requiring")
    print("external API keys or Gmail connection.")
    print()
    
    # Demo email classification
    asyncio.run(demo_email_classification())
    
    # Demo database operations
    demo_database_operations()
    
    # Demo API endpoints
    demo_api_endpoints()
    
    print("=" * 60)
    print("🎉 Demo completed!")
    print()
    print("To use the full email agent:")
    print("1. Get an Arcade.dev API key")
    print("2. Set up your .env file")
    print("3. Run: uvicorn app.main:app --reload")
    print("4. Visit: http://localhost:3000/email-agent")
    print()
    print("The email agent is now ready for development and testing!")

if __name__ == "__main__":
    main() 