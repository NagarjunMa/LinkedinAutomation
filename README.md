# JobFlow Pro - AI-Powered Job Search Automation Platform

A comprehensive full-stack application that transforms job searching from a chaotic process into an organized, AI-powered system. Built for students, new graduates, and job seekers who want to maximize their application success rate while saving 15+ hours weekly.

## 🚀 Core Features

### **Job Management & Extraction**
- 🔍 **Smart Job Extraction** - Extract job details from any job posting URL (LinkedIn, Indeed, company sites)
- 📊 **Interactive Dashboard** - Modern UI with activity calendar, progress tracking, and real-time analytics
- 📤 **Export Functionality** - CSV, Excel, and Google Sheets export for all job data
- 🤖 **AI-Powered Job Matching** - Smart compatibility scoring based on your profile and skills
- 🔍 **Advanced Search** - Search across all extracted jobs with filters and intelligent matching

### **Resume Optimization & Evaluation**
- 📄 **AI Resume Evaluation** - Multi-agent system providing recruiter-validated feedback
- 🎯 **ATS Optimization** - Ensure your resume passes Applicant Tracking Systems
- 📈 **Score Tracking** - Monitor improvement with detailed scoring breakdowns
- 🔧 **Actionable Feedback** - Specific, line-by-line recommendations for improvement
- 📊 **Market Positioning** - Understand your competitive level and salary range

### **Referral & Networking**
- 📧 **AI Referral Email Generator** - Generate personalized referral requests
- 👥 **Contact Management** - Organize and track your professional network
- 📝 **Email Templates** - Multiple templates for different relationship types
- 📊 **Referral Analytics** - Track response rates and success metrics
- 🔄 **Follow-up Automation** - Never miss important networking opportunities

### **Email & Application Tracking**
- 📧 **Gmail Integration** - Automatic job application email tracking with OAuth
- 📊 **Email Analytics** - Classify and analyze job-related communications
- 🔔 **Smart Notifications** - Get alerts for interview invitations and responses
- 📈 **Application Progress** - Track status from application to offer
- 🎯 **Response Tracking** - Monitor follow-ups and interview scheduling

### **Analytics & Intelligence**
- 📊 **Activity Calendar** - LeetCode-style consistency tracking for job search activities
- 📈 **Progress Analytics** - Detailed insights into your job search performance
- 🎯 **Market Intelligence** - Industry trends, skill demands, and salary insights
- 📊 **Success Metrics** - Track application rates, interview conversion, and offers
- 🔍 **Personalized Recommendations** - AI-driven suggestions for profile optimization

## 🛠️ Tech Stack

### **Frontend**
- **Next.js 14** (App Router) - Modern React framework with server-side rendering
- **TypeScript** - Type-safe development with enhanced IDE support
- **Tailwind CSS** - Utility-first CSS framework for rapid UI development
- **Shadcn UI** - Beautiful, accessible component library
- **Framer Motion** - Smooth animations and micro-interactions
- **React Context** - State management for user authentication and data
- **Custom Fonts** - Clash Display, Stardom, and Urbanist for premium typography

### **Backend**
- **Python FastAPI** - High-performance async web framework
- **SQLAlchemy** - Advanced ORM with database migrations
- **PostgreSQL** - Robust relational database for complex queries
- **Redis** - Caching and background task queue management
- **Celery** - Distributed task queue for background processing
- **Pydantic** - Data validation and serialization
- **Alembic** - Database migration management

### **AI & Machine Learning**
- **OpenAI GPT-4o-mini** - Advanced language model for job analysis and resume evaluation
- **Multi-Agent System** - Specialized AI agents for different evaluation aspects
- **Jina AI Reader** - Intelligent web scraping and content extraction
- **Custom AI Services** - Job matching, resume scoring, and email classification

### **Integrations**
- **Google OAuth 2.0** - Secure Gmail integration and user authentication
- **Gmail API** - Real-time email monitoring and classification
- **Apollo API** - Contact discovery and professional networking
- **Multiple Job Boards** - LinkedIn, Indeed, company career pages

### **DevOps & Deployment**
- **Docker** - Containerized application deployment
- **Docker Compose** - Multi-service development environment
- **Environment Management** - Secure configuration with .env files
- **Logging & Monitoring** - Comprehensive application monitoring

## Prerequisites

- Node.js 18+
- Python 3.9+
- PostgreSQL
- Redis
- Docker & Docker Compose
- Google Cloud Account (for Gmail OAuth)
- OpenAI API Key (for AI features)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/linkedin-automation.git
cd linkedin-automation
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Configure Google OAuth (for Gmail integration):
   - Follow the [Google OAuth Setup Guide](docs/GOOGLE_OAUTH_SETUP.md)
   - Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in your `.env` file

