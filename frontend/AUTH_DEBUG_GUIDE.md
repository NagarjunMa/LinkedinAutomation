# Authentication Debug Guide

## Critical Fixes Applied

### 1. **Enhanced AuthContext (contexts/auth-context.tsx)**
- ✅ Increased retry attempts from 3 to 5 with exponential backoff
- ✅ Better detection of OAuth callbacks and email confirmation flows
- ✅ Enhanced logging with timestamps and emojis for easier debugging
- ✅ Fixed useEffect setup to properly handle auth state changes

### 2. **Improved Middleware (middleware.ts)**
- ✅ Added special handling for auth callback scenarios (code= and token_hash= parameters)
- ✅ More lenient timing for dashboard access during auth flows
- ✅ Enhanced debugging with callback detection
- ✅ Better cache control headers

### 3. **Session Debug Endpoint (api/auth/test-session/route.ts)**
- ✅ New endpoint to debug session state and cookie detection
- ✅ Comprehensive cookie analysis and project reference detection

## Testing the Fixes

### Test 1: Google OAuth Flow
1. Go to `http://localhost:3000`
2. Click "Sign In with Google"
3. **Watch browser console** for AuthContext logs
4. Should see:
   ```
   🔄 Middleware: Potential auth callback detected on /dashboard, allowing through temporarily
   ✅ AuthContext: Session loaded successfully after X attempts
   ✅ AuthContext: User signed in via auth state change
   ```

### Test 2: Email Verification Flow
1. Sign up with email/password at `http://localhost:3000/signup`
2. Check email for verification link
3. Click verification link
4. **Watch browser console** for logs
5. Should redirect to dashboard without "Authentication Required"

### Test 3: Session Debug Tool
1. After logging in, visit: `http://localhost:3000/api/auth/test-session`
2. Check the JSON response for:
   - `hasSession: true`
   - `cookieAnalysis.hasExpectedCookie: true`
   - Session details populated

## Debug Commands

### Check Current Auth State
```bash
# In browser console after logging in:
fetch('/api/auth/test-session').then(r => r.json()).then(console.log)
```

### Monitor AuthContext Logs
Look for these patterns in browser console:
- `🔄 AuthContext: Retrying session retrieval` - Normal during auth flows
- `✅ AuthContext: Session loaded successfully` - Success!
- `❌ AuthContext: No session found after X attempts` - Problem!

### Check Middleware Logs
In the Next.js dev server console, look for:
- `🔄 Middleware: Potential auth callback detected` - Good sign during OAuth
- `🚫 Redirecting /dashboard to / - No auth session` - Problem detected

## Expected Behavior After Fixes

### ✅ OAuth Flow
1. User clicks "Sign In with Google"
2. Redirected to Google OAuth
3. Returns to `/api/auth/callback` with auth code
4. Server exchanges code for session and sets cookies
5. Redirects to `/dashboard`
6. Middleware detects callback and allows through
7. AuthContext loads session successfully
8. User sees dashboard (no "Authentication Required")

### ✅ Email Verification Flow
1. User signs up with email
2. Clicks verification link
3. Goes to `/api/auth/confirm` with token_hash
4. Server verifies email and creates session
5. Redirects to `/dashboard`
6. Middleware allows through due to callback detection
7. AuthContext loads session
8. User sees dashboard

## Troubleshooting

### Still seeing "Authentication Required"?

1. **Check session debug endpoint:**
   ```
   GET /api/auth/test-session
   ```

2. **Clear cookies and try again:**
   ```javascript
   // In browser console
   document.cookie.split(";").forEach(function(c) {
     document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
   });
   ```

3. **Check browser console** for auth context logs

4. **Verify environment variables:**
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Common Issues

- **Timing Issue**: AuthContext still retrying → Increase retry delay or count
- **Cookie Issue**: Check project reference in middleware logs
- **Supabase Config**: Verify OAuth redirect URLs in Supabase dashboard

## Quick Fix Validation

Run this test sequence:
1. `npm run dev` (start frontend)
2. Visit `http://localhost:3000`
3. Try Google OAuth sign in
4. Watch console logs during the flow
5. If still failing, check `/api/auth/test-session` response

The authentication flow should now work without the "Authentication Required" page appearing after successful OAuth or email verification.