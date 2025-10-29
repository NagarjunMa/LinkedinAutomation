# 🚀 Railway Environment Variables Setup

## **Critical Environment Variables for Production**

Copy these environment variables to your Railway services:

### **Backend Service Environment Variables:**

```bash
# Database Configuration (Using Supabase PostgreSQL)
SQLALCHEMY_DATABASE_URI=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
POSTGRES_SERVER=db.[project-ref].supabase.co
POSTGRES_USER=postgres
POSTGRES_PASSWORD=[your-supabase-db-password]
POSTGRES_DB=postgres

# Redis Configuration (Railway Redis Service)
REDIS_HOST=${{Redis.REDIS_HOST}}
REDIS_PORT=${{Redis.REDIS_PORT}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}/0
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}/0

# Alternative: External Redis (if not using Railway Redis)
# REDIS_HOST=your-redis-host.com
# REDIS_PORT=6379
# CELERY_BROKER_URL=redis://your-redis-host.com:6379/0
# CELERY_RESULT_BACKEND=redis://your-redis-host.com:6379/0

# Security
SECRET_KEY=your-super-secret-key-min-32-chars-production
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# Supabase Authentication (CRITICAL - App won't start without these)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret

# AI Services (CRITICAL - OpenAI required)
OPENAPI_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=4000

# Email Service
RESEND_API_KEY=your-resend-api-key
MAIL_FROM=noreply@yourdomain.com
MAIL_FROM_NAME=JobFlow Pro

# Google OAuth (for email agent)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-backend.railway.app/api/v1/auth/google/callback

# CORS and Security
CORS_ORIGINS=https://your-frontend.railway.app
PROJECT_NAME=JobFlow Pro Production

# Optional Configuration
EMAIL_CLASSIFICATION_MODEL=gpt-4o-mini
EMAIL_SYNC_FREQUENCY_MINUTES=15
EMAIL_CONFIDENCE_THRESHOLD=0.8
AUTO_UPDATE_THRESHOLD=0.85
DEBUG_EMAIL_PROCESSING=false
LOG_LEVEL=INFO
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

## **🔍 Critical Deployment Steps:**

### **1. FIRST - Add Database Services:**
- Add PostgreSQL database service in Railway
- Add Redis service in Railway
- Copy the generated connection URLs

### **2. SECOND - Set Environment Variables:**
- Go to backend service → Variables tab
- Add ALL variables from the template above
- Replace placeholder values with your actual API keys

### **3. CRITICAL Variables to Set BEFORE Deployment:**
```bash
# These MUST be set or app will fail to start:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-actual-anon-key
OPENAPI_KEY=your-actual-openai-key
SQLALCHEMY_DATABASE_URI=${{Postgres.DATABASE_URL}}
```

### **4. Environment Variable Validation:**
After deployment, check logs for:
- ✅ "All critical imports successful"
- ✅ "Database connection established"
- ✅ "Redis connection established"
- ✅ "FastAPI app started successfully"

### **5. Common Deployment Failures:**
- ❌ Missing SUPABASE_URL → App won't start
- ❌ Missing OPENAPI_KEY → AI features fail
- ❌ Missing DATABASE_URL → Database errors
- ❌ Typo in variable names → Silent failures

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