# LinkedIn Job Scraper & Automation Tool

A full-stack application for automated job searching, scraping, and management from LinkedIn and other job boards, with integrated Gmail email tracking using Google OAuth.

## Features

- 🔍 Advanced job search with customizable parameters
- 📊 Interactive dashboard for viewing and filtering results
- ⏰ Automated recurring searches
- 📤 Export functionality (CSV, Excel, Google Sheets)
- 🤖 AI-powered job matching and skill extraction
- 📧 Gmail integration for automatic job application email tracking
- 📱 Responsive, modern UI

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
- Playwright (Web Scraping)
- PostgreSQL
- Redis (Caching & Job Queue)
- Celery (Task Queue)
- Google OAuth 2.0 (Gmail Integration)

## Prerequisites

- Node.js 18+
- Python 3.9+
- PostgreSQL
- Redis
- Docker & Docker Compose
- Google Cloud Account (for Gmail OAuth)

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

4. Start the development environment:
```bash
docker-compose up -d
```

5. Access the application:
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

## Email Agent Setup

The Email Agent feature automatically tracks and classifies job application emails from Gmail:

1. **Google OAuth Configuration**: Follow the [Google OAuth Setup Guide](docs/GOOGLE_OAUTH_SETUP.md)
2. **Test the Setup**: Run `python scripts/test_google_oauth.py` to verify configuration
3. **Connect Gmail**: Use the Email Agent page to connect your Gmail account
4. **Process Emails**: Automatically classify and track job application emails

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
│   │   │   └── v1/endpoints/email_agent.py  # Gmail OAuth endpoints
│   │   ├── core/          # Core functionality
│   │   ├── models/        # Database models
│   │   │   └── email_models.py  # Gmail connection models
│   │   ├── services/      # Business logic
│   │   │   ├── gmail_service.py  # Google OAuth Gmail service
│   │   │   └── email_processor.py  # Email processing logic
│   │   └── utils/         # Utility functions
│   ├── tests/             # Test files
│   ├── scripts/           # Utility scripts
│   │   └── test_google_oauth.py  # OAuth setup verification
│   └── migrations/        # Database migrations
└── docs/                  # Comprehensive documentation
    └── GOOGLE_OAUTH_SETUP.md  # Google OAuth setup guide
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