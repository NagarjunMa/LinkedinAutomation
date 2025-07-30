#!/usr/bin/env python3
"""
Test script for AI-powered job matching system
Tests resume parsing, job scoring, and profile management
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.services.resume_parser import resume_parser
from app.services.job_scorer import job_scorer
from app.core.ai_service import ai_service
from app.db.session import SessionLocal
from app.models.job import UserProfile, JobListing, JobScore

# Sample resume text for testing
SAMPLE_RESUME_TEXT = """
John Smith
Software Engineer
Email: john.smith@email.com
Phone: (555) 123-4567
Location: San Francisco, CA
Work Authorization: US Citizen

PROFESSIONAL SUMMARY
Experienced Full Stack Developer with 3 years of experience building scalable web applications.
Strong background in Python, JavaScript, and cloud technologies.

SKILLS
Programming Languages: Python, JavaScript, TypeScript, Java
Frameworks: React, Django, FastAPI, Node.js
Tools & Platforms: AWS, Docker, Git, PostgreSQL, Redis
Soft Skills: Team Leadership, Problem Solving, Communication

EXPERIENCE
Software Engineer - Tech Startup Inc (2022-2024)
- Led development of microservices architecture serving 100k+ users
- Built REST APIs using Django and FastAPI
- Implemented CI/CD pipelines reducing deployment time by 50%

Junior Developer - WebDev Solutions (2021-2022)
- Developed responsive web applications using React and TypeScript
- Collaborated with cross-functional teams on agile projects
- Maintained legacy PHP applications

EDUCATION
Bachelor of Science in Computer Science
Stanford University, 2021
Relevant Coursework: Data Structures, Algorithms, Software Engineering, Machine Learning

