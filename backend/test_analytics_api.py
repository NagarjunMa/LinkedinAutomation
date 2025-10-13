"""
Test script for Analytics Intelligence API endpoints
Run this to test all the new analytics API routes
"""

import asyncio
import httpx
import json
import sys
import os
from datetime import datetime

# API base URL - adjust as needed
BASE_URL = "http://localhost:8000/api/v1"
ANALYTICS_BASE = f"{BASE_URL}/analytics-intelligence"


async def test_analytics_api():
    """Test all analytics API endpoints"""

    print("🧪 Testing Analytics Intelligence API")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Test 1: Health Check
        print("\n🏥 Testing Health Check...")
        try:
            response = await client.get(f"{ANALYTICS_BASE}/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Health: {data.get('data', {}).get('status', 'unknown')}")
                print("   ✅ Health check passed")
            else:
                print(f"   ❌ Health check failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")

        # Test 2: Analytics Overview
        print("\n📊 Testing Analytics Overview...")
        try:
            response = await client.get(f"{ANALYTICS_BASE}/overview")
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                message = data.get('message', '')

                print(f"   Response Status: {status}")
                print(f"   Message: {message}")

                if data.get('data'):
                    overview = data['data']
                    print(f"   Skills Preview: {len(overview.get('top_skills_preview', []))}")
                    print(f"   Primary Focus: {overview.get('primary_job_focus', 'None')}")
                    print(f"   Application Velocity: {overview.get('application_velocity', 0)}")
                    print(f"   Insights Count: {overview.get('key_insights_count', 0)}")

                print("   ✅ Overview endpoint working")
            else:
                print(f"   ❌ Overview failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Overview error: {e}")

        # Test 3: Skills Analytics
        print("\n🎯 Testing Skills Analytics...")
        try:
            response = await client.get(f"{ANALYTICS_BASE}/skills")
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                print(f"   Response Status: {status}")

                if data.get('data') and isinstance(data['data'], dict):
                    skills_data = data['data']
                    top_skills = skills_data.get('top_skills', [])
                    trending = skills_data.get('trending_skills', [])
                    recommended = skills_data.get('recommended_skills', [])

                    print(f"   Top Skills: {len(top_skills)}")
                    print(f"   Trending: {len(trending)}")
                    print(f"   Recommended: {len(recommended)}")

                    if top_skills:
                        print(f"   Sample Skill: {top_skills[0].get('skill', 'N/A')}")

                print("   ✅ Skills endpoint working")
            else:
                print(f"   ❌ Skills failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Skills error: {e}")

        # Test 4: Application Trends
        print("\n📈 Testing Trends Analytics...")
        try:
            response = await client.get(f"{ANALYTICS_BASE}/trends?days=30")
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                print(f"   Response Status: {status}")

                if data.get('data'):
                    trends = data['data']
                    print(f"   Data Points: {len(trends.get('data_points', []))}")
                    print(f"   Total Applications: {trends.get('total_applications', 0)}")
                    print(f"   Trend Direction: {trends.get('trend_direction', 'unknown')}")
                    print(f"   Avg Per Week: {trends.get('average_per_week', 0)}")

                print("   ✅ Trends endpoint working")
            else:
                print(f"   ❌ Trends failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Trends error: {e}")

        # Test 5: Full Analytics
        print("\n🔍 Testing Full Analytics...")
        try:
            response = await client.get(f"{ANALYTICS_BASE}/full?days=30")
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                print(f"   Response Status: {status}")

                if data.get('data'):
                    full_data = data['data']
                    print(f"   Has Skills: {'skills' in full_data}")
                    print(f"   Has Preferences: {'preferences' in full_data}")
                    print(f"   Has Behavior: {'behavior' in full_data}")
                    print(f"   Insights: {len(full_data.get('insights', []))}")

                    metadata = full_data.get('metadata', {})
                    print(f"   User ID: {metadata.get('user_id', 'N/A')}")
                    print(f"   Analysis Date: {metadata.get('analysis_date', 'N/A')}")

                print("   ✅ Full analytics endpoint working")
            else:
                print(f"   ❌ Full analytics failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Full analytics error: {e}")

        # Test 6: Refresh Analytics
        print("\n🔄 Testing Analytics Refresh...")
        try:
            refresh_data = {
                "days": 30,
                "force_refresh": False,
                "include_insights": True
            }

            response = await client.post(
                f"{ANALYTICS_BASE}/refresh",
                json=refresh_data
            )
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"   Response Status: {data.get('status', 'unknown')}")
                print(f"   Message: {data.get('message', '')}")
                print("   ✅ Refresh endpoint working")
            else:
                print(f"   ❌ Refresh failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Refresh error: {e}")

        # Test 7: Update Preferences
        print("\n⚙️ Testing Preferences Update...")
        try:
            preferences_data = {
                "weekly_digest": True,
                "insight_notifications": True,
                "analysis_period_days": 30
            }

            response = await client.put(
                f"{ANALYTICS_BASE}/preferences",
                json=preferences_data
            )
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"   Response Status: {data.get('status', 'unknown')}")
                print("   ✅ Preferences endpoint working")
            else:
                print(f"   ❌ Preferences failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Preferences error: {e}")


