# 🤖 AI-Powered Job Matching System

## Overview

This system transforms your LinkedIn automation platform into a personalized AI job matching service for students and new graduates. Instead of manual search queries, the system:

1. **AI Resume Parsing** - Extracts structured data from resumes using GPT-4o-mini
2. **Profile-Based Filtering** - Matches jobs based on skills, experience, and preferences  
3. **AI Job Scoring** - Provides compatibility scores with detailed reasoning
4. **Daily Digest Generation** - Creates personalized job recommendations

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Resume        │    │  Job Fetching   │    │  AI Scoring     │
│   Parser        │───→│  (RSS Feeds)    │───→│  Engine         │
│   (GPT-4o-mini) │    │                 │    │  (GPT-4o-mini)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  User Profiles  │    │  Job Database   │    │  Job Scores     │
│  Database       │    │                 │    │  Database       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Daily Digest   │    │  API Endpoints  │
                       │  Generator      │    │  & Frontend     │
                       └─────────────────┘    └─────────────────┘
```

## 🗄️ Database Models

### UserProfile
```sql
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Personal Information
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    location VARCHAR(255),
    work_authorization VARCHAR(100),
    
    -- Professional Summary
    years_of_experience FLOAT DEFAULT 0.0,
    career_level VARCHAR(50),
    professional_summary TEXT,
    
    -- Skills (JSON Arrays)
    programming_languages JSON,
    frameworks_libraries JSON,
    tools_platforms JSON,
    soft_skills JSON,
    
    -- Experience
    job_titles JSON,
    companies JSON,
    industries JSON,
    experience_descriptions JSON,
    
    -- Education
    degrees JSON,
    institutions JSON,
    graduation_years JSON,
    relevant_coursework JSON,
    
    -- Preferences
    desired_roles JSON,
    preferred_locations JSON,
    salary_range_min INTEGER,
    salary_range_max INTEGER,
    job_types JSON,
    company_size_preference JSON,
    
    -- AI Insights
    ai_profile_summary TEXT,
    ai_strengths JSON,
    ai_improvement_areas JSON,
    ai_career_advice TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_resume_upload TIMESTAMP
);
```

### JobScore
```sql
CREATE TABLE job_scores (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) REFERENCES user_profiles(user_id),
    job_id INTEGER REFERENCES job_listings(id),
    
    -- Scoring
    compatibility_score FLOAT NOT NULL,
    confidence_score FLOAT DEFAULT 0.0,
    
    -- AI Reasoning
    ai_reasoning TEXT,
    match_factors JSON,
    mismatch_factors JSON,
    
    -- Detailed Breakdown
    skills_match_score FLOAT DEFAULT 0.0,
    location_match_score FLOAT DEFAULT 0.0,
    experience_match_score FLOAT DEFAULT 0.0,
    salary_match_score FLOAT DEFAULT 0.0,
    culture_match_score FLOAT DEFAULT 0.0,
    
    -- User Actions
    user_interested BOOLEAN,
    user_applied BOOLEAN DEFAULT FALSE,
    user_feedback VARCHAR(20),
    
    -- Metadata
    scored_at TIMESTAMP DEFAULT NOW(),
    score_version VARCHAR(10) DEFAULT '1.0'
);
```

### DailyDigest
```sql
CREATE TABLE daily_digests (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) REFERENCES user_profiles(user_id),
    digest_date DATE NOT NULL,
    
    -- Content
    digest_title VARCHAR(255),
    digest_summary TEXT,
    digest_html TEXT,
    
    -- Job Data
    top_jobs JSON,
    total_new_jobs INTEGER DEFAULT 0,
    total_matches INTEGER DEFAULT 0,
    
    -- Market Insights
    market_trends JSON,
    skill_recommendations JSON,
    
    -- Delivery Status
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    email_opened BOOLEAN DEFAULT FALSE,
    email_clicked BOOLEAN DEFAULT FALSE,
    
    -- User Engagement
    user_viewed BOOLEAN DEFAULT FALSE,
    user_viewed_at TIMESTAMP,
    jobs_clicked JSON,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    generation_time_seconds FLOAT
);
```

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# OpenAI Configuration
OPENAPI_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=1000

# Database (existing)
DATABASE_URL=postgresql://user:password@localhost/dbname

# Redis (existing)
REDIS_URL=redis://localhost:6379
```

