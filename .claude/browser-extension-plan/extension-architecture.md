# Browser Extension Architecture

## Extension Structure

```
extension/
├── manifest.json              # Manifest V3 configuration
├── popup/
│   ├── popup.html            # Extension popup interface
│   ├── popup.js              # Popup logic and UI handling
│   └── popup.css             # Popup styling
├── sidepanel/
│   ├── panel.html            # Side panel HTML structure
│   ├── panel.js              # React-based side panel app
│   ├── components/
│   │   ├── JobAnalysis.jsx   # Job analysis results display
│   │   ├── ResponseGenerator.jsx # Application response interface
│   │   └── AuthStatus.jsx    # Authentication status component
│   └── styles/
│       └── panel.css         # Side panel styling
├── content/
│   ├── analyzer.js           # Page content analyzer
│   ├── dom-extractor.js      # DOM element extraction utilities
│   └── form-detector.js      # Application form detection
├── background/
│   ├── service-worker.js     # Background service worker
│   ├── auth-manager.js       # Authentication handling
│   └── api-client.js         # Backend API communication
├── utils/
│   ├── storage.js           # Chrome storage utilities
│   ├── constants.js         # Extension constants
│   └── helpers.js           # General utility functions
└── assets/
    ├── icons/               # Extension icons (16x16, 32x32, 48x48, 128x128)
    └── logo.png            # JobFlow Pro logo
```

## Manifest V3 Configuration

```json
{
  "manifest_version": 3,
  "name": "JobFlow Pro Assistant",
  "version": "1.0.0",
  "description": "AI-powered job application assistance directly from job posting pages",

  "permissions": [
    "activeTab",        // Access current tab content
    "storage",          // Store authentication and settings
    "sidePanel"         // Enable side panel functionality
  ],

  "host_permissions": [
    "*://linkedin.com/*",
    "*://*.indeed.com/*",
    "*://*.glassdoor.com/*",
    "*://*.greenhouse.io/*",
    "*://*.workday.com/*",
    "*://*.lever.co/*",
    "*://jobs.*.com/*"
  ],

  "action": {
    "default_popup": "popup/popup.html",
    "default_title": "JobFlow Pro - Analyze this page",
    "default_icon": {
      "16": "assets/icons/icon-16.png",
      "32": "assets/icons/icon-32.png",
      "48": "assets/icons/icon-48.png",
      "128": "assets/icons/icon-128.png"
    }
  },

  "background": {
    "service_worker": "background/service-worker.js",
    "type": "module"
  },

  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": [
        "content/analyzer.js",
        "content/dom-extractor.js",
        "content/form-detector.js"
      ],
      "run_at": "document_idle",
      "all_frames": false
    }
  ],

  "side_panel": {
    "default_path": "sidepanel/panel.html"
  },

  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'; connect-src 'self' https://api.jobflowpro.com https://*.supabase.co;"
  },

  "web_accessible_resources": [
    {
      "resources": ["assets/*"],
      "matches": ["<all_urls>"]
    }
  ]
}
```

## Page Analysis System

### Content Script Architecture

