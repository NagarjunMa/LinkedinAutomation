# Prism Pro (formerly JobFlow) - Project Documentation

**Prism Pro** is a comprehensive, AI-powered job search automation platform designed to help job seekers land their dream roles faster. It transforms the chaotic application process into an organized, intelligent workflow.

> **For LinkedIn Post Creation:** See the "Key Highlights for LinkedIn" section at the bottom of this file.

## 🏗️ Engineering Deep Dive (For Your Tech Blog/LinkedIn)

Use this section to showcase your technical expertise and the "Vision" behind Prism Pro.

### 1. The AI Architecture: "Precision over Complexity"
I initially experimented with a multi-agent system (12+ separate agents) but found it slow and expensive. I refactored this into a **Consolidated Intelligence Architecture**:
- **Job Extraction:**
    - **Tech:** `Telescope` (Jina AI Reader) + **GPT-4o-mini**.
    - **Why:** Jina turns messy HTML into clean Markdown. GPT-4o-mini is fast and cheap enough to parallelize extraction for 10+ jobs at once.
- **Resume Evaluation:**
    - **Tech:** **GPT-4o-2024-08-06** (Structured Outputs).
    - **Prompt Engineering:** Implemented a "Hyper-Critical Sr. Hiring Manager" persona.
    - **Standards Enforced:**
        - **Google's XYZ Formula:** "Accomplished [X] as measured by [Y], by doing [Z]".
        - **7-Second Scan Rule:** Optimizes "Above the Fold" content for human recruiters.
        - **ATS Compliance:** Checks for parsing blockers (tables, columns).
- **Referral Engine:**
    - **Tech:** **GPT-4o-mini** with "Paste-and-Parse" logic.
    - **Innovation:** Instead of complex scraping (which risks bans), I built a text-analysis engine that parses copied LinkedIn profile text to generate hyper-personalized 300-char connection requests.

### 2. Tech Stack & Choices
- **Backend:** FastAPI (Python) for high-performance async processing.
- **Database:** Supabase (PostgreSQL) + Row Level Security (RLS) for enterprise-grade data isolation.
- **Security:** implemented **JWT handling** manually to ensure strict stateless authentication without relying entirely on third-party black boxes.
- **Frontend:** Next.js 14 App Router for server-side SEO and client-side interactivity.

### 3. What I Learned (The "Vision")
*"Building Prism Pro wasn't just about wrapping an API. It was about solving the 'Context Gap' in AI."*
- **Context is King:** The biggest challenge wasn't generating text—it was injecting the *right* user context (experience level, target roles) into the prompt without blowing up token costs.
- **Structured AI:** Moving from random text generation to **Pydantic-validated Structured Outputs** changed everything. It turned "creative writing" AI into a reliable data processor.
- **The "Unverified" Trap:** Navigating Google's OAuth verification taught me that compliance (Limited Use Policy) is just as engineering-heavy as coding.

---

## 🚀 Core Features

### 1. 📊 Intelligent Job Tracking
- **Kanban & List Views:** Visual pipeline to track applications from "Saved" to "Offer".
- **Smart Extraction:** Browser extension automatically extracts job details (Salary, Location, Recruiter) from LinkedIn and Indeed.
- **Status Automation:** Drag-and-drop interface updates application status instantly.

### 2. 🧠 AI Resume Builder
- **Resume Scoring:** Upload a resume + job description to get a 0-100% compatibility score.
- **Keyword Analysis:** AI identifies missing hard/soft skills and keywords.
- **Tailoring Engine:** Automatically rewrites bullet points to match the specific job requirements.

### 3. 🤝 Networking & Referrals
- **Referral Templates:** AI-generated messages for asking for referrals (LinkedIn/Email).
- **Contact Management:** Track networking interactions and follow-ups.

### 4. 🔒 Enterprise-Grade Security & Compliance
- **Google OAuth Verified:** Fully verified by Google for secure "Sign in with Google".
- **Privacy First:** "Limited Use" compliant for Gmail integration.
- **Secure Data:** All user data is encrypted and isolated w/ Row Level Security (RLS).

## 🛠 Tech Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Framer Motion.
- **Backend:** FastAPI (Python), Supabase (Auth & DB), manual JWT handling.
- **Database:** PostgreSQL (Supabase), Redis (Caching).
- **Deployment:** Railway (Frontend & Backend), Docker.
- **AI:** OpenAI GPT-4o-mini for cost-effective, high-intelligence resume analysis.

## 📅 Recent Specific Updates (February 2026)

### Google Verification & Compliance
- **Scope Optimization:** Refactored login flow to use only non-sensitive scopes (`email`, `profile`), ensuring a seamless "Verified" login experience.
- **Privacy Policy:** Published a comprehensive, industry-standard Privacy Policy at `/privacy-policy` complying with Google's "Limited Use" policy for Restricted Scopes.
- **Documentation:** Launched a dedicated `/docs` page guiding users through every feature.

### User Experience
- **Documentation Portal:** New `/docs` route with guides for "Getting Started", "Job Tracking", and "AI Tools".
- **Performance:** Optimized dashboard rendering and removed legacy polling code.

---

## 📢 Key Highlights for LinkedIn Post

If you are writing a post about launching Prism Pro, here are the key talking points:

**Headline Ideas:**
- "Transforming the Job Hunt: Introducing Prism Pro"
- "Stop Applying Blindly. Start Applying Smartly with AI."
- "From Chaos to Offer Letter: My Journey Building Prism Pro"

**The Problem:**
"Job hunting is broken. Managing spreadsheets, guessing ATS keywords, and losing track of applications is exhausting."

**The Solution (Prism Pro):**
"I built Prism Pro to fix this. It's not just a tracker—it's an AI career copilot."

**Feature Spotlight:**
1.  **"One-Click Save":** Instantly save jobs from LinkedIn with all details filled in.
2.  **"Beat the ATS":** My AI scorer tells you exactly *why* your resume might get rejected and how to fix it.
3.  **"Verified & Secure":** Just passed Google's rigorous verification process!

**Call to Action:**
"Check it out live at [www.prismpro.live](https://www.prismpro.live) and let me know what you think! 🚀 #BuildInPublic #AI #JobSearch #React #FastAPI"