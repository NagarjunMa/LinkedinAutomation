# Environment Variables Configuration

## Critical Issue Identified
❌ **MISMATCH FOUND:** Railway backend deployment uses `OPENAPI_KEY` but code expects `OPENAI_API_KEY`

## Backend Environment Variables (Railway)

### Current Railway Variables (from screenshot)
```
GOOGLE_CLIENT_ID=*******
GOOGLE_CLIENT_SECRET=*******
NEXT_PUBLIC_GOOGLE_CLIENT_ID=*******
NEXT_PUBLIC_SUPABASE_ANON_KEY=*******
NEXT_PUBLIC_SUPABASE_URL=*******
OPENAPI_KEY=*******  ⚠️ INCORRECT NAME
POSTGRES_DB=*******
POSTGRES_PASSWORD=*******
POSTGRES_SERVER=*******
POSTGRES_USER=*******
SECRET_KEY=*******
SQLALCHEMY_DATABASE_URI=*******
SUPABASE_ANON_KEY=*******
SUPABASE_JWT_SECRET=*******
SUPABASE_URL=*******
```

### Required Changes in Railway Backend
1. **CRITICAL:** Rename `OPENAPI_KEY` → `OPENAI_API_KEY`
2. Remove frontend variables from backend (they're not needed there):
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_SUPABASE_URL`

### Complete Backend Variables List
```
# Database Configuration
POSTGRES_SERVER=<supabase-host>
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<your-password>
POSTGRES_DB=postgres
SQLALCHEMY_DATABASE_URI=postgresql://postgres:<password>@<host>:5432/postgres

# Supabase Configuration
SUPABASE_URL=https://fecoflibopgxliexcdbg.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_JWT_SECRET=<your-jwt-secret>

# AI Service
OPENAI_API_KEY=<your-openai-key>  # ⚠️ MUST be renamed from OPENAPI_KEY

# Authentication
SECRET_KEY=<secure-32-char-string>

# Google OAuth
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>

# Application Settings
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://your-frontend-railway-url.railway.app
```

## Frontend Environment Variables (Railway)

### Currently Missing in Railway Frontend
The frontend Railway deployment appears to have NO environment variables set. This is why the app may not be connecting to the backend properly.

### Required Frontend Variables
```
NEXT_PUBLIC_API_URL=https://your-backend-railway-url.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://fecoflibopgxliexcdbg.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZlY29mbGlib3BneGxpZXhjZGJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk0MDU5MDQsImV4cCI6MjA2NDk4MTkwNH0.sgOtVlM2Eom1McYT9DAMc0pKPLND-s4t99LelA5E--Y
NEXT_PUBLIC_GOOGLE_CLIENT_ID=706462409929-gtcraefuvdqqpjmlbt0f6ko1djf1aaij.apps.googleusercontent.com
```

## Immediate Actions Required

### 1. Railway Backend (Shared Variables)
- [ ] Rename `OPENAPI_KEY` to `OPENAI_API_KEY`
- [ ] Remove frontend-specific variables from backend
- [ ] Ensure `CORS_ORIGINS` includes frontend Railway URL

### 2. Railway Frontend (Shared Variables)
- [ ] Add all `NEXT_PUBLIC_*` variables listed above
- [ ] Set `NEXT_PUBLIC_API_URL` to backend Railway deployment URL
- [ ] Verify Supabase keys are correct

### 3. Verification Steps
- [ ] Check backend logs for OpenAI initialization success
- [ ] Test frontend-backend API connectivity
- [ ] Verify authentication flow works
- [ ] Test job extraction functionality

## Security Notes
- ✅ All `NEXT_PUBLIC_*` variables are safe to expose (they're client-side)
- ⚠️ Never put backend secrets in frontend environment variables
- 🔐 Ensure `SECRET_KEY` is a strong, unique 32+ character string
- 🔐 Keep `SUPABASE_JWT_SECRET` private (backend only)

## Testing Checklist
- [ ] Backend starts without errors
- [ ] Frontend connects to backend API
- [ ] OpenAI features work (resume analysis, job matching)
- [ ] Supabase authentication works
- [ ] Google OAuth integration functional
- [ ] Job extraction from URLs successful