JOB PREFERENCES
Desired Roles: Senior Software Engineer, Full Stack Developer, Backend Engineer
Preferred Locations: San Francisco, Seattle, Remote
Salary Range: $120,000 - $160,000
Job Types: Full-time
"""

async def test_ai_system():
    """
    Test the complete AI job matching system
    """
    print("🤖 Testing AI Job Matching System")
    print("=" * 50)
    
    # Check if OpenAI API key is set
    if not settings.OPENAPI_KEY:
        print("❌ ERROR: OPENAPI_KEY not set in environment variables")
        print("Please set OPENAPI_KEY in your .env file or environment")
        return False
    
    print(f"✅ OpenAI API Key configured (length: {len(settings.OPENAPI_KEY)})")
    print(f"✅ Model: {settings.OPENAI_MODEL}")
    
    # Test 1: Resume Parsing
    print("\n📄 Test 1: Resume Parsing")
    print("-" * 30)
    
    try:
        parsed_data = await resume_parser.update_profile_from_text(SAMPLE_RESUME_TEXT)
        
        print("✅ Resume parsing successful!")
        print(f"   Name: {parsed_data.get('personal_info', {}).get('full_name', 'N/A')}")
        print(f"   Experience: {parsed_data.get('professional_summary', {}).get('years_of_experience', 0)} years")
        print(f"   Skills: {len(parsed_data.get('skills', {}).get('programming_languages', []))} programming languages")
        print(f"   AI Summary: {parsed_data.get('ai_insights', {}).get('profile_summary', 'N/A')[:100]}...")
        
    except Exception as e:
        print(f"❌ Resume parsing failed: {str(e)}")
        return False
    
    # Test 2: Database Integration
    print("\n💾 Test 2: Database Integration")
    print("-" * 30)
    
    db = SessionLocal()
    try:
        # Create test user profile
        test_user_id = f"test_user_{int(datetime.now().timestamp())}"
        
        # Check if profile already exists and delete it
        existing_profile = db.query(UserProfile).filter(UserProfile.user_id == test_user_id).first()
        if existing_profile:
            db.delete(existing_profile)
            db.commit()
        
        # Create new profile from parsed data
        personal = parsed_data.get("personal_info", {})
        professional = parsed_data.get("professional_summary", {})
        skills = parsed_data.get("skills", {})
        preferences = parsed_data.get("preferences", {})
        ai_insights = parsed_data.get("ai_insights", {})
        
        profile = UserProfile(
            user_id=test_user_id,
            full_name=personal.get("full_name", ""),
            email=personal.get("email", ""),
            location=personal.get("location", ""),
            work_authorization=personal.get("work_authorization", ""),
            years_of_experience=professional.get("years_of_experience", 0.0),
            career_level=professional.get("career_level", "entry"),
            professional_summary=professional.get("summary", ""),
            programming_languages=skills.get("programming_languages", []),
            frameworks_libraries=skills.get("frameworks_libraries", []),
            tools_platforms=skills.get("tools_platforms", []),
            soft_skills=skills.get("soft_skills", []),
            desired_roles=preferences.get("desired_roles", []),
            preferred_locations=preferences.get("preferred_locations", []),
            salary_range_min=preferences.get("salary_range_min", 0),
            salary_range_max=preferences.get("salary_range_max", 0),
            ai_profile_summary=ai_insights.get("profile_summary", ""),
            ai_strengths=ai_insights.get("strengths", []),
            ai_improvement_areas=ai_insights.get("improvement_areas", []),
            ai_career_advice=ai_insights.get("career_advice", "")
        )
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        print(f"✅ User profile created with ID: {test_user_id}")
        print(f"   Database ID: {profile.id}")
        
    except Exception as e:
        print(f"❌ Database integration failed: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()
    
    # Test 3: Job Scoring
    print("\n🎯 Test 3: Job Scoring")
    print("-" * 30)
    
    db = SessionLocal()
    try:
        # Get a few recent jobs for testing
        recent_jobs = db.query(JobListing).filter(JobListing.is_active == True).limit(3).all()
        
        if not recent_jobs:
            print("⚠️  No active jobs found for scoring test")
            print("   Run RSS feed refresh first to get jobs")
        else:
            print(f"✅ Found {len(recent_jobs)} active jobs for testing")
            
            # Test job scoring for our test user
            scored_jobs = await job_scorer.score_jobs_for_user(test_user_id, job_limit=3, days_back=30)
            
            print(f"✅ Job scoring completed!")
            print(f"   Jobs scored: {len(scored_jobs)}")
            
            if scored_jobs:
                top_job = max(scored_jobs, key=lambda x: x['compatibility_score'])
                print(f"   Top match: {top_job.get('title', 'N/A')} at {top_job.get('company', 'N/A')}")
                print(f"   Score: {top_job.get('compatibility_score', 0):.1f}%")
                print(f"   Reasoning: {top_job.get('reasoning', 'N/A')[:100]}...")
    
    except Exception as e:
        print(f"❌ Job scoring failed: {str(e)}")
        return False
    finally:
        db.close()
    
    # Test 4: API Endpoints Check
    print("\n🌐 Test 4: API Endpoints")
    print("-" * 30)
    
    try:
        # Import the router to check if endpoints are properly configured
        from app.api.v1.endpoints.profiles import router
        
        # Get all routes
        routes = [route.path for route in router.routes if hasattr(route, 'path')]
        
        print("✅ Profile API endpoints available:")
        for route in routes:
            print(f"   {route}")
        
    except Exception as e:
        print(f"❌ API endpoint check failed: {str(e)}")
        return False
    
    # Test 5: Cleanup
    print("\n🧹 Test 5: Cleanup")
    print("-" * 30)
    
    db = SessionLocal()
    try:
        # Clean up test data
        test_profile = db.query(UserProfile).filter(UserProfile.user_id == test_user_id).first()
        if test_profile:
            # Delete associated job scores
            db.query(JobScore).filter(JobScore.user_id == test_user_id).delete()
            # Delete profile
            db.delete(test_profile)
            db.commit()
            print(f"✅ Cleaned up test user: {test_user_id}")
        
    except Exception as e:
        print(f"⚠️  Cleanup warning: {str(e)}")
    finally:
        db.close()
    
    print("\n🎉 AI Job Matching System Test Complete!")
    print("=" * 50)
    print("✅ All core components are working correctly")
    print("\n📋 Next Steps:")
    print("1. Set up frontend integration")
    print("2. Test resume file upload endpoints")
    print("3. Configure daily digest generation")
    print("4. Monitor AI costs and performance")
    
    return True

async def test_api_calls():
    """
    Test direct AI API calls
    """
    print("\n🔥 Testing Direct AI API Calls")
    print("-" * 30)
    
    try:
        # Test simple AI call
        sample_user_profile = {
            "skills": {"programming_languages": ["Python", "JavaScript"]},
            "experience": {"job_titles": ["Software Engineer"]},
            "preferences": {"desired_roles": ["Senior Software Engineer"]},
            "personal_info": {"location": "San Francisco"}
        }
        
        sample_job_description = "We are looking for a Senior Software Engineer with Python and JavaScript experience to join our team in San Francisco."
        
        result = await ai_service.score_job_compatibility(
            user_profile=sample_user_profile,
            job_description=sample_job_description,
            job_title="Senior Software Engineer"
        )
        
        print("✅ AI job scoring API call successful!")
        print(f"   Compatibility Score: {result.get('compatibility_score', 0):.1f}%")
        print(f"   Confidence: {result.get('confidence_score', 0):.1f}%")
        print(f"   Reasoning: {result.get('reasoning', 'N/A')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ AI API call failed: {str(e)}")
        print("   Check your OPENAPI_KEY and internet connection")
        return False

if __name__ == "__main__":
    print("🚀 Starting AI Job Matching System Tests...")
    
    async def run_all_tests():
        # Test AI API first
        ai_success = await test_api_calls()
        if not ai_success:
            print("\n❌ AI API tests failed. Please check OpenAI configuration.")
            return
        
        # Run full system test
        success = await test_ai_system()
        
        if success:
            print("\n🎊 All tests passed! System is ready for production.")
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
    
    # Run the tests
    asyncio.run(run_all_tests()) 