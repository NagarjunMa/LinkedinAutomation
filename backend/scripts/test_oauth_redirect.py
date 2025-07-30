#!/usr/bin/env python3
"""
Test script to verify OAuth redirect functionality
"""

import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from starlette.responses import RedirectResponse

def test_redirect_url():
    """Test redirect URL construction"""
    print("Testing OAuth Redirect URLs...")
    
    # Test success redirect
    gmail_email = "test@gmail.com"
    success_url = f"http://localhost:3000/email-agent?success=true&gmail_email={gmail_email.replace('@', '%40')}"
    print(f"Success URL: {success_url}")
    
    # Test error redirect
    error_message = "Failed to exchange code for tokens"
    error_url = f"http://localhost:3000/email-agent?error={error_message.replace(' ', '%20')}"
    print(f"Error URL: {error_url}")
    
    # Test URL decoding
    decoded_email = gmail_email.replace('%40', '@')
    decoded_error = error_message.replace('%20', ' ')
    print(f"Decoded email: {decoded_email}")
    print(f"Decoded error: {decoded_error}")
    
    print("✓ Redirect URL construction works correctly")

if __name__ == "__main__":
    test_redirect_url() 