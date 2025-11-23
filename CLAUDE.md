# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JobFlow Pro is a comprehensive full-stack AI-powered job search automation platform built with Next.js 14 (frontend) and FastAPI (backend). The platform helps students and job seekers transform chaotic job searching into an organized, intelligent system with AI-powered features for job extraction, resume evaluation, email automation, and networking.

## Development Commands

### Frontend (Next.js 14)
```bash
cd frontend
npm run dev          # Start development server (localhost:3000)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run test:e2e     # Run Playwright E2E tests
npm run test:e2e:ui  # Run Playwright tests with UI
npm run test:e2e:debug # Debug Playwright tests
```

### Backend (FastAPI/Python)
```bash
cd backend
# Development (requires Python 3.9+ and virtual environment)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Background worker (Celery)
celery -A app.core.celery_app worker --loglevel=info
```

### Docker Development Environment
```bash
docker-compose up -d     # Start all services (frontend, backend, DB, Redis, Celery)
docker-compose logs -f   # View logs
docker-compose down      # Stop all services
```

### Database Operations
```bash
cd backend
# Database migrations (Alembic)
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Architecture & Key Components

### Frontend Architecture (Next.js 14 App Router)
- **Framework**: Next.js 14 with App Router pattern (`frontend/app/` directory structure)
- **UI Components**: Shadcn UI + Radix UI primitives with Tailwind CSS
- **State Management**: React Context + TanStack Query for server state
- **Authentication**: Supabase Auth integration with JWT tokens
- **Type Safety**: Full TypeScript implementation with Zod validation

### Backend Architecture (FastAPI)
- **Framework**: FastAPI with async/await support
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Database**: PostgreSQL with Redis for caching and task queues
- **Background Tasks**: Celery for async processing (email classification, AI tasks)
- **Security**: Multi-layer middleware stack with rate limiting, CORS, and security headers
- **Validation**: Comprehensive Zod schema validation with type-safe form handling
- **Logging**: Railway-optimized structured JSON logging for production debugging

### Core Service Architecture

#### 1. Job Management System (`backend/app/services/`)
- **URL Job Extractor** (`url_job_extractor.py`): Extracts job details from LinkedIn, Indeed, and company sites using Jina AI Reader
- **Smart Job Scorer** (`smart_job_scorer.py`): AI-powered compatibility scoring based on user profiles
- **Job Search Service**: Advanced filtering and search across extracted jobs

#### 2. AI Resume Evaluation (`backend/app/services/agentic_resume_evaluator.py`)
- **Multi-Agent System**: Specialized AI agents for different evaluation aspects
- **ATS Optimization**: Ensures resumes pass Applicant Tracking Systems
- **Score Tracking**: Monitors improvement with detailed feedback

#### 3. Email Automation (`backend/app/services/gmail_service.py`)
- **Gmail OAuth Integration**: Secure email access with proper scopes
- **Email Classification** (`email_classification_service.py`): AI-powered job-related email detection
- **Application Progress Tracking**: Status updates from email content

#### 4. Referral & Networking System
- **AI Email Generator** (`referral_email_generator.py`): Personalized referral requests
- **Contact Discovery** (`contact_discovery.py`): Professional network organization

#### 5. Educational Information System
- **Education Service** (`education_service.py`): Comprehensive education data management
- **AI-Powered Job Matching**: Education-job compatibility scoring with GPT-4o-mini
- **Skills Integration**: Technical skills extraction and relevance calculation

### Database Schema Design
Key models in `backend/app/models/`:
- **JobListing**: Core job information with AI compatibility scores
- **UserProfile**: AI-extracted user profiles and preferences
- **JobApplication**: Application tracking with status management
- **Resume/ResumeEvaluation**: Resume storage and AI evaluation results
- **EmailEvent**: Gmail integration and email classification
- **ReferralContact**: Professional networking and referral management
- **EducationRecord**: Academic institution records with AI relevance scoring
- **Certification**: Professional certifications with skills validation
- **OnlineCourse**: Online learning records and completion tracking
- **AcademicProject**: Project portfolio with technical skills gained

## API Architecture

All endpoints follow RESTful conventions under `/api/v1/`:

- **Job Management** (`/api/v1/jobs/`): Job extraction, search, CRUD operations
- **Resume Evaluation** (`/api/v1/resumes/`): AI-powered resume analysis
- **Referral System** (`/api/v1/referral/`): Networking and email generation
- **Email Agent** (`/api/v1/email-agent/`): Gmail integration and processing
- **Analytics** (`/api/v1/analytics/`): Dashboard data and insights
- **Activity Tracking** (`/api/v1/activity/`): User engagement metrics
- **Education Management** (`/api/v1/education/`): Educational information CRUD and AI analysis
- **User Profiles** (`/api/v1/user-profiles/`): Enhanced profile management with validation

## Environment Configuration

### Required Environment Variables

**Frontend** (`.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

