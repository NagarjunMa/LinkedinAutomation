# 🚀 Production Environment Variables Guide

This guide provides a clean, comprehensive list of environment variables needed for deploying JobFlow Pro to Railway with Supabase integration.

## 📋 **Required Environment Variables**

### **🔐 Core Security (REQUIRED)**
```bash
# Strong secret key for JWT and encryption (32+ characters)
SECRET_KEY=your-super-secure-secret-key-at-least-32-chars-long

# Environment mode
ENVIRONMENT=production
DEBUG=false
```

### **🗃️ Database & Supabase (REQUIRED)**
```bash
# Supabase PostgreSQL connection
SQLALCHEMY_DATABASE_URI=postgresql://postgres:[your-password]@db.[your-ref].supabase.co:5432/postgres

# Supabase authentication
SUPABASE_URL=https://[your-project-ref].supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
```

### **🤖 AI Services (REQUIRED for AI features)**
```bash
# OpenAI for resume analysis and job matching
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=4000
```

### **🌐 CORS & Security**
```bash
# Frontend URL for CORS
CORS_ORIGINS=https://your-frontend-domain.railway.app

# Project metadata
PROJECT_NAME=JobFlow Pro - Production
API_V1_STR=/api/v1
```

## 📋 **Optional Environment Variables**

### **📧 Email Services (Recommended)**
```bash
# Resend for transactional emails
RESEND_API_KEY=your-resend-api-key
MAIL_FROM=noreply@yourdomain.com
MAIL_FROM_NAME=JobFlow Pro
```

### **📬 Google OAuth (for Email Agent)**
```bash
# Only needed if using Gmail integration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-backend.railway.app/api/v1/auth/google/callback
```

### **⚙️ Feature Configuration**
```bash
# Feature toggles (default: true)
ENABLE_AI_FEATURES=true
ENABLE_EMAIL_SCANNING=true
ENABLE_ANALYTICS=true

# Email processing settings
EMAIL_SYNC_FREQUENCY_MINUTES=15
EMAIL_CONFIDENCE_THRESHOLD=0.8
AUTO_UPDATE_THRESHOLD=0.85
```

### **📊 Logging & Monitoring**
```bash
# Production logging
LOG_LEVEL=INFO

# File upload limits
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
UPLOAD_DIR=uploads
```

---

## 🚀 **Railway Deployment Setup**

### **Step 1: Create Railway Project**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and create project
railway login
railway init
```

### **Step 2: Deploy Backend First**
```bash
# From project root, deploy backend
cd backend
railway up

# Note the deployed URL (e.g., https://backend-production-xyz.railway.app)
```

### **Step 3: Deploy Frontend**
```bash
# From project root, deploy frontend
cd frontend
railway up