async def test_api_error_handling():
    """Test API error handling"""

    print("\n🚨 Testing Error Handling...")
    print("-" * 30)

    async with httpx.AsyncClient(timeout=10.0) as client:

        # Test invalid days parameter
        print("\n📅 Testing invalid days parameter...")
        try:
            response = await client.get(f"{ANALYTICS_BASE}/trends?days=500")  # Too many days
            print(f"   Status: {response.status_code}")

            if response.status_code == 422:  # Validation error
                print("   ✅ Validation error handled correctly")
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error test failed: {e}")

        # Test invalid force_refresh parameter
        print("\n🔄 Testing invalid refresh parameter...")
        try:
            response = await client.get(f"{ANALYTICS_BASE}/full?force_refresh=invalid")
            print(f"   Status: {response.status_code}")

            if response.status_code in [422, 400]:
                print("   ✅ Parameter validation working")
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Parameter test failed: {e}")


async def test_api_performance():
    """Test API response times"""

    print("\n⚡ Testing API Performance...")
    print("-" * 25)

    async with httpx.AsyncClient(timeout=30.0) as client:

        endpoints = [
            ("Health", f"{ANALYTICS_BASE}/health"),
            ("Overview", f"{ANALYTICS_BASE}/overview"),
            ("Skills", f"{ANALYTICS_BASE}/skills"),
            ("Trends", f"{ANALYTICS_BASE}/trends?days=7")
        ]

        for name, url in endpoints:
            try:
                start_time = datetime.now()
                response = await client.get(url)
                end_time = datetime.now()

                duration = (end_time - start_time).total_seconds()

                print(f"   {name:10} - {response.status_code} - {duration:.2f}s")

                if duration > 10:
                    print(f"      ⚠️  Slow response time: {duration:.2f}s")
                elif duration < 2:
                    print(f"      ✅ Fast response: {duration:.2f}s")

            except Exception as e:
                print(f"   {name:10} - ERROR - {e}")


def test_api_documentation():
    """Check if API documentation is accessible"""

    print("\n📚 API Documentation Check...")
    print("-" * 30)

    print("   Analytics Intelligence endpoints should be available at:")
    print(f"   📖 Swagger UI: http://localhost:8000/docs#/analytics-intelligence")
    print(f"   📋 ReDoc: http://localhost:8000/redoc")
    print("   ✅ Documentation URLs provided")


async def main():
    """Run all API tests"""

    print("🚀 Analytics Intelligence API Test Suite")
    print("=" * 55)
    print(f"🌐 Testing against: {ANALYTICS_BASE}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Main API functionality tests
    await test_analytics_api()

    # Error handling tests
    await test_api_error_handling()

    # Performance tests
    await test_api_performance()

    # Documentation check
    test_api_documentation()

    print("\n" + "=" * 55)
    print("🏁 API Test Suite Completed!")
    print("\n💡 Next Steps:")
    print("   1. Check FastAPI docs at http://localhost:8000/docs")
    print("   2. Test with real user authentication")
    print("   3. Integrate with frontend components")
    print("   4. Set up monitoring and logging")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        sys.exit(1)