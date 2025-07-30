#!/usr/bin/env python3
"""
Email Agent Test Script
Tests the email agent configuration and basic functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.utils.email_helpers import test_email_config, validate_email_config
from app.services.gmail_service import GmailService
from app.services.email_classifier import EmailClassifier
from app.services.email_processor import EmailProcessor
from app.db.session import SessionLocal
from app.models.email_models import UserGmailConnection, EmailEvent, EmailSyncLog

async def test_gmail_service():
    """Test Gmail service functionality"""
    print("\n=== Testing Gmail Service ===")
    
    service = GmailService()
    
    # Test connection
    print("Testing Gmail connection...")
    result = await service.connect_gmail("999", "test@example.com")
    print(f"Connection result: {result}")
    
    if result['status'] == 'auth_required':
        print(f"✅ Auth URL generated: {result['auth_url']}")
        print("Please complete authorization in your browser")
    elif result['status'] == 'connected':
        print("✅ Gmail already connected")
    else:
        print(f"❌ Connection failed: {result['message']}")
    
    return result

async def test_email_classifier():
    """Test email classifier functionality"""
    print("\n=== Testing Email Classifier ===")
    
    classifier = EmailClassifier()
    
    # Test emails
    test_cases = [
        {
            'sender': 'noreply@company.com',
            'subject': 'Thank you for your application',
            'content': 'We received your application for Software Engineer. We will review and get back to you.'
        },
        {
            'sender': 'recruiting@tech.com', 
            'subject': 'Interview invitation',
            'content': 'We would like to schedule an interview for the Software Engineer position. Are you available next week?'
        },
        {
            'sender': 'hr@startup.com',
            'subject': 'Application status',
            'content': 'Unfortunately, we have decided to move forward with other candidates for this position.'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['subject']}")
        
        result = await classifier.classify_email(
            test['sender'], 
            test['subject'], 
            test['content']
        )
        
        print(f"  Type: {result.email_type}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Company: {result.company_name}")
        print(f"  Action: {result.suggested_action}")

def test_database_models():
    """Test database models"""
    print("\n=== Testing Database Models ===")
    
    try:
        db = SessionLocal()
        
        # Test creating a Gmail connection
        connection = UserGmailConnection(
            user_id="999",
            arcade_user_id="dev_999_test",
            gmail_email="test@example.com",
            is_authorized=True
        )
        
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        print(f"✅ Created Gmail connection: {connection}")
        
        # Test creating an email event
        event = EmailEvent(
            user_id="999",
            gmail_connection_id=connection.id,
            email_message_id="test_message_123",
            sender_email="test@company.com",
            subject="Test Email",
            email_received_at="2024-01-01T12:00:00",
            email_type="confirmation",
            confidence_score=0.9,
            company_name="Test Company"
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        print(f"✅ Created email event: {event}")
        
        # Clean up
        db.delete(event)
        db.delete(connection)
        db.commit()
        
        print("✅ Database models working correctly")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
    finally:
        db.close()

async def test_email_processor():
    """Test email processor functionality"""
    print("\n=== Testing Email Processor ===")
    
    try:
        db = SessionLocal()
        processor = EmailProcessor()
        
        # Test user summary
        summary = await processor.get_user_summary("999", db)
        print(f"User summary: {summary}")
        
        print("✅ Email processor working correctly")
        
    except Exception as e:
        print(f"❌ Email processor test failed: {e}")
    finally:
        db.close()

def main():
    """Run all tests"""
    print("🚀 Email Agent Test Suite")
    print("=" * 50)
    
    # Test configuration
    print("\n=== Testing Configuration ===")
    config_valid = test_email_config()
    
    if not config_valid:
        print("\n❌ Configuration validation failed!")
        print("Please check your environment variables and try again.")
        return
    
    print("\n✅ Configuration is valid!")
    
    # Test database models
    test_database_models()
    
    # Test services
    asyncio.run(test_email_classifier())
    asyncio.run(test_gmail_service())
    asyncio.run(test_email_processor())
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Install arcadepy: pip install arcadepy")
    print("2. Set up your .env file with API keys")
    print("3. Run the backend server: uvicorn app.main:app --reload")
    print("4. Visit http://localhost:3000/email-agent to test the UI")

if __name__ == "__main__":
    main() 