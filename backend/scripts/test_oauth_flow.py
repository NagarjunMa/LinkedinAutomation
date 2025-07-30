#!/usr/bin/env python3
"""
Test script to verify Google OAuth flow with updated scopes
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.gmail_service import GmailService
from app.core.config import settings

def test_oauth_flow():
    """Test the OAuth flow creation"""
    print("Testing Google OAuth Flow...")
    print(f"Client ID: {'✓ Set' if settings.GOOGLE_CLIENT_ID else '✗ Missing'}")
    print(f"Client Secret: {'✓ Set' if settings.GOOGLE_CLIENT_SECRET else '✗ Missing'}")
    print(f"Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
    print(f"Scopes: {settings.GOOGLE_SCOPES}")
    
    try:
        gmail_service = GmailService()
        
        # Test authorization URL creation
        result = gmail_service.get_authorization_url("test_user_123")
        
        if result['status'] == 'auth_required':
            print("✓ Authorization URL created successfully")
            print(f"Auth URL: {result['auth_url'][:100]}...")
            print(f"State: {result['state']}")
        else:
            print(f"✗ Failed to create authorization URL: {result['message']}")
            
    except Exception as e:
        print(f"✗ Error testing OAuth flow: {e}")

if __name__ == "__main__":
    test_oauth_flow() 