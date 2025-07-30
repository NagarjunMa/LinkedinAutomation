#!/usr/bin/env python3
"""
RSS Feed Scheduler Fix Script

This script diagnoses and fixes the RSS feed refresh scheduler
"""

import subprocess
import time
import asyncio
from datetime import datetime
from app.db.session import SessionLocal
from app.models.job import RSSFeedConfiguration, JobListing
from app.services.job_aggregator import JobAggregator

def check_redis():
    """Check if Redis is running"""
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis is running")
            return True
        else:
            print("❌ Redis is not responding")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Redis is not installed or not running")
        return False

def check_celery_processes():
    """Check if Celery worker and beat are running"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        processes = result.stdout
        
        worker_running = 'celery worker' in processes
        beat_running = 'celery beat' in processes or 'celery -A app.core.celery_app beat' in processes
        
        print(f"✅ Celery Beat: {'Running' if beat_running else 'Not Running'}")
        print(f"✅ Celery Worker: {'Running' if worker_running else 'Not Running'}")
        
        return worker_running, beat_running
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return False, False

def start_redis():
    """Start Redis server"""
    print("\n🚀 Starting Redis server...")
    try:
        # Try different Redis start commands
        commands = [
            ['redis-server'],
            ['brew', 'services', 'start', 'redis'],  # macOS with Homebrew
            ['sudo', 'systemctl', 'start', 'redis'],  # Linux systemd
            ['sudo', 'service', 'redis-server', 'start']  # Linux sysvinit
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"✅ Redis started with: {' '.join(cmd)}")
                    time.sleep(2)  # Give Redis time to start
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        print("❌ Could not start Redis automatically")
        print("💡 Please install and start Redis manually:")
        print("   macOS: brew install redis && brew services start redis")
        print("   Ubuntu: sudo apt install redis-server && sudo service redis-server start")
        return False
        
    except Exception as e:
        print(f"❌ Error starting Redis: {e}")
        return False

async def manual_rss_refresh():
    """Manually refresh RSS feeds to get new jobs immediately"""
    print("\n🔄 Performing manual RSS refresh...")
    
    db = SessionLocal()
    try:
        # Count jobs before
        jobs_before = db.query(JobListing).count()
        print(f"📊 Jobs before refresh: {jobs_before}")
        
        # Get RSS feed URLs
        feeds = db.query(RSSFeedConfiguration).filter(RSSFeedConfiguration.is_active == True).all()
        print(f"📡 Found {len(feeds)} active RSS feeds")
        
        # Use JobAggregator to fetch new jobs
        aggregator = JobAggregator()
        
        # Create a search query to trigger RSS fetching
        query = {
            "title": "Software Engineer",
            "location": "United States",
            "keywords": "software,engineering,development,python,javascript",
            "enhanced_search": True
        }
        
        print("⏳ Fetching jobs from all RSS feeds...")
        jobs = await aggregator.search_jobs(query)
        print(f"🎯 Found {len(jobs)} jobs from RSS feeds")
        
        # Count jobs after
        jobs_after = db.query(JobListing).count()
        new_jobs = jobs_after - jobs_before
        
        print(f"📈 Jobs after refresh: {jobs_after}")
        print(f"✅ New jobs added: {new_jobs}")
        
        if new_jobs > 0:
            print("🎉 RSS feeds are working! New jobs successfully added.")
        else:
            print("⚠️ No new jobs found - feeds may be returning same content")
        
        return new_jobs
        
    except Exception as e:
        print(f"❌ Error during manual refresh: {e}")
        return 0
    finally:
        db.close()

def show_startup_commands():
    """Show commands to start Celery worker and beat"""
    print("\n📋 Manual Startup Commands")
    print("=" * 50)
    print("Open 3 separate terminals and run:")
    print()
    print("🔴 Terminal 1 - Start Redis:")
    print("   redis-server")
    print("   # OR on macOS: brew services start redis")
    print()
    print("🟡 Terminal 2 - Start Celery Worker:")
    print("   cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend")
    print("   celery -A app.core.celery_app worker --loglevel=info")
    print()
    print("🟢 Terminal 3 - Start Celery Beat (Scheduler):")
    print("   cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend")
    print("   celery -A app.core.celery_app beat --loglevel=info")
    print()
    print("💡 Alternative: Use Docker Compose")
    print("   cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation")
    print("   docker-compose up redis celery-worker celery-beat")

async def main():
    """Main diagnostic and fix function"""
    print("🔧 RSS Feed Scheduler Diagnostic & Fix")
    print("=" * 50)
    
    # Step 1: Check Redis
    redis_ok = check_redis()
    if not redis_ok:
        redis_started = start_redis()
        if redis_started:
            redis_ok = check_redis()
    
    # Step 2: Check Celery processes
    worker_running, beat_running = check_celery_processes()
    
    # Step 3: Manual refresh to get immediate results
    new_jobs = await manual_rss_refresh()
    
    # Step 4: Show status and next steps
    print("\n📊 Diagnosis Complete")
    print("=" * 30)
    print(f"Redis: {'✅' if redis_ok else '❌'}")
    print(f"Celery Worker: {'✅' if worker_running else '❌'}")
    print(f"Celery Beat: {'✅' if beat_running else '❌'}")
    print(f"Manual refresh: {'✅' if new_jobs > 0 else '⚠️'} ({new_jobs} new jobs)")
    
    if not redis_ok or not worker_running:
        print("\n🚨 Action Required:")
        if not redis_ok:
            print("   • Start Redis server")
        if not worker_running:
            print("   • Start Celery worker process")
        show_startup_commands()
    else:
        print("\n🎉 All systems operational!")
        print("   RSS feeds will refresh automatically every hour")

if __name__ == "__main__":
    asyncio.run(main()) 