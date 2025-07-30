# Google OAuth Setup Guide

This guide will help you set up Google OAuth 2.0 for Gmail integration in the LinkedIn Automation application.

## Prerequisites

- Google Cloud Console account
- Python 3.8+ with pip
- PostgreSQL database
- Redis server

## Step 1: Google Cloud Console Setup

### 1.1 Create a New Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable billing (required for API usage)

### 1.2 Enable Gmail API
1. Navigate to **APIs & Services** → **Library**
2. Search for "Gmail API"
3. Click on it and press **Enable**

### 1.3 Configure OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** user type
3. Fill in the required information:
   - **App name**: LinkedIn-Automation
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Add the following scopes:
   - `openid`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/userinfo.email`
5. Add test users (your email address)
6. Save and continue

### 1.4 Create OAuth 2.0 Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client IDs**
3. Choose **Web application**
4. Set the following:
   - **Name**: LinkedIn-Automation Web Client
   - **Authorized redirect URIs**: `http://localhost:8000/api/v1/email-agent/oauth/callback`
5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

## Step 2: Environment Variables

Add the following to your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/email-agent/oauth/callback

# OpenAI Configuration (for email classification)
OPENAPI_KEY=your_openai_api_key_here
```

## Step 3: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 4: Database Migration

```bash
cd backend
alembic upgrade head
```

## Step 5: Test the Setup

Run the test script to verify everything is configured correctly:

```bash
cd backend
python scripts/test_oauth_flow.py
```

You should see:
```
✓ Authorization URL created successfully
```

## Step 6: Start the Application

### Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

## Step 7: Test the OAuth Flow

1. Navigate to `http://localhost:3000/email-agent`
2. Enter your Gmail address
3. Click "Connect Gmail"
4. Complete the Google OAuth authorization
5. Verify the connection status

## Troubleshooting

### Error: "Access blocked: App has not completed Google verification process"
**Solution**: Add your email as a test user in the OAuth consent screen.

### Error: "Scope has changed"
**Solution**: The application now includes the `openid` scope by default. This is required for proper OAuth flow.

### Error: "Failed to exchange code for tokens"
**Solution**: 
1. Verify your redirect URI matches exactly
2. Check that your client ID and secret are correct
3. Ensure the OAuth consent screen is configured properly

### Error: "Invalid redirect URI"
**Solution**: Make sure the redirect URI in your Google Cloud Console matches exactly: `http://localhost:8000/api/v1/email-agent/oauth/callback`

## Security Considerations

1. **Never commit credentials** to version control
2. **Use environment variables** for sensitive data
3. **Add test users** to OAuth consent screen for development
4. **Consider app verification** for production use

## Production Deployment

For production deployment:

1. **Update redirect URIs** to your production domain
2. **Complete app verification** if making it public
3. **Use secure environment variables**
4. **Enable HTTPS** for all OAuth endpoints

## API Endpoints

- `POST /api/v1/email-agent/connect` - Start OAuth flow
- `GET /api/v1/email-agent/oauth/callback` - Handle OAuth callback
- `GET /api/v1/email-agent/status/{user_id}` - Check connection status
- `POST /api/v1/email-agent/process/{user_id}` - Process emails
- `DELETE /api/v1/email-agent/disconnect/{user_id}` - Disconnect Gmail

## Support

If you encounter issues:
1. Check the application logs
2. Verify your Google Cloud Console configuration
3. Ensure all environment variables are set correctly
4. Test with the provided test script 