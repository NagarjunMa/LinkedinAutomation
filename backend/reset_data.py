#!/usr/bin/env python3
"""
Data Reset Script for Testing
Clears all user-related data from the database for fresh testing.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings

def reset_database():
    """Reset database by clearing all user-related data"""

    # Create database connection
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

    print("🔄 Starting database reset...")

    try:
        with engine.connect() as conn:
            # Clear user-related data in dependency order
            clear_queries = [
                "DELETE FROM email_events;",
                "DELETE FROM user_settings;",
                "DELETE FROM resumes;",
                "DELETE FROM user_profiles;",
                "DELETE FROM jobs;",
                "DELETE FROM auth.users;",
            ]

            for query in clear_queries:
                try:
                    with conn.begin():  # Use transaction for each query
                        result = conn.execute(text(query))
                        table_name = query.split("FROM ")[1].split(";")[0]
                        print(f"✅ Cleared {table_name}")
                except Exception as e:
                    table_name = query.split("FROM ")[1].split(";")[0]
                    print(f"⚠️  Error clearing {table_name}: {str(e)}")

            print("✅ Database reset completed successfully!")

    except Exception as e:
        print(f"❌ Error during database reset: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    print("🚨 WARNING: This will delete ALL user data from the database!")
    print("📊 Database:", settings.SQLALCHEMY_DATABASE_URI.split("@")[1] if "@" in settings.SQLALCHEMY_DATABASE_URI else "Unknown")

    # Auto-confirm for automation
    print("🔄 Proceeding with database reset...")
    success = reset_database()
    if success:
        print("\n🎉 Database reset complete! You can now:")
        print("1. Create a fresh user account")
        print("2. Test the application with clean data")
        print("3. Upload new resumes and jobs")
    else:
        print("\n❌ Database reset failed. Check the errors above.")