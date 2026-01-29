# JobFlow Pro - AI-Powered Job Search Automation Platform

A comprehensive full-stack application that transforms job searching from a chaotic process into an organized, AI-powered system. Built for students, new graduates, and job seekers who want to maximize their application success rate while saving 15+ hours weekly.

**✨ New Design**: Featuring the "Leica Theory Minimalism" aesthetic with Bento Grid layouts, premium typography, and seamless animations.

## 🚀 Core Features

### **🎨 Modern "Leica Theory" UX/UI**
- **Bento Grid Dashboard** - Modular, data-dense, yet clean visualization of your job search progress.
- **Micro-Interactions** - Polish and responsiveness with Framer Motion animations.
- **Premium Aesthetics** - "Leica Theory" inspired minimalism with *Playfair Display* & *JetBrains Mono* typography, glassmorphism, and subtle noise textures.
- **Sidebar Navigation** - Collapsible, context-aware sidebar for seamless navigation.

### **Job Management & Extraction**
- 🔍 **Smart Job Extraction** - Extract job details from any job posting URL (LinkedIn, Indeed, company sites)
- 📊 **Activity Heatmap** - "Overview Calendar" visualizing your systemic consistency.
- 📈 **Market Engagement** - Interactive charts tracking daily applications and engagement.
- 🤖 **AI-Powered Job Matching** - Smart compatibility scoring based on your profile and skills
- 📤 **Export Functionality** - CSV, Excel, and Google Sheets export for all job data

### **Resume Optimization & Evaluation**
- 📄 **AI Resume Evaluation V2** - Multi-agent system providing recruiter-validated feedback
- 🎯 **ATS Optimization** - Ensure your resume passes Applicant Tracking Systems
- 🔧 **Actionable Feedback** - Specific, line-by-line recommendations for improvement
- 📊 **Market Positioning** - Understand your competitive level and salary range

### **Referral & Networking**
- 📧 **AI Referral Email Generator** - Generate personalized referral requests
- 👥 **Contact Management** - Organize and track your professional network
- 📝 **Email Templates** - Multiple templates for different relationship types
- 📊 **Referral Analytics** - Track response rates and success metrics

### **Email & Application Tracking**
- 📧 **Gmail Integration** - Automatic job application email tracking with OAuth
- 📊 **Email Analytics** - Classify and analyze job-related communications
- 🔔 **Smart Notifications** - Get alerts for interview invitations and responses

## 🛠️ Tech Stack

### **Frontend**
- **Next.js 14** (App Router) - Modern React framework with server-side rendering
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling with custom "Leica Theory" theme configuration
- **Framer Motion** - Advanced animations and gesture handling
- **Recharts** - Composable charting library for data visualization
- **Radix UI** - Accessible component primitives
- **React Context** - Global state management (Auth, Dashboard, Theme)
- **Custom Fonts** - *Inter*, *Playfair Display* (Serif), *JetBrains Mono* (Code)

### **Backend**
- **Python FastAPI** - High-performance async web framework
- **SQLAlchemy** - Advanced ORM with database migrations
- **PostgreSQL** - Robust relational database for complex queries
- **Redis** - Caching and background task queue management
- **Celery** - Distributed task queue for background processing
- **Pydantic** - Data validation and serialization

### **AI & Machine Learning**
- **OpenAI GPT-4o-mini** - Advanced language model for job analysis and resume evaluation
- **Multi-Agent System** - Specialized AI agents for different evaluation aspects
- **Jina AI Reader** - Intelligent web scraping and content extraction

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

## Project Structure

```
linkedin-automation/
├── frontend/                 # Next.js frontend application
│   ├── app/                 # App router pages and layouts
│   │   ├── dashboard/       # Main dashboard views (Bento Grid)
│   │   ├── layout.tsx       # Root layout with fonts & providers
│   │   └── globals.css      # "Leica Theory" theme styles
│   ├── components/          # Reusable React components
│   │   ├── dashboard/       # Dashboard specific components
│   │   └── ui/              # Shared UI primitives
│   ├── lib/                 # Utility functions and hooks
│   └── types/              # TypeScript type definitions
├── backend/                 # FastAPI backend application
│   ├── app/                # Main application code
│   │   ├── api/           # API routes
│   │   ├── core/          # Core functionality
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utility functions
│   └── migrations/        # Database migrations
└── docs/                  # Comprehensive documentation
```

## 📚 Documentation

For detailed documentation, guides, and setup instructions, see the **[docs/](docs/README.md)** folder.

## Security

- All API keys and sensitive data should be stored in environment variables
- Rate limiting is implemented to prevent abuse
- Input validation is enforced on all endpoints
- Regular security audits are performed

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 