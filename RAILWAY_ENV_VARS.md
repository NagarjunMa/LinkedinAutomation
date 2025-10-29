# 🚀 Railway Environment Variables Setup

## **Critical Environment Variables for Production**

Copy these environment variables to your Railway services:

### **Backend Service Environment Variables:**

```bash
# Database (Railway will provide these)
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# Security
SECRET_KEY=your-super-secret-key-min-32-chars-production
ENVIRONMENT=production
DEBUG=false

# Supabase Authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret

# AI Services
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# External APIs
APOLLO_API_KEY=your-apollo-api-key
ARCADE_API_KEY=your-arcade-api-key

# Email Service
RESEND_API_KEY=your-resend-api-key

# Google OAuth (for email agent)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# CORS and Security
ALLOWED_HOSTS=your-backend-domain.railway.app
CORS_ORIGINS=https://your-frontend-domain.railway.app
```

### **Frontend Service Environment Variables:**

```bash
# API Connection
NEXT_PUBLIC_API_URL=https://your-backend.railway.app

# Supabase (Public keys only)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key

# Google OAuth
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id

# Production Settings
NODE_ENV=production
```

## **🔧 Railway Setup Steps:**

1. **Add PostgreSQL Database:**
   - Go to Railway dashboard
   - "Add Service" → "Database" → "PostgreSQL"
   - Copy the DATABASE_URL

2. **Add Redis Cache:**
   - "Add Service" → "Database" → "Redis"
   - Copy the REDIS_URL

3. **Configure Backend Variables:**
   - Go to backend service → "Variables"
   - Add all backend environment variables above
   - Use `${{Postgres.DATABASE_URL}}` syntax for database URLs

4. **Configure Frontend Variables:**
   - Go to frontend service → "Variables"
   - Add all frontend environment variables above
   - Use `${{backend.url}}` for NEXT_PUBLIC_API_URL

5. **Custom Domains (Optional):**
   - Add custom domains in Railway settings
   - Update CORS_ORIGINS and API URLs accordingly

## **🔍 Environment Variable Validation:**

After setting variables, check the deployment logs for:
- ✅ "All critical imports successful"
- ✅ "Database connection established"
- ✅ "Redis connection established"
- ✅ "FastAPI app started successfully"

## **🚨 Security Notes:**

- **Never commit real API keys to git**
- **Use strong, unique SECRET_KEY (32+ characters)**
- **Keep SUPABASE_SERVICE_ROLE_KEY secret**
- **Set DEBUG=false in production**
- **Use HTTPS URLs for all external services**

## **📝 Quick Copy Template:**

**Backend:**
```
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
SECRET_KEY=REPLACE_WITH_STRONG_SECRET_KEY
ENVIRONMENT=production
DEBUG=false
SUPABASE_URL=REPLACE_WITH_YOUR_SUPABASE_URL
SUPABASE_ANON_KEY=REPLACE_WITH_YOUR_ANON_KEY
OPENAI_API_KEY=REPLACE_WITH_YOUR_OPENAI_KEY
```

**Frontend:**
```
NEXT_PUBLIC_API_URL=${{backend.url}}
NEXT_PUBLIC_SUPABASE_URL=REPLACE_WITH_YOUR_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY=REPLACE_WITH_YOUR_ANON_KEY
NODE_ENV=production
```