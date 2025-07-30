#!/usr/bin/env python3
"""
Gmail Connection Test Script
Tests the Gmail connection with your specific email
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.gmail_service import GmailService
from app.utils.email_helpers import validate_email_config

async def test_gmail_connection():
    """Test Gmail connection with your email"""
    print("🔗 Gmail Connection Test")
    print("=" * 50)
    
    # Test configuration
    print("1. Checking configuration...")
    config = validate_email_config()
    print(f"   Configuration valid: {config['is_valid']}")
    print(f"   Arcade API key: {'✓ Configured' if config['config_status']['ARCADE_API_KEY'] == 'Configured' else '✗ Missing'}")
    print()
    
    if not config['is_valid']:
        print("❌ Configuration is invalid. Please check your .env file.")
        return
    
    # Test Gmail service
    print("2. Testing Gmail service...")
    service = GmailService()
    
    # Test with your email
    user_id = "999"
    user_email = "nagarjunmallesh@gmail.com"
    
    print(f"   User ID: {user_id}")
    print(f"   Email: {user_email}")
    print()
    
    try:
        print("3. Attempting Gmail connection...")
        result = await service.connect_gmail(user_id, user_email)
        
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        
        if result['status'] == 'auth_required':
            print("\n✅ SUCCESS! Gmail authorization required.")
            print(f"   Auth URL: {result['auth_url']}")
            print("\n📋 Next steps:")
            print("   1. Click the auth URL above")
            print("   2. Complete Gmail authorization in your browser")
            print("   3. Return to the application")
            print("   4. Test email processing")
            
        elif result['status'] == 'connected':
            print("\n✅ SUCCESS! Gmail already connected.")
            print("\n📋 Next steps:")
            print("   1. Test email processing")
            print("   2. Check the web interface")
            
        elif result['status'] == 'error':
            print(f"\n❌ ERROR: {result['message']}")
            
            if "401" in result['message']:
                print("\n🔧 Troubleshooting 401 error:")
                print("   1. Check if your Arcade API key is valid")
                print("   2. Verify the key is correctly set in .env file")
                print("   3. Make sure you have an active Arcade.dev account")
                print("   4. Check Arcade.dev documentation for API key format")
                
            elif "500" in result['message']:
                print("\n🔧 Troubleshooting 500 error:")
                print("   1. Check Arcade.dev service status")
                print("   2. Verify your account has Gmail integration enabled")
                print("   3. Contact Arcade.dev support if issue persists")
        
    except Exception as e:
        print(f"\n❌ Exception occurred: {str(e)}")
        print("\n🔧 General troubleshooting:")
        print("   1. Check your internet connection")
        print("   2. Verify Arcade.dev service is available")
        print("   3. Check the logs for more details")

def test_web_interface():
    """Instructions for testing via web interface"""
    print("\n🌐 Web Interface Test")
    print("=" * 50)
    print("You can also test the Gmail connection through the web interface:")
    print()
    print("1. Start the backend server:")
    print("   cd backend")
    print("   uvicorn app.main:app --reload")
    print()
    print("2. Start the frontend (if not already running):")
    print("   cd frontend")
    print("   npm run dev")
    print()
    print("3. Visit the email agent page:")
    print("   http://localhost:3000/email-agent")
    print()
    print("4. Use the Gmail Connection component to:")
    print("   - Connect your Gmail account")
    print("   - Process emails")
    print("   - View email dashboard")

def main():
    """Run the Gmail connection test"""
    print("🚀 Gmail Connection Test for nagarjunmallesh@gmail.com")
    print("=" * 60)
    
    # Test Gmail connection
    asyncio.run(test_gmail_connection())
    
    # Show web interface instructions
    test_web_interface()
    
    print("\n" + "=" * 60)
    print("🎯 Test completed!")
    print("\nIf you're still having issues:")
    print("1. Check your Arcade.dev account and API key")
    print("2. Verify Gmail integration is enabled in Arcade.dev")
    print("3. Try the web interface for a better user experience")
    print("4. Check the logs for detailed error information")

if __name__ == "__main__":
    main() 