```javascript
// content/analyzer.js
class PageAnalyzer {
  constructor() {
    this.pageType = 'unknown';
    this.confidence = 0;
    this.extractedData = {};
  }

  async detectPageType() {
    const url = window.location.href;
    const pageContent = this.getPageContent();
    const pageStructure = this.analyzePageStructure();

    // Job posting detection
    if (this.isJobPosting(url, pageContent, pageStructure)) {
      this.pageType = 'job_posting';
      this.confidence = this.calculateJobPostingConfidence();
      return this.pageType;
    }

    // Application form detection
    if (this.isApplicationForm(pageContent, pageStructure)) {
      this.pageType = 'application_form';
      this.confidence = this.calculateApplicationFormConfidence();
      return this.pageType;
    }

    return 'unknown';
  }

  isJobPosting(url, content, structure) {
    const jobIndicators = [
      // URL patterns
      /\/jobs?\//i,
      /\/careers?\//i,
      /\/positions?\//i,
      /\/opportunities/i,

      // Content patterns
      /job description/i,
      /responsibilities/i,
      /requirements/i,
      /qualifications/i,
      /about (this|the) (role|position)/i,

      // Structure patterns
      structure.hasJobTitle,
      structure.hasCompanyName,
      structure.hasJobRequirements
    ];

    return this.matchIndicators(jobIndicators, url, content, structure);
  }

  isApplicationForm(content, structure) {
    const formIndicators = [
      // Content patterns
      /apply (for|to)/i,
      /application/i,
      /tell us about yourself/i,
      /why are you interested/i,
      /cover letter/i,
      /upload resume/i,

      // Structure patterns
      structure.hasForm,
      structure.hasTextAreas,
      structure.hasFileUpload,
      structure.hasSubmitButton
    ];

    return this.matchIndicators(formIndicators, '', content, structure);
  }

  analyzePageStructure() {
    return {
      hasForm: !!document.querySelector('form'),
      hasTextAreas: document.querySelectorAll('textarea').length > 0,
      hasFileUpload: !!document.querySelector('input[type="file"]'),
      hasSubmitButton: !!document.querySelector('button[type="submit"], input[type="submit"]'),
      hasJobTitle: this.detectJobTitle(),
      hasCompanyName: this.detectCompanyName(),
      hasJobRequirements: this.detectJobRequirements()
    };
  }

  extractJobPostingData() {
    if (this.pageType !== 'job_posting') return null;

    return {
      url: window.location.href,
      title: this.extractJobTitle(),
      company: this.extractCompanyName(),
      location: this.extractLocation(),
      description: this.extractJobDescription(),
      requirements: this.extractRequirements(),
      benefits: this.extractBenefits(),
      salary: this.extractSalary(),
      jobType: this.extractJobType(),
      postedDate: this.extractPostedDate()
    };
  }

  extractApplicationFormData() {
    if (this.pageType !== 'application_form') return null;

    const questions = this.extractQuestions();
    const jobContext = this.extractJobContext();

    return {
      type: 'application_form',
      questions: questions,
      jobContext: jobContext,
      formStructure: this.analyzeFormStructure()
    };
  }

  extractQuestions() {
    const questions = [];

    // Text areas with labels
    document.querySelectorAll('textarea').forEach(textarea => {
      const question = this.findQuestionForField(textarea);
      if (question) {
        questions.push({
          id: textarea.id || this.generateId(),
          question: question,
          type: 'textarea',
          element: textarea,
          required: textarea.required,
          maxLength: textarea.maxLength
        });
      }
    });

    // Large text inputs
    document.querySelectorAll('input[type="text"]').forEach(input => {
      const question = this.findQuestionForField(input);
      if (question && this.isLikelyEssayQuestion(question)) {
        questions.push({
          id: input.id || this.generateId(),
          question: question,
          type: 'text',
          element: input,
          required: input.required
        });
      }
    });

    return questions;
  }

  findQuestionForField(element) {
    // Look for associated label
    const label = document.querySelector(`label[for="${element.id}"]`);
    if (label) return label.textContent.trim();

    // Look for preceding heading or text
    const prevSibling = element.previousElementSibling;
    if (prevSibling && ['H1', 'H2', 'H3', 'H4', 'LABEL', 'P'].includes(prevSibling.tagName)) {
      return prevSibling.textContent.trim();
    }

    // Look for parent container with question text
    const parent = element.closest('.question, .field, .form-group, [class*="question"], [class*="field"]');
    if (parent) {
      const questionText = parent.querySelector('h1, h2, h3, h4, label, .question-text, [class*="question"]');
      if (questionText) return questionText.textContent.trim();
    }

    return null;
  }
}
```

## Authentication System

### Background Service Worker

```javascript
// background/service-worker.js
class ExtensionAuthManager {
  constructor() {
    this.apiBaseUrl = 'https://api.jobflowpro.com';
    this.authToken = null;
    this.refreshToken = null;
  }

  async initialize() {
    // Load stored auth tokens
    const stored = await chrome.storage.local.get(['authToken', 'refreshToken', 'userId']);
    this.authToken = stored.authToken;
    this.refreshToken = stored.refreshToken;
    this.userId = stored.userId;

    // Verify token validity
    if (this.authToken) {
      const isValid = await this.verifyToken();
      if (!isValid && this.refreshToken) {
        await this.refreshAuthToken();
      }
    }
  }

  async authenticateUser(token) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/extension/auth/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token })
      });

      if (response.ok) {
        const data = await response.json();

        // Store auth data securely
        await chrome.storage.local.set({
          authToken: data.token,
          refreshToken: data.refreshToken,
          userId: data.userId,
          authenticated: true
        });

        this.authToken = data.token;
        this.refreshToken = data.refreshToken;
        this.userId = data.userId;

        return { success: true, user: data };
      }

      throw new Error('Authentication failed');
    } catch (error) {
      console.error('Auth error:', error);
      return { success: false, error: error.message };
    }
  }

  async makeAuthenticatedRequest(url, options = {}) {
    if (!this.authToken) {
      throw new Error('Not authenticated');
    }

    const headers = {
      'Authorization': `Bearer ${this.authToken}`,
      'Content-Type': 'application/json',
      ...options.headers
    };

    const response = await fetch(url, { ...options, headers });

    // Handle token expiry
    if (response.status === 401 && this.refreshToken) {
      await this.refreshAuthToken();
      // Retry request with new token
      headers['Authorization'] = `Bearer ${this.authToken}`;
      return fetch(url, { ...options, headers });
    }

    return response;
  }

  async logout() {
    await chrome.storage.local.remove(['authToken', 'refreshToken', 'userId', 'authenticated']);
    this.authToken = null;
    this.refreshToken = null;
    this.userId = null;
  }
}
```

