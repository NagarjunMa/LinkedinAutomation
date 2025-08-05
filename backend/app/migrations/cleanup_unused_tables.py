"""
Database cleanup migration to remove unused tables and implement RLS
"""
from sqlalchemy import text
from app.db.session import engine

def cleanup_unused_tables():
    """Remove unused tables and implement RLS"""
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # 1. Drop unused tables (in correct order due to foreign key constraints)
            
            # Drop tables that depend on others first
            print("Dropping unused tables...")
            
            # Drop SearchResult first (depends on SearchQuery and JobListing)
            conn.execute(text("DROP TABLE IF EXISTS search_results CASCADE"))
            print("✓ Dropped search_results table")
            
            # Drop SearchQuery (deprecated, replaced by RSS feeds)
            conn.execute(text("DROP TABLE IF EXISTS search_queries CASCADE"))
            print("✓ Dropped search_queries table")
            
            # Drop UserJobPreferences (functionality merged into UserProfile)
            conn.execute(text("DROP TABLE IF EXISTS user_job_preferences CASCADE"))
            print("✓ Dropped user_job_preferences table")
            
            # Drop DailyDigest (not actively used)
            conn.execute(text("DROP TABLE IF EXISTS daily_digests CASCADE"))
            print("✓ Dropped daily_digests table")
            
            # Drop JobScore (not actively used)
            conn.execute(text("DROP TABLE IF EXISTS job_scores CASCADE"))
            print("✓ Dropped job_scores table")
            
            # 2. Create users table for authentication
            print("\nCreating users table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    full_name VARCHAR(255),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✓ Created users table")
            
            # 3. Add user_id column to job_listings if it doesn't exist
            print("\nAdding user_id to job_listings...")
            conn.execute(text("""
                ALTER TABLE job_listings 
                ADD COLUMN IF NOT EXISTS user_id VARCHAR(100) DEFAULT 'demo_user'
            """))
            print("✓ Added user_id to job_listings")
            
            # 4. Add user_id column to rss_feed_configurations if it doesn't exist
            print("\nAdding user_id to rss_feed_configurations...")
            conn.execute(text("""
                ALTER TABLE rss_feed_configurations 
                ADD COLUMN IF NOT EXISTS user_id VARCHAR(100) DEFAULT 'demo_user'
            """))
            print("✓ Added user_id to rss_feed_configurations")
            
            # 5. Enable RLS on all tables
            print("\nEnabling Row Level Security...")
            
            # Enable RLS on job_listings
            conn.execute(text("ALTER TABLE job_listings ENABLE ROW LEVEL SECURITY"))
            print("✓ Enabled RLS on job_listings")
            
            # Enable RLS on job_applications
            conn.execute(text("ALTER TABLE job_applications ENABLE ROW LEVEL SECURITY"))
            print("✓ Enabled RLS on job_applications")
            
            # Enable RLS on user_profiles
            conn.execute(text("ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY"))
            print("✓ Enabled RLS on user_profiles")
            
            # Enable RLS on rss_feed_configurations
            conn.execute(text("ALTER TABLE rss_feed_configurations ENABLE ROW LEVEL SECURITY"))
            print("✓ Enabled RLS on rss_feed_configurations")
            
            # Enable RLS on email tables
            conn.execute(text("ALTER TABLE user_gmail_connections ENABLE ROW LEVEL SECURITY"))
            print("✓ Enabled RLS on user_gmail_connections")
            
            conn.execute(text("ALTER TABLE email_events ENABLE ROW LEVEL SECURITY"))
            print("✓ Enabled RLS on email_events")
            
            conn.execute(text("ALTER TABLE email_sync_logs ENABLE ROW LEVEL SECURITY"))
            print("✓ Enabled RLS on email_sync_logs")
            
            # 6. Create RLS policies
            print("\nCreating RLS policies...")
            
            # Policy for job_listings - users can only see their own jobs
            conn.execute(text("""
                CREATE POLICY job_listings_user_policy ON job_listings
                FOR ALL USING (user_id = current_setting('app.current_user_id', true)::VARCHAR(100))
            """))
            print("✓ Created job_listings RLS policy")
            
            # Policy for job_applications - users can only see their own applications
            conn.execute(text("""
                CREATE POLICY job_applications_user_policy ON job_applications
                FOR ALL USING (user_id = current_setting('app.current_user_id', true)::VARCHAR(100))
            """))
            print("✓ Created job_applications RLS policy")
            
            # Policy for user_profiles - users can only see their own profile
            conn.execute(text("""
                CREATE POLICY user_profiles_user_policy ON user_profiles
                FOR ALL USING (user_id = current_setting('app.current_user_id', true)::VARCHAR(100))
            """))
            print("✓ Created user_profiles RLS policy")
            
            # Policy for rss_feed_configurations - users can only see their own feeds
            conn.execute(text("""
                CREATE POLICY rss_feeds_user_policy ON rss_feed_configurations
                FOR ALL USING (user_id = current_setting('app.current_user_id', true)::VARCHAR(100))
            """))
            print("✓ Created rss_feed_configurations RLS policy")
            
            # Policy for email tables - users can only see their own email data
            conn.execute(text("""
                CREATE POLICY gmail_connections_user_policy ON user_gmail_connections
                FOR ALL USING (user_id = current_setting('app.current_user_id', true)::VARCHAR(100))
            """))
            print("✓ Created user_gmail_connections RLS policy")
            
            conn.execute(text("""
                CREATE POLICY email_events_user_policy ON email_events
                FOR ALL USING (user_id = current_setting('app.current_user_id', true)::VARCHAR(100))
            """))
            print("✓ Created email_events RLS policy")
            
            conn.execute(text("""
                CREATE POLICY email_sync_logs_user_policy ON email_sync_logs
                FOR ALL USING (user_id = current_setting('app.current_user_id', true)::VARCHAR(100))
            """))
            print("✓ Created email_sync_logs RLS policy")
            
            # 7. Create indexes for better performance
            print("\nCreating performance indexes...")
            
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_listings_user_id ON job_listings(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_applications_user_id ON job_applications(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_rss_feeds_user_id ON rss_feed_configurations(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_gmail_connections_user_id ON user_gmail_connections(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_email_events_user_id ON email_events(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_email_sync_logs_user_id ON email_sync_logs(user_id)"))
            
            print("✓ Created performance indexes")
            
            # 8. Insert demo user if not exists
            print("\nSetting up demo user...")
            conn.execute(text("""
                INSERT INTO users (user_id, email, full_name) 
                VALUES ('demo_user', 'demo@example.com', 'Demo User')
                ON CONFLICT (user_id) DO NOTHING
            """))
            print("✓ Demo user setup complete")
            
            # Commit transaction
            trans.commit()
            print("\n✅ Database cleanup and RLS setup completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error during migration: {e}")
            raise

if __name__ == "__main__":
    cleanup_unused_tables() 