### Cost Optimization

**GPT-4o-mini Pricing (as of 2024):**
- Input: $0.000150 per 1K tokens
- Output: $0.000600 per 1K tokens

**Estimated Daily Costs for 100 Users:**
- Resume parsing: ~$0.01/user = $1.00/day
- Job scoring: ~$0.30/day total
- Daily digests: ~$0.016/day total
- **Total: ~$1.32/day for 100 active users**

## 📡 API Endpoints

### Profile Management

```bash
# Upload Resume
POST /api/v1/profiles/upload-resume/{user_id}
Content-Type: multipart/form-data
Body: file=resume.pdf

# Parse Resume Text
POST /api/v1/profiles/parse-text/{user_id}
Content-Type: application/x-www-form-urlencoded
Body: resume_text="John Smith\nSoftware Engineer..."

# Get User Profile
GET /api/v1/profiles/profile/{user_id}

# Update Profile
PUT /api/v1/profiles/profile/{user_id}
Content-Type: application/json
Body: {
  "personal_info": {
    "full_name": "John Smith",
    "location": "San Francisco, CA"
  },
  "preferences": {
    "desired_roles": ["Senior Software Engineer"],
    "salary_range": {"min": 120000, "max": 160000}
  }
}
```

### Job Matching

```bash
# Get Job Matches
GET /api/v1/profiles/matches/{user_id}?limit=10&min_score=70.0

# Score New Jobs (Manual Trigger)
POST /api/v1/profiles/score-jobs/{user_id}?job_limit=50&days_back=1

# List All Users (Admin)
GET /api/v1/profiles/users?skip=0&limit=100
```

## 🔄 Automated Workflows

### Celery Scheduled Tasks

```python
# 1. Fetch Jobs (Every 60 minutes)
'refresh-all-searches': {
    'task': 'app.tasks.search_tasks.refresh_all_active_searches',
    'schedule': 3600.0,
}

# 2. Score Jobs for All Users (Every 60 minutes, offset)
'ai-job-scoring': {
    'task': 'app.tasks.search_tasks.score_jobs_for_all_users',
    'schedule': 3600.0,
}

# 3. Generate Daily Digests (Once per day)
'daily-digests': {
    'task': 'app.tasks.search_tasks.generate_daily_digests',
    'schedule': 86400.0,
}

# 4. Cleanup Old Scores (Weekly)
'cleanup-old-scores': {
    'task': 'app.tasks.search_tasks.cleanup_old_job_scores',
    'schedule': 604800.0,
}
```

### Daily Workflow

```
06:00 AM - Fetch new jobs from RSS feeds
06:30 AM - AI scoring for all users (new jobs only)
07:00 AM - Generate daily digests
07:30 AM - Send digest emails
```

## 🧪 Testing

### Run Test Suite

```bash
cd backend
python test_ai_system.py
```

### Manual API Testing

```bash
# Test resume parsing
curl -X POST "http://localhost:8000/api/v1/profiles/parse-text/test_user" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "resume_text=John Smith\nSoftware Engineer\nPython, JavaScript"

# Test job matching
curl -X GET "http://localhost:8000/api/v1/profiles/matches/test_user?limit=5&min_score=70"

# Test job scoring
curl -X POST "http://localhost:8000/api/v1/profiles/score-jobs/test_user?job_limit=10"
```

## 🚀 Deployment Steps

### 1. Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start services
uvicorn app.main:app --host 0.0.0.0 --port 8000
celery -A app.core.celery_app worker --loglevel=info
celery -A app.core.celery_app beat --loglevel=info
```

### 2. Environment Configuration

```bash
# Set OpenAI API key
export OPENAPI_KEY="sk-your-key-here"

# Verify configuration
python -c "from app.core.config import settings; print(f'API Key: {settings.OPENAPI_KEY[:10]}...')"
```

### 3. Initial Data Setup

```bash
# Test the system
python test_ai_system.py

# Trigger job refresh
curl -X POST "http://localhost:8000/api/v1/jobs/refresh"

