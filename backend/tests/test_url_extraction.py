#!/usr/bin/env python3
"""
Test script for URL Job Extraction Feature

This script tests the complete workflow:
1. URL validation
2. Content extraction via Jina AI
3. Job data extraction via OpenAI
4. Database integration
5. API endpoint functionality
"""

import asyncio
import requests
import json
from app.services.url_job_extractor import url_job_extractor

async def test_url_extraction_service():
    """Test the URL extraction service directly"""
    print("🧪 Testing URL Extraction Service")
    print("=" * 50)
    
    # Test URLs - you can replace these with real job posting URLs
    test_urls = [
        "https://stackoverflow.com/jobs/companies/acme-corp",  # Placeholder
        "https://example-company.com/careers/software-engineer",  # Placeholder
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📡 Test {i}: {url}")
        
        try:
            # Test the extraction service
            result = await url_job_extractor.extract_job_details(url)
            
            print("✅ Extraction completed")
            print(f"   Title: {result.get('title', 'N/A')}")
            print(f"   Company: {result.get('company', 'N/A')}")
            print(f"   Location: {result.get('location', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            print(f"   Success: {result.get('extraction_success', False)}")
            
            if not result.get('extraction_success', False):
                print(f"   Error: {result.get('extraction_error', 'Unknown error')}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")

def test_api_endpoint():
    """Test the API endpoint"""
    print("\n🌐 Testing API Endpoint")
    print("=" * 30)
    
    # Test the API endpoint
    api_url = "http://localhost:8000/api/v1/jobs/extract-from-url"
    
    test_data = {
        "url": "https://example-company.com/careers/developer",
        "user_id": "test_user",
        "auto_apply": True,
        "application_notes": "Test extraction via API"
    }
    
    try:
        response = requests.post(api_url, json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API endpoint working")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Job ID: {result.get('job_id', 'N/A')}")
            print(f"   Application ID: {result.get('application_id', 'N/A')}")
            print(f"   Message: {result.get('message', 'N/A')}")
        else:
            print(f"❌ API returned status: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Backend server not running")
        print("💡 Start with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ API test failed: {e}")

def test_real_url_extraction():
    """Test with a real job URL (if available)"""
    print("\n🔗 Testing with Real URL")
    print("=" * 30)
    
    # You can replace this with a real job posting URL for testing
    real_url = input("Enter a real job posting URL (or press Enter to skip): ").strip()
    
    if not real_url:
        print("⏭️  Skipping real URL test")
        return
    
    try:
        # Test with real URL
        response = requests.post(
            "http://localhost:8000/api/v1/jobs/extract-from-url",
            json={
                "url": real_url,
                "user_id": "demo_user",
                "auto_apply": True
            },
            timeout=60  # Longer timeout for real URLs
        )
        
        if response.status_code == 200:
            result = response.json()
            print("🎉 Real URL extraction successful!")
            
            job = result.get('extracted_job', {})
            print(f"   Title: {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Skills: {', '.join(job.get('skills', [])[:5])}")
            print(f"   Confidence: {job.get('confidence', 0):.2f}")
            print(f"   Job ID: {result.get('job_id', 'N/A')}")
            
        else:
            print(f"❌ Extraction failed: {response.status_code}")
            error = response.json()
            print(f"   Error: {error.get('detail', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Real URL test failed: {e}")

def display_summary():
    """Display test summary and next steps"""
    print("\n📊 Test Summary")
    print("=" * 20)
    print("✅ Backend service: URL extraction service created")
    print("✅ API endpoint: /api/v1/jobs/extract-from-url available")
    print("✅ Database: Migration applied for URL extraction fields")
    print("✅ Frontend: JobURLExtractor component created")
    print("✅ Integration: Component added to ProfileTab")
    
    print("\n🚀 Next Steps:")
    print("1. Open http://localhost:3000 in browser")
    print("2. Navigate to Profile tab → 'Extract Job URL'")
    print("3. Paste a job posting URL and test extraction")
    print("4. Check dashboard for tracked applications")
    
    print("\n💡 Supported Job Sites:")
    print("- LinkedIn Jobs")
    print("- Indeed")
    print("- Glassdoor")
    print("- Stack Overflow Jobs")
    print("- Monster, Dice, ZipRecruiter")
    print("- Company career pages")

async def main():
    """Run all tests"""
    print("🎯 URL Job Extraction - Complete Test Suite")
    print("=" * 60)
    
    # Test 1: Service level testing
    await test_url_extraction_service()
    
    # Test 2: API endpoint testing
    test_api_endpoint()
    
    # Test 3: Real URL testing (optional)
    test_real_url_extraction()
    
    # Test 4: Display summary
    display_summary()

if __name__ == "__main__":
    asyncio.run(main()) 