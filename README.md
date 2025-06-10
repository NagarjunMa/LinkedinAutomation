# LinkedIn Job Scraper & Automation Tool

A full-stack application for automated job searching, scraping, and management from LinkedIn and other job boards.

## Features

- 🔍 Advanced job search with customizable parameters
- 📊 Interactive dashboard for viewing and filtering results
- ⏰ Automated recurring searches
- 📤 Export functionality (CSV, Excel, Google Sheets)
- 🤖 AI-powered job matching and skill extraction
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

## Prerequisites

- Node.js 18+
- Python 3.9+
- PostgreSQL
- Redis
- Docker & Docker Compose

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

3. Start the development environment:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

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

## Project Structure

```
linkedin-automation/
├── frontend/                 # Next.js frontend application
│   ├── app/                 # App router pages and layouts
│   ├── components/          # Reusable React components
│   ├── lib/                 # Utility functions and hooks
│   └── types/              # TypeScript type definitions
├── backend/                 # FastAPI backend application
│   ├── app/                # Main application code
│   │   ├── api/           # API routes
│   │   ├── core/          # Core functionality
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utility functions
│   └── tests/             # Backend tests
├── docker/                 # Docker configuration files
└── docs/                  # Documentation
```

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