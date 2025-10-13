"""
Simple test script for analytics intelligence system
Run this to test the analytics generation pipeline
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.db.session import SessionLocal
from app.services.analytics_intelligence import AnalyticsIntelligenceService
from app.models.user import User
from app.models.job import JobListing, JobApplication
from datetime import datetime, timedelta
import json


async def test_analytics_generation():
    """Test the analytics generation for a sample user"""

    db = SessionLocal()

    try:
        print("🚀 Testing Analytics Intelligence System")
        print("=" * 50)

        # Get a user with applications for testing
        user = db.query(User).join(
            JobApplication, User.user_id == JobApplication.user_id
        ).first()

        if not user:
            print("❌ No users with applications found")
            print("💡 Create some job applications first to test analytics")
            return

        print(f"👤 Testing analytics for user: {user.user_id}")

        # Create analytics service
        analytics_service = AnalyticsIntelligenceService(db)

        # Test getting recent applications
        print("\n📋 Getting recent applications...")
        applications = await analytics_service.get_recent_applications(user.user_id, days=30)
        print(f"   Found {len(applications)} applications in last 30 days")

        if len(applications) < 3:
            print("⚠️  Insufficient applications for full analytics")
            print("   Creating minimal analytics instead...")

        # Generate analytics
        print("\n🧠 Generating AI analytics...")
        start_time = datetime.utcnow()

        analytics_data = await analytics_service.generate_user_analytics(user.user_id, days=30)

        generation_time = (datetime.utcnow() - start_time).total_seconds()
        print(f"   ✅ Analytics generated in {generation_time:.2f} seconds")

        # Display results
        print("\n📊 Analytics Results:")
        print("-" * 30)

        metadata = analytics_data.get("metadata", {})
        print(f"   Applications analyzed: {metadata.get('total_applications', 0)}")

        # Skills analysis
        skills = analytics_data.get("skills", {})
        if isinstance(skills, dict) and "top_skills" in skills:
            print(f"   Top skills found: {len(skills.get('top_skills', []))}")
            for skill in skills.get("top_skills", [])[:3]:
                if isinstance(skill, dict):
                    print(f"     - {skill.get('skill', 'Unknown')}: {skill.get('percentage', 0)}%")

        # Insights
        insights = analytics_data.get("insights", [])
        print(f"   AI insights generated: {len(insights)}")
        for i, insight in enumerate(insights[:2]):
            if isinstance(insight, dict):
                print(f"     {i+1}. {insight.get('title', 'Unknown insight')}")

        # Test caching
        print("\n💾 Testing analytics cache...")
        cached_data = await analytics_service.get_cached_analytics(user.user_id)
        if cached_data:
            print("   ✅ Cache working correctly")
        else:
            print("   ⚠️  Cache not found (expected for first run)")

        print("\n✅ Analytics test completed successfully!")
        print("🎯 Next steps:")
        print("   1. Run database migration to create analytics tables")
        print("   2. Set up Celery for background tasks")
        print("   3. Create API endpoints for frontend access")

        return analytics_data

    except Exception as e:
        print(f"\n❌ Analytics test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        db.close()


async def test_skills_analysis():
    """Test just the skills analysis component"""

    print("\n🔧 Testing Skills Analysis Component")
    print("-" * 40)

    db = SessionLocal()
    analytics_service = AnalyticsIntelligenceService(db)

    # Create mock applications for testing
    mock_applications = []

    # Mock application 1 - Frontend role
    app1 = type('MockApp', (), {
        'requirements': 'React, JavaScript, TypeScript, CSS, HTML, Git, REST APIs',
        'description': 'Frontend developer role working with React and modern JavaScript'
    })()

    # Mock application 2 - Full stack role
    app2 = type('MockApp', (), {
        'requirements': 'Python, Django, PostgreSQL, React, Docker, AWS',
        'description': 'Full stack developer position using Python backend and React frontend'
    })()

    # Mock application 3 - Backend role
    app3 = type('MockApp', (), {
        'requirements': 'Node.js, Express, MongoDB, GraphQL, TypeScript',
        'description': 'Backend engineer role building APIs with Node.js and GraphQL'
    })()

    mock_applications = [app1, app2, app3]

    try:
        skills_analysis = await analytics_service.analyze_skills_patterns(mock_applications)

        print("📋 Skills Analysis Results:")
        print(f"   Top skills: {len(skills_analysis.get('top_skills', []))}")
        print(f"   Trending skills: {skills_analysis.get('trending_skills', [])}")
        print(f"   Recommended skills: {skills_analysis.get('recommended_skills', [])}")

        return skills_analysis

    except Exception as e:
        print(f"❌ Skills analysis test failed: {e}")
        # Test fallback method
        print("🔄 Testing fallback skills analysis...")
        fallback_result = await analytics_service.fallback_skills_analysis(mock_applications)
        print(f"   Fallback result: {len(fallback_result.get('top_skills', []))} skills found")
        return fallback_result

    finally:
        db.close()


async def test_database_operations():
    """Test database storage and retrieval"""

    print("\n💾 Testing Database Operations")
    print("-" * 35)

    db = SessionLocal()

    try:
        from app.models.analytics import UserAnalytics, AnalyticsCache

        # Test if tables exist (they may not if migration hasn't run)
        try:
            analytics_count = db.query(UserAnalytics).count()
            cache_count = db.query(AnalyticsCache).count()

            print(f"   📊 Analytics records: {analytics_count}")
            print(f"   🗄️  Cache entries: {cache_count}")
            print("   ✅ Database tables accessible")

        except Exception as e:
            print(f"   ⚠️  Database tables not found: {e}")
            print("   💡 Run migration first: alembic upgrade head")

    except ImportError as e:
        print(f"   ⚠️  Analytics models not imported: {e}")

    finally:
        db.close()


def main():
    """Run all analytics tests"""

    print("🧪 Analytics Intelligence System Test Suite")
    print("=" * 55)

    # Test database operations first
    asyncio.run(test_database_operations())

    # Test skills analysis component
    asyncio.run(test_skills_analysis())

    # Test full analytics generation
    asyncio.run(test_analytics_generation())

    print("\n" + "=" * 55)
    print("🏁 Test suite completed!")


if __name__ == "__main__":
    main()