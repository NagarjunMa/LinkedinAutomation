#!/usr/bin/env python3
"""
Test script for email-driven job status automation system
"""

import sys
import asyncio
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.email_classifier import EmailClassifier
from app.services.job_matcher import JobMatcher
from app.services.email_processor import EmailProcessor
from app.db.session import SessionLocal
from app.models.job import JobListing
from app.models.email_models import UserGmailConnection

async def test_email_classification():
    """Test email classification with sample emails"""
    print("🧪 Testing Email Classification...")
    
    classifier = EmailClassifier()
    
    test_emails = [
        {
            "subject": "Thank you for your application",
            "content": "Dear John, Thank you for your application for the Software Engineer position at TechCorp. We have received your application and will review it carefully. We will get back to you within 2 weeks.",
            "sender": "careers@techcorp.com"
        },
        {
            "subject": "Interview invitation - Software Engineer",
            "content": "Hello John, We are pleased to invite you for an interview for the Software Engineer position. Please let us know your availability for next week.",
            "sender": "hr@techcorp.com"
        },
        {
            "subject": "Application status update",
            "content": "Unfortunately, we have decided to move forward with other candidates for the Software Engineer position. We appreciate your interest in TechCorp.",
            "sender": "recruiting@techcorp.com"
        },
        {
            "subject": "Job offer - Software Engineer",
            "content": "Congratulations! We are pleased to offer you the Software Engineer position at TechCorp. Please review the attached offer letter.",
            "sender": "hr@techcorp.com"
        }
    ]
    
    for i, email in enumerate(test_emails, 1):
        print(f"\n📧 Test Email {i}: {email['subject']}")
        
        result = await classifier.classify_email(
            email['content'], 
            email['subject'], 
            email['sender']
        )
        
        print(f"   Type: {result['email_type']}")
        print(f"   Confidence: {result['confidence_score']:.2f}")
        print(f"   Company: {result['company_name']}")
        print(f"   Job Title: {result['job_title']}")
        print(f"   Sentiment: {result['sentiment']}")
        print(f"   Job Related: {classifier.is_job_related(result['email_type'], result['confidence_score'])}")
        print(f"   Should Update Status: {classifier.should_update_job_status(result['email_type'], result['confidence_score'])}")

def test_job_matching():
    """Test job matching functionality"""
    print("\n🎯 Testing Job Matching...")
    
    matcher = JobMatcher()
    
    # Test company name matching
    test_cases = [
        ("TechCorp", "TechCorp Inc"),
        ("Google", "google.com"),
        ("Microsoft", "Microsoft Corporation"),
        ("Apple", "Apple Inc."),
        ("Amazon", "amazon.com")
    ]
    
    for company1, company2 in test_cases:
        score = matcher._match_company_name(company1, company2)
        print(f"   {company1} vs {company2}: {score:.2f}")
    
    # Test job title matching
    title_tests = [
        ("Software Engineer", "Software Engineer"),
        ("Software Engineer", "Senior Software Engineer"),
        ("Data Scientist", "Data Analyst"),
        ("Product Manager", "Product Manager")
    ]
    
    print("\n   Job Title Matching:")
    for title1, title2 in title_tests:
        score = matcher._match_job_title(title1, title2)
        print(f"   {title1} vs {title2}: {score:.2f}")

async def test_complete_workflow():
    """Test the complete email processing workflow"""
    print("\n🔄 Testing Complete Workflow...")
    
    db = SessionLocal()
    try:
        # Check if test user exists
        user_id = "999"
        
        # Check Gmail connection
        connection = db.query(UserGmailConnection).filter(
            UserGmailConnection.user_id == user_id
        ).first()
        
        if not connection:
            print("   ❌ No Gmail connection found for test user")
            return
        
        if not connection.is_authorized:
            print("   ❌ Gmail connection not authorized")
            return
        
        print("   ✅ Gmail connection found and authorized")
        
        # Check if user has job applications
        from app.models.job import JobApplication
        applications = db.query(JobApplication).filter(JobApplication.user_id == user_id).all()
        print(f"   📋 Found {len(applications)} job applications")
        
        if applications:
            print("   Sample applications:")
            for app in applications[:3]:
                job = db.query(JobListing).filter(JobListing.id == app.job_id).first()
                if job:
                    print(f"     - {job.title} at {job.company} (Status: {app.application_status})")
        
        # Test email processor
        processor = EmailProcessor()
        
        # Note: This would require actual Gmail access
        print("   ⚠️  Email processing requires Gmail API access")
        print("   💡 Use the API endpoints to test with real data")
        
    finally:
        db.close()

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/api/v1/email-agent/status/999",
        "/api/v1/email-agent/summary/999",
        "/api/v1/email-agent/analytics/999",
        "/api/v1/email-agent/test-classification?subject=Test&content=Test content",
        "/api/v1/email-agent/test-job-matching/999?company_name=TechCorp&job_title=Software Engineer"
    ]
    
    print("   Available endpoints to test:")
    for endpoint in endpoints:
        print(f"     GET {base_url}{endpoint}")

async def main():
    """Run all tests"""
    print("🚀 Email Automation System Test Suite")
    print("=" * 50)
    
    # Test email classification
    await test_email_classification()
    
    # Test job matching
    test_job_matching()
    
    # Test complete workflow
    await test_complete_workflow()
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("\n📝 Next Steps:")
    print("   1. Start the backend server: uvicorn app.main:app --reload")
    print("   2. Test API endpoints with curl or browser")
    print("   3. Connect Gmail account and process real emails")
    print("   4. Monitor job status updates in the dashboard")

if __name__ == "__main__":
    asyncio.run(main()) 