# Note the deployed URL (e.g., https://frontend-production-abc.railway.app)
```

### **Step 4: Configure Google OAuth (Required for Gmail integration)**

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create/Select Project** → APIs & Services → Credentials
3. **Create OAuth 2.0 Client ID:**
   - Application type: Web application
   - Name: JobFlow Pro Production
   - **Authorized redirect URIs:**
     ```
     https://YOUR-BACKEND-URL.railway.app/api/v1/auth/google/callback
     ```
   - Replace `YOUR-BACKEND-URL` with your actual Railway backend URL

### **Step 5: Set Environment Variables in Railway**
Go to Railway dashboard → Your Project → Variables tab:

**Backend Service Variables:**
```bash
SECRET_KEY=your-generated-secret-key-here
ENVIRONMENT=production
DEBUG=false
SQLALCHEMY_DATABASE_URI=postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
SUPABASE_URL=https://[your-ref].supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
OPENAI_API_KEY=your-openai-key
CORS_ORIGINS=https://YOUR-FRONTEND-URL.railway.app
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://YOUR-BACKEND-URL.railway.app/api/v1/auth/google/callback
```

**Frontend Service Variables:**
```bash
NEXT_PUBLIC_API_URL=https://YOUR-BACKEND-URL.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://[your-ref].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NODE_ENV=production
```

### **Step 3: Generate Secure Values**

**Generate a strong SECRET_KEY:**
```bash
# Use one of these methods:
python -c "import secrets; print(secrets.token_urlsafe(32))"
# OR
openssl rand -base64 32
```

**Get your Supabase credentials:**
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Project Settings → API
3. Copy: URL, anon key, JWT secret
4. Database Settings → Connection string

---

## ✅ **Validation Checklist**

Before deploying, ensure you have:

- [ ] **SECRET_KEY** is 32+ characters and unique
- [ ] **SQLALCHEMY_DATABASE_URI** connects to your Supabase database
- [ ] **SUPABASE_URL** is your correct project URL
- [ ] **SUPABASE_ANON_KEY** is valid
- [ ] **SUPABASE_JWT_SECRET** is set
- [ ] **OPENAI_API_KEY** is valid (if AI features enabled)
- [ ] **CORS_ORIGINS** includes your frontend domain

---

## 🔧 **Environment Variables by Service**

### **Frontend (Next.js)**
```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://[your-ref].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NODE_ENV=production
```

### **Backend (FastAPI)**
```bash
# Use all variables from sections above
# Backend needs all configuration variables
```

---

## 🚨 **Security Best Practices**

1. **Never commit real API keys** to version control
2. **Use Railway's environment variables** - never hardcode secrets
3. **Rotate keys regularly** in production
4. **Use strong, unique SECRET_KEY** (32+ characters)
5. **Keep SUPABASE_JWT_SECRET private** - never expose in frontend
6. **Set DEBUG=false** in production
7. **Use HTTPS URLs** for all external services

---

## 📋 **GitHub Repository Configuration**

### **Required Files for Railway Auto-Deploy:**

1. **Backend Dockerfile** (already exists at `/backend/Dockerfile`)
2. **Frontend Configuration** (uses Next.js auto-detection)
3. **Environment Variables** (set in Railway dashboard)

### **Setting up GitHub Integration:**

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Production ready with Supabase caching"
   git push origin main
   ```

2. **Connect to Railway:**
   - Go to Railway dashboard → New Project → Deploy from GitHub repo
   - Select your repository
   - Railway will auto-detect both frontend and backend services

3. **Configure Build Settings:**
   - **Backend:** Automatically detected via Dockerfile
   - **Frontend:** Automatically detected as Next.js app
   - **Root Directory:** Set to `backend/` for backend service, `frontend/` for frontend service

### **Auto-Deploy Setup:**
- Railway automatically redeploys when you push to main branch
- Environment variables persist across deployments
- Both services will get unique URLs

---

## 🔧 **Railway Project Structure**

Your Railway project will have 2 services:
```
JobFlow Pro Project
├── Backend Service (FastAPI)
│   ├── URL: https://backend-production-xyz.railway.app
│   ├── Build: Dockerfile
│   └── Root: backend/
└── Frontend Service (Next.js)
    ├── URL: https://frontend-production-abc.railway.app
    ├── Build: Auto-detected
    └── Root: frontend/
```

---

## 🔍 **Troubleshooting**

### **Common Issues:**

**"SQLALCHEMY_DATABASE_URI is required"**
- Ensure your Supabase connection string is correct
- **For Railway: Use Connection Pooling (FREE)** instead of Direct connection
- Format: `postgresql://postgres.YOUR_REF:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres`

**"Network is unreachable" or IPv6 connection errors**
- Use Supabase **Connection Pooler** (port 6543) instead of Direct connection (port 5432)
- Go to Supabase → Settings → Database → Connection pooling section
- Copy the pooler URI - it resolves to IPv4 automatically (FREE)
- **Don't** pay $25/month for IPv4 add-on when pooler works for free!

**"CORS errors in frontend"**
- Add your frontend URL to `CORS_ORIGINS`
- Use exact domain: `https://your-app.railway.app`

**"OpenAI API errors"**
- Verify `OPENAI_API_KEY` is valid and has credits
- Set `ENABLE_AI_FEATURES=false` to disable if not needed

**"500 Internal Server Error"**
- Check Railway logs for specific error messages
- Verify all required environment variables are set
- Ensure Supabase credentials are correct

---

## 📞 **Need Help?**

- Check Railway logs: `railway logs`
- Validate config: Use the built-in config validation
- Test locally first: `python -c "from app.core.config import validate_production_config; print(validate_production_config())"`