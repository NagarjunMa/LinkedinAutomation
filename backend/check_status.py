#!/usr/bin/env python3
"""
RSS Feed Status Checker

Quick script to check if RSS feeds are being refreshed properly
"""

from app.db.session import SessionLocal
from app.models.job import RSSFeedConfiguration, JobListing
from datetime import datetime, timedelta
from sqlalchemy import text
import subprocess

def check_processes():
    """Check if Celery processes are running"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        processes = result.stdout
        
        worker_count = processes.count('celery worker')
        beat_running = 'celery beat' in processes
        
        print(f"🔧 Celery Worker: {worker_count} processes")
        print(f"🔧 Celery Beat: {'✅ Running' if beat_running else '❌ Not Running'}")
        
        return worker_count > 0, beat_running
    except:
        return False, False

def main():
    """Check RSS feed status"""
    print("📊 RSS Feed Status Check")
    print("=" * 40)
    
    # Check processes
    worker_ok, beat_ok = check_processes()
    
    db = SessionLocal()
    try:
        # Current statistics
        total_jobs = db.query(JobListing).count()
        active_feeds = db.query(RSSFeedConfiguration).filter(RSSFeedConfiguration.is_active == True).count()
        
        print(f"📈 Total jobs: {total_jobs}")
        print(f"📡 Active feeds: {active_feeds}")
        
        # Recent jobs check
        for hours in [1, 6, 24]:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            recent = db.query(JobListing).filter(JobListing.extracted_date >= cutoff).count()
            print(f"🕐 Jobs added (last {hours}h): {recent}")
        
        # Feed health
        print(f"\n📡 Feed Health:")
        feeds = db.query(RSSFeedConfiguration).filter(RSSFeedConfiguration.is_active == True).all()
        
        overdue_count = 0
        for feed in feeds:
            if feed.last_refresh:
                hours_ago = (datetime.utcnow() - feed.last_refresh).total_seconds() / 3600
                status = "✅" if hours_ago < 2 else "⚠️"
                if hours_ago >= 2:
                    overdue_count += 1
                print(f"   {status} {feed.name}: {hours_ago:.1f}h ago ({feed.last_job_count} jobs)")
            else:
                print(f"   ❌ {feed.name}: Never refreshed")
                overdue_count += 1
        
        # Overall status
        print(f"\n🎯 System Status:")
        if worker_ok and beat_ok and overdue_count == 0:
            print("   ✅ All systems operational!")
        elif worker_ok and beat_ok:
            print(f"   ⚠️  Scheduler running, but {overdue_count} feeds overdue")
        else:
            print("   ❌ Scheduler not running properly")
            print("   💡 Run: ./start_celery.sh")
        
        # Next refresh estimate
        if beat_ok:
            print(f"   ⏰ Next refresh: Within 60 minutes")
        
    finally:
        db.close()

if __name__ == "__main__":
    main() 