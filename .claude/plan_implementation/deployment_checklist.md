# Railway Deployment Checklist

## Critical Issues Fixed ✅

### 1. Environment Variable Naming
**Issue:** Backend code expects `OPENAI_API_KEY` but Railway was configured with `OPENAPI_KEY`
**Status:** ✅ RESOLVED
**Action Required:** Update Railway backend deployment:
```bash
# Remove this:
OPENAPI_KEY=sk-...

# Add this:
OPENAI_API_KEY=sk-...
```

## Backend Railway Environment Variables

### ✅ Currently Set (from screenshot)
```bash
GOOGLE_CLIENT_ID=*******
GOOGLE_CLIENT_SECRET=*******
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

### ❌ Issues to Fix
1. **CRITICAL:** Rename `OPENAPI_KEY` → `OPENAI_API_KEY`
2. **Remove:** Frontend variables from backend (not needed):
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_SUPABASE_URL`

### ➕ Additional Variables Needed
```bash
# Application Settings
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://your-frontend-railway-url.railway.app

# Playwright (for job extraction)
PLAYWRIGHT_BROWSERS_PATH=/app/browsers
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Optional: Enhanced logging
LOG_LEVEL=INFO
```

## Frontend Railway Environment Variables

### ❌ Currently Missing (ADD ALL OF THESE)
The frontend Railway deployment appears to have NO environment variables set.

**Required Frontend Variables:**
```bash
NEXT_PUBLIC_API_URL=https://your-backend-railway-url.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://fecoflibopgxliexcdbg.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZlY29mbGlib3BneGxpZXhjZGJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk0MDU5MDQsImV4cCI6MjA2NDk4MTkwNH0.sgOtVlM2Eom1McYT9DAMc0pKPLND-s4t99LelA5E--Y
NEXT_PUBLIC_GOOGLE_CLIENT_ID=706462409929-gtcraefuvdqqpjmlbt0f6ko1djf1aaij.apps.googleusercontent.com
```

## Pre-Deployment Actions

### Backend Changes ✅
- [x] Fixed environment variable naming inconsistency
- [x] Updated OpenAI client to AsyncOpenAI
- [x] Enhanced logging for Railway
- [x] Added Playwright job extraction
- [x] Implemented individual education editing
- [x] Removed mock data fallbacks

### Frontend Changes ✅
- [x] Removed mock data from components
- [x] Enhanced profile editing features
- [x] Improved validation and error handling
- [x] Added skills autocomplete
- [x] Fixed data persistence issues

## Deployment Verification Steps

### 1. Backend Health Check
```bash
curl https://your-backend-railway-url.railway.app/health
# Should return: {"status": "healthy"}
```

### 2. OpenAI Integration Test
```bash
curl https://your-backend-railway-url.railway.app/api/v1/jobs/domain-info?url=https://linkedin.com/jobs/123
# Should return domain classification without errors
```

### 3. Frontend-Backend Connectivity
- Visit frontend URL
- Check browser console for API connection errors
- Test user registration/login flow
- Verify job extraction works

### 4. Feature Testing
- [ ] User registration with Supabase
- [ ] Profile creation and editing
- [ ] Individual education entry editing
- [ ] Job extraction from LinkedIn URL
- [ ] Job extraction from Indeed URL
- [ ] Skills autocomplete functionality
- [ ] No mock data visible anywhere

## Post-Deployment Monitoring

### Critical Logs to Monitor
```bash
# Backend logs to check:
- OpenAI API initialization
- Database connections
- Playwright browser launches
- Job extraction success rates

# Frontend logs to check:
- API connectivity
- Authentication flow
- Component rendering without errors
```

### Success Metrics
- OpenAI extraction success rate > 80%
- Frontend loads without console errors
- All user flows work end-to-end
- No "localhost" references in production

## Rollback Plan
If deployment fails:
1. Revert environment variable changes
2. Check Railway logs for specific errors
3. Test individual services (database, OpenAI, Supabase)
4. Verify network connectivity between services

## Security Verification
- [ ] No secrets exposed in frontend bundle
- [ ] CORS configured for production domains only
- [ ] JWT tokens properly validated
- [ ] Environment variables correctly scoped
- [ ] Supabase RLS policies active

## Performance Checklist
- [ ] Playwright browsers properly cached
- [ ] Database connections pooled
- [ ] API response times < 5 seconds
- [ ] Frontend bundle size reasonable
- [ ] No memory leaks in long-running processes