4. Configure OpenAI API (for AI features):
   - Get your API key from [OpenAI](https://platform.openai.com/)
   - Set `OPENAPI_KEY` in your `.env` file

5. Start the development environment:
```bash
docker-compose up -d
```

6. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Email Agent: http://localhost:3000/email-agent

## Development Setup

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Core Features

### 1. URL Job Extraction
Extract job details from any job posting URL:
- **LinkedIn Jobs**: Full job details extraction
- **Indeed Jobs**: Company, title, location, description
- **Generic Job Boards**: Smart parsing for various formats
- **Batch Processing**: Extract multiple URLs at once
- **On-Demand Processing**: No background fetching, jobs extracted when requested

### 2. AI Job Matching
Intelligent job scoring using OpenAI:
- **Resume Parsing**: Extract skills and experience from resumes
- **Smart Scoring**: Multi-factor compatibility scoring
- **Personalized Recommendations**: Based on user profiles and preferences

### 3. Email Automation
Gmail integration for application tracking:
- **OAuth 2.0**: Secure Gmail access
- **Email Classification**: AI-powered job-related email detection
- **Status Updates**: Automatic application status tracking
- **Follow-up Reminders**: Never miss important emails

### 4. Job Management
Comprehensive job tracking system:
- **Application Status**: Track from interested to hired
- **Notes & Follow-ups**: Keep track of communications
- **Export Options**: CSV, Excel, Google Sheets
- **Analytics**: Application success rates and insights

## 🔌 API Endpoints

### **Job Management**
- `POST /api/v1/jobs/extract-from-url` - Extract job details from any URL
- `POST /api/v1/jobs/extract-multiple-urls` - Batch job extraction
- `GET /api/v1/jobs/` - List and filter jobs with advanced search
- `GET /api/v1/jobs/{job_id}` - Get specific job details
- `PUT /api/v1/jobs/{job_id}` - Update job information
- `DELETE /api/v1/jobs/{job_id}` - Delete job record
- `GET /api/v1/jobs/user/{user_id}/applications` - Get user's job applications

### **Resume Evaluation**
- `POST /api/v1/resumes/upload` - Upload resume for AI analysis
- `POST /api/v1/resumes/{resume_id}/evaluate` - Start AI-powered resume evaluation
- `GET /api/v1/resumes/{resume_id}` - Get resume with evaluation results
- `GET /api/v1/resumes/{resume_id}/progress` - Track evaluation progress
- `DELETE /api/v1/resumes/{resume_id}` - Delete resume and evaluation data

### **Referral & Networking**
- `POST /api/v1/referral/generate-email` - Generate AI-powered referral emails
- `POST /api/v1/referral/create-request` - Create complete referral request
- `GET /api/v1/referral/contacts` - Get user's professional contacts
- `POST /api/v1/referral/send/{draft_id}` - Send referral email
- `GET /api/v1/referral/analytics` - Get referral performance metrics

### **Email & Communication**
- `POST /api/v1/email-agent/connect-gmail` - Connect Gmail account
- `POST /api/v1/email-agent/process/{user_id}` - Process and classify emails
- `GET /api/v1/email-agent/analytics/{user_id}` - Email analytics and insights
- `GET /api/v1/email-agent/events/{user_id}` - Get email events and responses

### **Analytics & Intelligence**
- `GET /api/v1/analytics/dashboard-all` - Complete analytics dashboard data
- `GET /api/v1/analytics/executive-dashboard` - Executive summary and KPIs
- `GET /api/v1/analytics/recommendations` - Personalized job search recommendations
- `GET /api/v1/analytics/tech-trends` - Industry trends and skill analysis

### **Activity Tracking**
- `POST /api/v1/activity/track` - Track user activities (job extractions, referrals)
- `GET /api/v1/activity/stats/{user_id}` - Get activity statistics and streaks
- `GET /api/v1/activity/daily/{user_id}` - Get daily activity data for calendar

### **User Management**
- `GET /api/v1/user-profiles/{user_id}` - Get user profile with statistics
- `POST /api/v1/user-profiles/{user_id}` - Create or update user profile
- `GET /api/v1/profiles/profile/{user_id}` - Get detailed profile information

## System Architecture

### Simplified Design
- **No Automated Job Fetching**: Jobs are extracted on-demand from URLs
- **No RSS Feeds**: Removed dependency on external RSS services
- **No Background Schedulers**: Celery only handles email processing
- **Direct URL Processing**: Users submit URLs for immediate extraction

### Database Models
- **JobListing**: Core job information
- **UserProfile**: AI-extracted user profiles
- **JobApplication**: Application tracking
- **UserGmailConnection**: Gmail OAuth integration
- **EmailEvent**: Email classification and tracking

## Project Structure

```
linkedin-automation/
├── frontend/                 # Next.js frontend application
│   ├── app/                 # App router pages and layouts
│   ├── components/          # Reusable React components
│   │   └── email-agent/    # Gmail integration components
│   ├── lib/                 # Utility functions and hooks
│   └── types/              # TypeScript type definitions
├── backend/                 # FastAPI backend application
│   ├── app/                # Main application code
│   │   ├── api/           # API routes
│   │   ├── core/          # Core functionality
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utility functions
│   ├── tests/             # Test files
│   ├── scripts/           # Utility scripts
│   └── migrations/        # Database migrations
└── docs/                  # Comprehensive documentation
```

## 📚 Documentation

For detailed documentation, guides, and setup instructions, see the **[docs/](docs/README.md)** folder:

- **[Email Agent Setup](docs/EMAIL_AGENT_SETUP.md)** - AI-powered email automation
- **[Gmail Connection Guide](docs/GMAIL_CONNECTION_GUIDE.md)** - OAuth troubleshooting
- **[AI Job Matching](docs/AI_JOB_MATCHING_GUIDE.md)** - Smart job scoring system
- **[Complete Documentation Index](docs/README.md)** - All documentation organized

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

- All API keys and sensitive data should be stored in environment variables
- Rate limiting is implemented to prevent abuse
- Input validation is enforced on all endpoints
- Regular security audits are performed

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 