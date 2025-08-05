#!/usr/bin/env python3
"""Script to set up automatic job cleanup scheduling"""

import os
import sys
from celery.schedules import crontab

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.celery_app import celery_app
from app.tasks.cleanup_tasks import cleanup_old_jobs_task, get_cleanup_stats_task

def setup_cleanup_schedule():
    """Set up automatic cleanup schedule using Celery Beat"""
    print("Setting up automatic job cleanup schedule...")
    
    celery_app.conf.beat_schedule = {
        'daily-job-cleanup': {
            'task': 'app.tasks.cleanup_tasks.cleanup_old_jobs_task',
            'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
            'args': (20,),
            'options': {'queue': 'cleanup'}
        },
        'weekly-cleanup-stats': {
            'task': 'app.tasks.cleanup_tasks.get_cleanup_stats_task',
            'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3:00 AM
            'args': (20,),
            'options': {'queue': 'cleanup'}
        },
    }
    
    print("Cleanup schedule configured:")
    print("- Daily cleanup: 2:00 AM (jobs older than 20 days)")
    print("- Weekly stats: Sunday 3:00 AM")
    print("\nTo start the scheduler, run:")
    print("celery -A app.core.celery_app beat --loglevel=info")
    print("\nTo start a worker for cleanup tasks, run:")
    print("celery -A app.core.celery_app worker -Q cleanup --loglevel=info")

def test_cleanup_task():
    """Test the cleanup task manually"""
    print("Testing cleanup task...")
    try:
        result = cleanup_old_jobs_task.delay(20)
        print(f"Task submitted with ID: {result.id}")
        task_result = result.get(timeout=30)
        print(f"Task result: {task_result}")
    except Exception as e:
        print(f"Error testing cleanup task: {e}")

def test_cleanup_stats():
    """Test the cleanup stats task manually"""
    print("Testing cleanup stats task...")
    try:
        result = get_cleanup_stats_task.delay(20)
        print(f"Stats task submitted with ID: {result.id}")
        task_result = result.get(timeout=30)
        print(f"Stats task result: {task_result}")
    except Exception as e:
        print(f"Error testing stats task: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup job cleanup scheduling")
    parser.add_argument("--test", action="store_true", help="Test cleanup tasks")
    parser.add_argument("--test-stats", action="store_true", help="Test stats task")
    parser.add_argument("--setup", action="store_true", help="Setup cleanup schedule")
    
    args = parser.parse_args()
    
    if args.test:
        test_cleanup_task()
    elif args.test_stats:
        test_cleanup_stats()
    elif args.setup:
        setup_cleanup_schedule()
    else:
        # Default: setup schedule
        setup_cleanup_schedule() 