# Create test user profile
curl -X POST "http://localhost:8000/api/v1/profiles/parse-text/demo_user" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "resume_text=Demo User\nSoftware Developer\nPython, React, AWS"
```

## 📊 Monitoring & Analytics

### Key Metrics to Track

1. **System Performance**
   - Resume parsing success rate
   - AI API response times
   - Job scoring throughput

2. **User Engagement**
   - Profile creation rate
   - Job match click-through rates
   - Digest open rates

3. **AI Quality**
   - Average compatibility scores
   - User feedback on matches
   - False positive/negative rates

4. **Cost Management**
   - Daily OpenAI API costs
   - Tokens consumed per operation
   - Cost per user per day

### Logging

```python
# Check application logs
tail -f backend/logs/app.log

# Check Celery logs
tail -f backend/logs/celery.log

# Monitor AI service calls
grep "AI" backend/logs/app.log | tail -20
```

## 🛠️ Customization

### Adjust AI Prompts

Edit `backend/app/core/ai_service.py`:

```python
# Customize resume parsing prompt
prompt = f"""
Extract information from this resume...
Focus on: skills, experience, education, preferences
Return JSON format with specific structure...
"""

# Customize job scoring criteria
prompt = f"""
Score job compatibility from 0-100 considering:
1. Skills match (40% weight)
2. Experience level (30% weight)
3. Location preference (20% weight)
4. Salary alignment (10% weight)
"""
```

### Modify Scoring Thresholds

Edit `backend/app/services/job_scorer.py`:

```python
class JobScoringService:
    def __init__(self):
        self.min_score_threshold = 60.0  # Only store scores >= 60%
        self.max_concurrent_scoring = 5  # Limit concurrent AI calls
```

### Add New Profile Fields

1. Update database model in `backend/app/models/job.py`
2. Run migration: `alembic revision --autogenerate -m "Add new fields"`
3. Update API endpoints in `backend/app/api/v1/endpoints/profiles.py`
4. Modify AI prompts to extract new fields

## 🔒 Security Considerations

1. **API Key Management**
   - Never commit API keys to version control
   - Use environment variables or secure vaults
   - Rotate keys regularly

2. **Data Privacy**
   - Don't store actual resume files
   - Encrypt sensitive profile data
   - Implement data retention policies

3. **Rate Limiting**
   - Implement API rate limits
   - Monitor OpenAI API usage
   - Set spending alerts

4. **Input Validation**
   - Validate all user inputs
   - Sanitize resume text before AI processing
   - Limit file upload sizes

## 🆘 Troubleshooting

### Common Issues

**1. "OpenAI API key not set"**
```bash
# Check environment variable
echo $OPENAPI_KEY

# Set in current session
export OPENAPI_KEY="sk-your-key-here"

# Add to .env file
echo "OPENAPI_KEY=sk-your-key-here" >> .env
```

**2. "No jobs found for scoring"**
```bash
# Check if RSS feeds are working
curl http://localhost:8000/api/v1/jobs/

# Trigger job refresh
curl -X POST http://localhost:8000/api/v1/jobs/refresh
```

**3. "Database connection error"**
```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432

# Verify database URL
echo $DATABASE_URL
```

**4. "AI parsing returns empty data"**
- Check OpenAI API key validity
- Verify internet connection
- Review AI service logs for errors
- Test with simpler resume text

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run test script with verbose output
python test_ai_system.py

# Check specific component
python -c "
import asyncio
from app.core.ai_service import ai_service
result = asyncio.run(ai_service.parse_resume('John Smith\nSoftware Engineer'))
print(result)
"
```

## 🎯 Production Best Practices

1. **Scalability**
   - Use connection pooling for database
   - Implement Redis caching for frequent queries
   - Consider async workers for heavy AI operations

2. **Reliability**
   - Set up health checks for all services
   - Implement retry logic for AI API calls
   - Monitor and alert on failures

3. **Performance**
   - Batch AI operations when possible
   - Cache frequently accessed data
   - Use database indexes for common queries

4. **Cost Management**
   - Set OpenAI spending limits
   - Monitor token usage patterns
   - Optimize prompts for efficiency

---

## 🎉 Success Metrics

After successful deployment, you should see:

- ✅ Users can upload resumes and get structured profiles
- ✅ Jobs are automatically scored with AI reasoning
- ✅ Daily digests are generated and delivered
- ✅ System costs remain under $2/day for 100 users
- ✅ High user engagement with personalized matches

**The system is now a fully functional AI-powered job matching platform!** 🚀 