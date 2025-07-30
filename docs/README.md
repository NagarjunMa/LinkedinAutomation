# LinkedIn Automation Project Documentation

Welcome to the comprehensive documentation for the LinkedIn Automation project. This folder contains all the documentation, guides, and setup instructions for the project.

## 📚 Documentation Index

### 🚀 **Getting Started**
- **[README.md](../README.md)** - Main project overview and quick start guide

### 📧 **Email Agent System**
- **[EMAIL_AGENT_SETUP.md](EMAIL_AGENT_SETUP.md)** - Complete setup guide for the AI email agent
- **[EMAIL_AGENT_SUMMARY.md](EMAIL_AGENT_SUMMARY.md)** - Technical summary and implementation details
- **[GMAIL_CONNECTION_GUIDE.md](GMAIL_CONNECTION_GUIDE.md)** - Gmail OAuth connection troubleshooting

### 🤖 **AI & Job Matching**
- **[AI_JOB_MATCHING_GUIDE.md](AI_JOB_MATCHING_GUIDE.md)** - AI-powered job matching system guide

### 🔄 **Background Processing**
- **[celery- tracking.md](celery- tracking.md)** - Celery background task management

## 🏗️ **Project Structure**

```
linkedin-automation/
├── backend/                 # Python FastAPI backend
│   ├── app/                # Main application code
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Configuration and core services
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic services
│   │   └── utils/         # Utility functions
│   ├── tests/             # Test files
│   ├── scripts/           # Utility scripts
│   └── migrations/        # Database migrations
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/          # Next.js app router
│   │   ├── components/   # React components
│   │   └── lib/          # Utility libraries
│   └── public/           # Static assets
└── docs/                 # Documentation (this folder)
```

## 🎯 **Key Features**

### **Email Agent System**
- **Gmail Integration**: OAuth-based Gmail connection via Arcade.dev
- **AI Email Classification**: OpenAI-powered email categorization
- **Job Application Tracking**: Automatic status updates from emails
- **Email Dashboard**: Web interface for email management

### **Job Matching & AI**
- **Smart Job Scoring**: AI-powered job relevance scoring
- **Resume Parsing**: Automated resume analysis
- **Job Aggregation**: Multi-source job collection
- **Application Tracking**: Comprehensive job application management

### **Background Processing**
- **Celery Tasks**: Asynchronous job processing
- **Email Sync**: Automated email synchronization
- **Job Scraping**: Scheduled LinkedIn job scraping

## 🚀 **Quick Start**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd linkedin-automation
   ```

2. **Set up environment variables**
   ```bash
   # Copy and configure .env files
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

3. **Install dependencies**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

4. **Start the application**
   ```bash
   # Backend (in backend directory)
   uvicorn app.main:app --reload
   
   # Frontend (in frontend directory)
   npm run dev
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📖 **Detailed Guides**

### **Email Agent Setup**
For complete email agent setup instructions, see [EMAIL_AGENT_SETUP.md](EMAIL_AGENT_SETUP.md).

### **Gmail Connection**
For Gmail OAuth troubleshooting, see [GMAIL_CONNECTION_GUIDE.md](GMAIL_CONNECTION_GUIDE.md).

### **AI Job Matching**
For AI-powered job matching configuration, see [AI_JOB_MATCHING_GUIDE.md](AI_JOB_MATCHING_GUIDE.md).

## 🔧 **Development**

### **Running Tests**
```bash
cd backend/tests
python test_email_agent.py
python test_gmail_connection.py
```

### **Database Migrations**
```bash
cd backend
alembic upgrade head
```

### **Background Tasks**
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

## 📞 **Support**

For issues and questions:
1. Check the relevant documentation files above
2. Review the troubleshooting guides
3. Check the test files for examples
4. Review the API documentation at http://localhost:8000/docs

## 📝 **Contributing**

When adding new features:
1. Update relevant documentation
2. Add tests in the `backend/tests/` directory
3. Update this README if needed
4. Follow the existing code structure and patterns

---

**Last Updated**: July 2024  
**Version**: 1.0.0 