#!/usr/bin/env python3
"""
Database cleanup and RLS setup script
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.migrations.cleanup_unused_tables import cleanup_unused_tables

if __name__ == "__main__":
    print("🚀 Starting database cleanup and RLS setup...")
    print("=" * 50)
    
    try:
        cleanup_unused_tables()
        print("\n" + "=" * 50)
        print("✅ Database cleanup and RLS setup completed successfully!")
        print("\n📋 Summary of changes:")
        print("   • Removed unused tables: search_queries, search_results, user_job_preferences, daily_digests, job_scores")
        print("   • Created users table for authentication")
        print("   • Added user_id columns to existing tables")
        print("   • Enabled Row Level Security (RLS) on all tables")
        print("   • Created RLS policies for user data isolation")
        print("   • Added performance indexes")
        print("   • Set up demo user for testing")
        print("\n🔒 Security improvements:")
        print("   • Users can only access their own data")
        print("   • Database-level security with RLS policies")
        print("   • Proper user context management")
        print("\n⚠️  Next steps:")
        print("   1. Update your application code to use the new RLS session")
        print("   2. Test the application with the demo user")
        print("   3. Consider implementing proper authentication if needed")
        
    except Exception as e:
        print(f"\n❌ Error during database cleanup: {e}")
        sys.exit(1) 