## Side Panel Implementation

### React-based Side Panel

```javascript
// sidepanel/panel.js
import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';

function JobFlowPanel() {
  const [currentPage, setCurrentPage] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    const result = await chrome.storage.local.get(['authenticated']);
    setAuthenticated(result.authenticated || false);
  };

  const handleAnalyzePage = async () => {
    setLoading(true);

    try {
      // Get active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

      // Send message to content script
      const response = await chrome.tabs.sendMessage(tab.id, {
        action: 'analyze_page'
      });

      if (response.type === 'job_posting') {
        // Analyze job using existing backend
        const jobAnalysis = await analyzeJobPosting(response.data);
        setAnalysis({
          type: 'job',
          data: jobAnalysis
        });
      } else if (response.type === 'application_form') {
        // Generate responses for application questions
        const generatedResponses = await generateApplicationResponses(response.data);
        setAnalysis({
          type: 'application',
          data: generatedResponses
        });
      } else {
        setAnalysis({
          type: 'unknown',
          message: 'Unable to analyze this page. Please visit a job posting or application form.'
        });
      }
    } catch (error) {
      console.error('Analysis failed:', error);
      setAnalysis({
        type: 'error',
        message: 'Analysis failed. Please try again.'
      });
    }

    setLoading(false);
  };

  const analyzeJobPosting = async (jobData) => {
    const response = await chrome.runtime.sendMessage({
      action: 'api_request',
      endpoint: '/api/v1/jobs/extract-from-url',
      method: 'POST',
      data: {
        url: jobData.url,
        user_id: await getUserId(),
        auto_apply: false
      }
    });

    return response.data;
  };

  const generateApplicationResponses = async (formData) => {
    const response = await chrome.runtime.sendMessage({
      action: 'api_request',
      endpoint: '/api/v1/extension/knowledge/generate-response',
      method: 'POST',
      data: {
        questions: formData.questions,
        jobContext: formData.jobContext,
        user_id: await getUserId()
      }
    });

    return response.data;
  };

  if (!authenticated) {
    return <AuthenticationView onAuthenticated={setAuthenticated} />;
  }

  return (
    <div className="jobflow-panel">
      <div className="panel-header">
        <img src="../assets/logo.png" alt="JobFlow Pro" className="logo" />
        <h2>JobFlow Assistant</h2>
      </div>

      <div className="panel-content">
        <button
          onClick={handleAnalyzePage}
          disabled={loading}
          className="analyze-button"
        >
          {loading ? 'Analyzing...' : 'Analyze This Page'}
        </button>

        {analysis && (
          <AnalysisResults analysis={analysis} />
        )}
      </div>
    </div>
  );
}

// Mount React app
const root = createRoot(document.getElementById('root'));
root.render(<JobFlowPanel />);
```

## Communication Flow

### Message Passing Architecture

```javascript
// Message flow between extension components

// 1. User clicks analyze button in popup/side panel
popup.js → background/service-worker.js → content/analyzer.js

// 2. Content script analyzes page and returns data
content/analyzer.js → background/service-worker.js → popup.js/sidepanel.js

// 3. Extension sends data to backend for processing
sidepanel.js → background/service-worker.js → FastAPI backend

// 4. Backend returns analysis/generated content
FastAPI backend → background/service-worker.js → sidepanel.js

// Example message structure:
{
  action: 'analyze_page',
  data: {
    pageType: 'job_posting',
    extractedData: { ... },
    confidence: 0.95
  },
  timestamp: Date.now(),
  tabId: 123
}
```

## Security Considerations

### Token Storage and Management
- **Encryption**: Auth tokens encrypted using Web Crypto API before storage
- **Isolation**: Tokens stored in chrome.storage.local (isolated per extension)
- **Expiry**: Automatic token refresh before expiration
- **Cleanup**: Tokens cleared on logout or extension removal

### Content Security Policy
- **Strict CSP**: Prevents inline scripts and unsafe evaluations
- **Approved Origins**: Only allows connections to JobFlow Pro backend
- **No Eval**: Prevents code injection attacks
- **Resource Isolation**: Web accessible resources properly scoped

### Data Privacy
- **Minimal Collection**: Only collect data necessary for functionality
- **User Control**: Clear indication when data is being processed
- **No Tracking**: No analytics or tracking without user consent
- **Transparent**: Clear privacy policy and data usage explanation

This architecture provides a secure, performant, and maintainable browser extension that integrates seamlessly with the existing JobFlow Pro infrastructure.