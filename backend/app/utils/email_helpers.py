import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test user for development
TEST_USER_ID = 999
TEST_USER_EMAIL = "test@example.com"

def validate_email_config() -> Dict[str, Any]:
    """
    Validate email agent configuration for Google OAuth
    
    Returns:
        Dict with validation results
    """
    required_vars = [
        'GOOGLE_CLIENT_ID', 
        'GOOGLE_CLIENT_SECRET',
        'OPENAPI_KEY'  # Using existing OpenAI key
    ]
    
    missing = []
    config_status = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            config_status[var] = "Missing"
        else:
            config_status[var] = "Configured"
    
    # Check optional settings
    optional_vars = [
        'GOOGLE_REDIRECT_URI',
        'EMAIL_CLASSIFICATION_MODEL',
        'EMAIL_SYNC_FREQUENCY_MINUTES',
        'EMAIL_CONFIDENCE_THRESHOLD',
        'DEBUG_EMAIL_PROCESSING'
    ]
    
    for var in optional_vars:
        value = os.getenv(var)
        config_status[var] = value if value else "Using default"
    
    is_valid = len(missing) == 0
    
    return {
        'is_valid': is_valid,
        'missing_vars': missing,
        'config_status': config_status,
        'test_user_id': TEST_USER_ID,
        'test_user_email': TEST_USER_EMAIL
    }

def get_email_config() -> Dict[str, Any]:
    """
    Get email agent configuration
    
    Returns:
        Dict with all email configuration
    """
    return {
        'google_client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'google_client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'google_redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/v1/email-agent/oauth/callback'),
        'openai_api_key': os.getenv('OPENAPI_KEY'),
        'email_classification_model': os.getenv('EMAIL_CLASSIFICATION_MODEL', 'gpt-4o-mini'),
        'email_sync_frequency_minutes': int(os.getenv('EMAIL_SYNC_FREQUENCY_MINUTES', '15')),
        'email_confidence_threshold': float(os.getenv('EMAIL_CONFIDENCE_THRESHOLD', '0.8')),
        'auto_update_threshold': float(os.getenv('AUTO_UPDATE_THRESHOLD', '0.85')),
        'debug_email_processing': os.getenv('DEBUG_EMAIL_PROCESSING', 'true').lower() == 'true',
        'log_level': os.getenv('LOG_LEVEL', 'DEBUG')
    }

def test_email_config():
    """
    Test email configuration and print results
    """
    print("=== Email Agent Configuration Test ===")
    
    validation = validate_email_config()
    config = get_email_config()
    
    print(f"Configuration Valid: {validation['is_valid']}")
    
    if validation['missing_vars']:
        print(f"Missing Variables: {validation['missing_vars']}")
        print("\nPlease add these to your .env file:")
        for var in validation['missing_vars']:
            if var == 'GOOGLE_CLIENT_ID':
                print(f"{var}=your_google_client_id_here")
            elif var == 'GOOGLE_CLIENT_SECRET':
                print(f"{var}=your_google_client_secret_here")
            elif var == 'OPENAPI_KEY':
                print(f"{var}=your_openai_key_here")
    
    print("\nConfiguration Status:")
    for var, status in validation['config_status'].items():
        print(f"  {var}: {status}")
    
    print(f"\nTest User ID: {validation['test_user_id']}")
    print(f"Test User Email: {validation['test_user_email']}")
    
    if validation['is_valid']:
        print("\n✅ Email agent is ready to use!")
        print("   You can now connect Gmail accounts using Google OAuth")
    else:
        print("\n❌ Please configure the missing variables to use the email agent")
    
    return validation['is_valid']

if __name__ == "__main__":
    test_email_config() 