**Backend** (`.env`):
```
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=linkedin_jobs

# Redis
REDIS_HOST=localhost

# AI Services
OPENAI_API_KEY=your_openai_api_key

# Email Integration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Authentication
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## Development Patterns

### Frontend Patterns
- **Components**: Use Shadcn UI components in `frontend/components/ui/`
- **Pages**: App Router structure in `frontend/app/` with page.tsx and layout.tsx
- **State Management**: Use React Context for global state, TanStack Query for server state
- **Forms**: React Hook Form + Zod validation pattern with custom validation hooks
- **Styling**: Tailwind CSS with custom design tokens for fonts (Clash Display, Stardom, Urbanist)
- **Skills Input**: Tag-based autocomplete with 200+ predefined skills database
- **Validation**: Real-time and on-blur validation with comprehensive error handling

### Backend Patterns
- **Service Layer**: Business logic in `backend/app/services/`
- **Repository Pattern**: Data access through SQLAlchemy models
- **Dependency Injection**: FastAPI dependency system for database sessions
- **Background Tasks**: Use Celery for long-running operations (AI processing, email classification)
- **Error Handling**: Structured exceptions with proper HTTP status codes

## Security Implementation

### Production Security Features
- **Rate Limiting**: Configurable per-minute/hour limits with burst protection
- **Request Validation**: Input sanitization and size limits (50MB for resume uploads)
- **Security Headers**: CSP, HSTS, X-Frame-Options, XSS protection
- **CORS Configuration**: Environment-specific origin allowlists
- **Authentication**: JWT tokens with Supabase integration

### Security Middleware Stack
Located in `backend/app/middleware/security.py` (currently simplified in production):
- Rate limiting by IP and user
- Request validation and sanitization
- Security headers injection
- Request/response logging (development only)

## AI Integration

### OpenAI Integration
- **Client**: Modern AsyncOpenAI client with async/await patterns
- **Model**: GPT-4o-mini for cost-effective AI processing
- **Services**: Job scoring, resume evaluation, email classification, referral generation, education matching
- **Configuration**: Centralized in `backend/app/core/config.py` with Railway deployment validation
- **Monitoring**: Cost tracking and token usage logging in `backend/app/core/enhanced_logging.py`
- **Error Handling**: Comprehensive retry logic and structured error logging

### Jina AI Reader
- **Purpose**: Intelligent web scraping for job extraction
- **Usage**: Converts job posting URLs to structured data

## Testing & Quality Assurance

### Frontend Testing
- **Framework**: Playwright for E2E testing
- **Test Location**: `frontend/tests/` (implied by package.json scripts)
- **Commands**: `npm run test:e2e` for headless, `npm run test:e2e:ui` for interactive

### Backend Testing
- **Framework**: Standard Python testing patterns expected
- **Test Location**: `backend/tests/` directory exists

## Deployment Architecture

### Development
- **Docker Compose**: Multi-service setup with PostgreSQL, Redis, Celery worker
- **Hot Reload**: Enabled for both frontend and backend
- **Database**: Local PostgreSQL with volume persistence

### Production
- **Platform**: Designed for Railway/Render deployment
- **Database**: Supabase PostgreSQL with connection pooling
- **Monitoring**: Health endpoints at `/health` and `/metrics`
- **Environment Detection**: Automatic production/development mode switching

## Common Development Tasks

### Adding New API Endpoints
1. Define route in `backend/app/api/v1/endpoints/`
2. Add business logic in `backend/app/services/`
3. Update database models in `backend/app/models/` if needed
4. Add frontend integration in appropriate `frontend/app/` route

### Database Schema Changes
1. Modify models in `backend/app/models/`
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Review and edit migration file if needed
4. Apply: `alembic upgrade head`

### Adding New AI Features
1. Implement service in `backend/app/services/`
2. Use existing OpenAI configuration from `app.core.config`
3. Add background task support via Celery if needed
4. Integrate with frontend using TanStack Query patterns

### Adding Educational Features
1. Define education models in `backend/app/models/education.py`
2. Create Pydantic schemas in `backend/app/schemas/education.py`
3. Implement service logic in `backend/app/services/education_service.py`
4. Add API endpoints in `backend/app/api/v1/endpoints/education.py`
5. Create frontend components with validation using patterns from `education-form.tsx`

## Code Quality Standards

- **TypeScript**: Full type coverage in frontend
- **Python Type Hints**: Use throughout backend
- **Error Handling**: Structured exception handling with proper HTTP status codes
- **Logging**: Enhanced logging system in `backend/app/core/enhanced_logging.py`
- **Security**: Never commit API keys, use environment variables exclusively
- **Validation**: Use Zod schemas for frontend validation with backend Pydantic integration
- **Form Patterns**: Follow validation hooks pattern from `frontend/src/hooks/use-form-validation.ts`

## Development Context Tracking

### .claude Folder Structure
Development history and context is tracked in the `.claude/` folder:
- **development-log.md**: Chronological development history and session summaries
- **architecture-decisions.md**: Technical decision documentation and rationale
- **bug-fixes.md**: Issue resolution tracking with root cause analysis
- **feature-implementations.md**: Detailed feature documentation and implementation guides

This structure ensures continuity across development sessions and provides comprehensive context for future development work.