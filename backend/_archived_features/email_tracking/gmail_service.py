import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import re
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

class GmailService:
    """Gmail service using Google OAuth 2.0"""
    
    def __init__(self):
        self.debug = settings.DEBUG_EMAIL_PROCESSING
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.scopes = settings.GOOGLE_SCOPES
        
        if not self.client_id or not self.client_secret:
            logger.warning("Google OAuth credentials not configured")
    
    def create_oauth_flow(self) -> Flow:
        """Create OAuth flow for Google authentication"""
        return Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                    "scopes": self.scopes
                }
            },
            scopes=self.scopes
        )
    
    def get_authorization_url(self, user_id: str) -> Dict[str, Any]:
        """Get authorization URL for Google OAuth"""
        try:
            flow = self.create_oauth_flow()
            flow.redirect_uri = self.redirect_uri
            
            # Add state parameter to identify user
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id
            )
            
            return {
                'status': 'auth_required',
                'auth_url': authorization_url,
                'state': state,
                'message': 'Please complete Google authorization'
            }
        except Exception as e:
            logger.error(f"Failed to create authorization URL: {e}")
            return {
                'status': 'error',
                'message': f'Failed to create authorization URL: {str(e)}'
            }
    
    def exchange_code_for_tokens(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        try:
            flow = self.create_oauth_flow()
            flow.redirect_uri = self.redirect_uri
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Get user info
            user_info = self._get_user_info(credentials)
            
            return {
                'status': 'success',
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expiry': credentials.expiry,
                'google_user_id': user_info.get('id'),
                'gmail_email': user_info.get('email'),
                'user_id': state  # From state parameter
            }
        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            return {
                'status': 'error',
                'message': f'Failed to exchange code for tokens: {str(e)}'
            }
    
    def _get_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        """Get user information from Google"""
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {}
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            credentials = Credentials(
                None,  # No access token initially
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Refresh the credentials
            credentials.refresh(Request())
            
            return {
                'status': 'success',
                'access_token': credentials.token,
                'token_expiry': credentials.expiry
            }
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return {
                'status': 'error',
                'message': f'Failed to refresh access token: {str(e)}'
            }
    
    def create_gmail_service(self, access_token: str) -> Any:
        """Create Gmail API service with access token"""
        try:
            credentials = Credentials(access_token)
            service = build('gmail', 'v1', credentials=credentials)
            return service
        except Exception as e:
            logger.error(f"Failed to create Gmail service: {e}")
            return None
    
    async def fetch_job_emails(self, user_id: str, user_email: str = None, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch job-related emails from Gmail"""
        try:
            # Get connection from database (this would be passed from the calling function)
            # For now, we'll assume the connection is passed as a parameter
            
            # This method will be called with the actual connection object
            # The connection should have valid access_token and refresh_token
            
            return []  # Placeholder - will be implemented with actual connection
            
        except Exception as e:
            logger.error(f"Failed to fetch job emails: {e}")
            return []
    
    async def check_connection(self, user_id: str, user_email: str = None) -> Dict[str, Any]:
        """Check if Gmail connection is valid"""
        try:
            # This method will be called with the actual connection object
            # For now, return a placeholder
            return {
                'connected': False,
                'message': 'Connection check not implemented yet'
            }
        except Exception as e:
            logger.error(f"Failed to check connection: {e}")
            return {
                'connected': False,
                'message': f'Connection check failed: {str(e)}'
            }

# Test function for development
async def test_gmail_service():
    """Test the Gmail service"""
    print("🔍 Testing Gmail Service")
    print("=" * 50)
    
    service = GmailService()
    
    if not service.client_id or not service.client_secret:
        print("❌ Google OAuth credentials not configured")
        print("   Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file")
        return False
    
    print("✅ Gmail service initialized successfully")
    
    # Test authorization URL creation
    print("\n1. Testing authorization URL creation...")
    auth_result = service.get_authorization_url("test_user_123")
    
    if auth_result['status'] == 'auth_required':
        print(f"   ✅ Authorization URL created: {auth_result['auth_url'][:50]}...")
        print(f"   State: {auth_result['state']}")
    else:
        print(f"   ❌ Failed to create authorization URL: {auth_result['message']}")
        return False
    
    print("\n🎉 Gmail service is working!")
    print("   You can now use Google OAuth for Gmail integration")
    
    return True 