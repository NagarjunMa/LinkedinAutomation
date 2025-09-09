# JobFlow Pro - AI-Powered Job Search Automation

A full-stack application for **on-demand job extraction** from URLs, with integrated Gmail email tracking using Google OAuth.

## Features

- 🔍 **Smart Job Extraction** - Extract job details from LinkedIn URLs with one click
- 📊 **Interactive Dashboard** - View and filter extracted jobs with modern UI
- 📤 **Export Functionality** - CSV, Excel, and Google Sheets export
- 🤖 **AI-Powered Job Matching** - Smart job scoring and skill extraction
- 📧 **Gmail Integration** - Automatic job application email tracking
- 📱 **Responsive, Modern UI** - Built with Next.js and Tailwind CSS

## Tech Stack

### Frontend
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Shadcn UI
- React Query
- Zustand (State Management)

### Backend
- Python FastAPI
- BeautifulSoup4 (Web Scraping)
- PostgreSQL
- Redis (Caching & Email Queue)
- Celery (Email Processing Only)
- Google OAuth 2.0 (Gmail Integration)
- OpenAI GPT-4o-mini (AI Job Matching)

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

## API Endpoints

### Job Extraction
- `POST /api/v1/jobs/extract-from-url` - Extract job from single URL
- `POST /api/v1/jobs/extract-multiple-urls` - Batch URL extraction
- `GET /api/v1/jobs/extraction-stats/{user_id}` - User extraction statistics

### Job Management
- `GET /api/v1/jobs/` - List all jobs
- `GET /api/v1/jobs/{job_id}` - Get specific job
- `PUT /api/v1/jobs/{job_id}` - Update job details
- `DELETE /api/v1/jobs/{job_id}` - Delete job

### User Profiles
- `POST /api/v1/profiles/upload-resume/{user_id}` - Upload and parse resume
- `GET /api/v1/profiles/profile/{user_id}` - Get user profile
- `PUT /api/v1/profiles/profile/{user_id}` - Update profile

### Email Agent
- `POST /api/v1/email-agent/process/{user_id}` - Process user emails
- `GET /api/v1/email-agent/analytics/{user_id}` - Email analytics

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