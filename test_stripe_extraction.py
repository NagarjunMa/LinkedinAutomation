#!/usr/bin/env python3
"""
Test script for Stripe job extraction
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.url_job_extractor import url_job_extractor

async def test_stripe_extraction():
    """Test Stripe job extraction"""
    url = "https://stripe.com/jobs/listing/software-engineer/6891899"
    
    print(f"Testing job extraction from: {url}")
    print("=" * 60)
    
    try:
        # Extract job details
        job_data = await url_job_extractor.extract_job_details(url)
        
        print("✅ Extraction successful!")
        print(f"Title: {job_data.get('title', 'N/A')}")
        print(f"Company: {job_data.get('company', 'N/A')}")
        print(f"Location: {job_data.get('location', 'N/A')}")
        print(f"Job Type: {job_data.get('job_type', 'N/A')}")
        print(f"Experience Level: {job_data.get('experience_level', 'N/A')}")
        print(f"Confidence: {job_data.get('confidence', 'N/A')}")
        print(f"Extraction Method: {job_data.get('extraction_method', 'N/A')}")
        print(f"Success: {job_data.get('extraction_success', 'N/A')}")
        
        if job_data.get('extraction_error'):
            print(f"⚠️  Extraction Error: {job_data.get('extraction_error')}")
        
        print("\nDescription Preview:")
        desc = job_data.get('description', '')
        if desc:
            print(desc[:200] + "..." if len(desc) > 200 else desc)
        
        print("\nRequirements Preview:")
        reqs = job_data.get('requirements', '')
        if reqs:
            print(reqs[:200] + "..." if len(reqs) > 200 else reqs)
        
        print("\nSkills:")
        skills = job_data.get('skills', [])
        if skills:
            print(", ".join(skills[:10]))  # Show first 10 skills
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stripe_extraction())
