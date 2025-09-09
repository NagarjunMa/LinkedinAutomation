# Authentication System Setup Guide

This guide explains how to set up the unified Google OAuth authentication system that handles both user authentication and Gmail access.

## Overview

The new authentication system provides:
- **Unified OAuth Flow**: Single Google sign-in that grants both user authentication and Gmail access
- **Supabase Integration**: Session management and user data storage
- **Protected Routes**: Automatic redirection for unauthenticated users
- **Seamless User Experience**: No separate Gmail connection step needed

## Prerequisites

1. **Supabase Project**: You need a Supabase account and project
2. **Google Cloud Project**: For OAuth credentials
3. **Gmail API**: Enabled in your Google Cloud project

## Step 1: Supabase Setup

### 1.1 Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your project URL and anon key

### 1.2 Configure Authentication
1. In your Supabase dashboard, go to **Authentication** → **Providers**
2. Enable **Google** provider
3. Add your Google OAuth credentials (Client ID and Client Secret)
4. Set the redirect URL to: `https://your-domain.com/auth/callback`

### 1.3 Environment Variables
Create a `.env.local` file in your frontend directory:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Step 2: Google Cloud Setup

### 2.1 Create OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Gmail API**
4. Go to **APIs & Services** → **Credentials**
5. Create **OAuth 2.0 Client ID**
6. Set application type to **Web application**

### 2.2 Configure OAuth Consent Screen
1. Go to **OAuth consent screen**
2. Set app name, user support email, and developer contact
3. Add scopes:
   - `email`
   - `profile`
   - `https://www.googleapis.com/auth/gmail.readonly`

### 2.3 Authorized Redirect URIs
Add these redirect URIs to your OAuth client:
- `https://your-domain.com/auth/callback`
- `http://localhost:3000/auth/callback` (for development)

## Step 3: Backend Integration

### 3.1 Update Gmail Service
The backend Gmail service should now use the access token from Supabase instead of managing its own OAuth flow.

### 3.2 Environment Variables (Backend)
Add to your backend `.env`:

```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## Step 4: Frontend Configuration

### 4.1 Verify Components
Ensure these components are properly configured:
- `AuthProvider` in `src/contexts/auth-context.tsx`
- `ProtectedRoute` in `src/components/protected-route.tsx`
- `LandingPageCTA` in `src/components/landing-page-cta.tsx`

### 4.2 Protected Routes
All dashboard routes are now protected. Users must authenticate before accessing:
- `/dashboard/*`
- `/email-agent`
- Any other protected features

## How It Works

### 1. User Flow
1. User visits landing page
2. Clicks "Start Free Trial" or "Get Started"
3. Redirected to Google OAuth (with Gmail scopes)
4. After successful authentication, redirected to `/auth/callback`
5. Supabase creates session and stores user data
6. User is redirected to dashboard
7. Gmail access is automatically available

### 2. Authentication Context
The `AuthContext` provides:
- `user`: Current user object
- `session`: Current session
- `loading`: Authentication state
- `signIn`: Initiate Google OAuth
- `signOutUser`: Sign out user
- `refreshUser`: Refresh user data

### 3. Protected Routes
The `ProtectedRoute` component:
- Checks if user is authenticated
- Shows loading state while checking
- Redirects unauthenticated users to landing page
- Renders children for authenticated users

## Testing

### 1. Development Testing
1. Start your frontend: `npm run dev`
2. Visit `http://localhost:3000`
3. Click "Start Free Trial"
4. Complete Google OAuth flow
5. Verify redirect to dashboard
6. Check that Gmail access is available

### 2. Production Testing
1. Deploy with proper environment variables
2. Test OAuth flow with production URLs
3. Verify session persistence
4. Test sign out functionality

## Troubleshooting

### Common Issues

1. **OAuth Redirect Error**
   - Check redirect URIs in Google Cloud Console
   - Verify Supabase redirect URL configuration

2. **Session Not Persisting**
   - Check Supabase configuration
   - Verify environment variables

3. **Gmail Access Denied**
   - Ensure Gmail API is enabled
   - Check OAuth scopes include Gmail access

4. **Protected Route Issues**
   - Verify `AuthProvider` is wrapping your app
   - Check `ProtectedRoute` implementation

### Debug Steps

1. Check browser console for errors
2. Verify Supabase client initialization
3. Check network requests to OAuth endpoints
4. Verify environment variables are loaded

## Security Considerations

1. **Environment Variables**: Never commit `.env.local` to version control
2. **OAuth Scopes**: Only request necessary scopes
3. **Session Management**: Supabase handles secure session storage
4. **HTTPS**: Use HTTPS in production for secure OAuth flow

## Next Steps

1. **User Profile Management**: Add user profile editing
2. **Email Preferences**: Allow users to configure email settings
3. **Team Features**: Add multi-user support
4. **Analytics**: Track authentication metrics

## Support

For issues or questions:
1. Check Supabase documentation
2. Review Google OAuth documentation
3. Check browser console for errors
4. Verify all environment variables are set correctly
