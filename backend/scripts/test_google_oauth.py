#!/usr/bin/env python3
"""
Test Google OAuth Setup
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.gmail_service import GmailService

def test_google_oauth_setup():
    """Test Google OAuth configuration"""
    print("🔍 Testing Google OAuth Setup")
    print("=" * 50)
    
    # Check environment variables
    print("1. Checking environment variables...")
    
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    
    if not client_id:
        print("   ❌ GOOGLE_CLIENT_ID not found")
        return False
    else:
        print(f"   ✅ GOOGLE_CLIENT_ID found: {client_id[:10]}...")
    
    if not client_secret:
        print("   ❌ GOOGLE_CLIENT_SECRET not found")
        return False
    else:
        print(f"   ✅ GOOGLE_CLIENT_SECRET found: {client_secret[:10]}...")
    
    print(f"   ✅ GOOGLE_REDIRECT_URI: {redirect_uri}")
    
    # Test Gmail service initialization
    print("\n2. Testing Gmail service initialization...")
    try:
        gmail_service = GmailService()
        print("   ✅ Gmail service initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize Gmail service: {e}")
        return False
    
    # Test OAuth flow creation
    print("\n3. Testing OAuth flow creation...")
    try:
        auth_result = gmail_service.get_authorization_url("test_user_123")
        
        if auth_result['status'] == 'auth_required':
            print("   ✅ Authorization URL created successfully")
            print(f"   Auth URL: {auth_result['auth_url'][:50]}...")
            print(f"   State: {auth_result['state']}")
        else:
            print(f"   ❌ Failed to create authorization URL: {auth_result['message']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Failed to create OAuth flow: {e}")
        return False
    
    # Test scopes
    print("\n4. Checking OAuth scopes...")
    expected_scopes = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/userinfo.email"
    ]
    
    for scope in expected_scopes:
        if scope in settings.GOOGLE_SCOPES:
            print(f"   ✅ Scope configured: {scope}")
        else:
            print(f"   ❌ Missing scope: {scope}")
            return False
    
    print("\n🎉 Google OAuth setup is working correctly!")
    print("\nNext steps:")
    print("1. Start your backend server: uvicorn app.main:app --reload")
    print("2. Start your frontend: npm run dev")
    print("3. Navigate to http://localhost:3000/email-agent")
    print("4. Click 'Connect Gmail' to test the OAuth flow")
    
    return True

def main():
    """Run the test"""
    print("🚀 Google OAuth Setup Test")
    print("=" * 50)
    
    success = test_google_oauth_setup()
    
    if not success:
        print("\n❌ Setup test failed!")
        print("\nPlease check:")
        print("1. Your .env file has GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
        print("2. Your Google Cloud Console OAuth configuration")
        print("3. The redirect URI matches your environment variable")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main() 