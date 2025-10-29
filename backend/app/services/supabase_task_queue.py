"""
Supabase PostgreSQL-based Task Queue
Replaces Celery with PostgreSQL for background task processing
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy.sql import func, text
from app.services.supabase_cache_service import TaskQueue
import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class SupabaseTaskQueue:
    """PostgreSQL-based task queue system"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        self.worker_thread = None
        self.registered_tasks: Dict[str, Callable] = {}

    def _get_db(self) -> Session:
        """Get database session"""
        from app.db.session import SessionLocal
        db = SessionLocal()
        return db

    def register_task(self, name: str, func: Callable):
        """Register a task function"""
        self.registered_tasks[name] = func
        logger.info(f"Registered task: {name}")

    def delay(
        self,
        task_name: str,
        *args,
        priority: int = 5,
        delay_seconds: int = 0,
        **kwargs
    ) -> str:
        """Add a task to the queue (equivalent to Celery .delay())"""
        task_id = str(uuid.uuid4())

        scheduled_for = None
        if delay_seconds > 0:
            scheduled_for = datetime.utcnow() + timedelta(seconds=delay_seconds)

        db = self._get_db()
        try:
            task = TaskQueue(
                id=task_id,
                task_name=task_name,
                args=list(args),
                kwargs=kwargs,
                priority=priority,
                scheduled_for=scheduled_for
            )
            db.add(task)
            db.commit()
            logger.info(f"Queued task {task_name} with ID {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Failed to queue task {task_name}: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def apply_async(
        self,
        task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
        priority: int = 5,
        eta: Optional[datetime] = None
    ) -> str:
        """Add a task to the queue with more options (equivalent to Celery .apply_async())"""
        task_id = str(uuid.uuid4())

        db = self._get_db()
        try:
            task = TaskQueue(
                id=task_id,
                task_name=task_name,
                args=args or [],
                kwargs=kwargs or {},
                priority=priority,
                scheduled_for=eta
            )
            db.add(task)
            db.commit()
            logger.info(f"Queued task {task_name} with ID {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Failed to queue task {task_name}: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def get_pending_tasks(self, limit: int = 10) -> List[TaskQueue]:
        """Get pending tasks ordered by priority and creation time"""
        db = self._get_db()
        try:
            now = datetime.utcnow()
            tasks = db.query(TaskQueue).filter(
                TaskQueue.status == "PENDING",
                # Include tasks with no schedule or scheduled for now/past
                (TaskQueue.scheduled_for.is_(None)) | (TaskQueue.scheduled_for <= now)
            ).order_by(
                TaskQueue.priority.asc(),  # Lower number = higher priority
                TaskQueue.created_at.asc()
            ).limit(limit).all()

            return tasks
        finally:
            db.close()

    def execute_task(self, task: TaskQueue) -> bool:
        """Execute a single task"""
        db = self._get_db()
        try:
            # Update task status to RUNNING
            task.status = "RUNNING"
            task.started_at = datetime.utcnow()
            db.commit()

            # Get the task function
            if task.task_name not in self.registered_tasks:
                raise ValueError(f"Task {task.task_name} not registered")

            task_func = self.registered_tasks[task.task_name]

            # Execute the task
            try:
                result = task_func(*task.args, **task.kwargs)

                # Update task as successful
                task.status = "SUCCESS"
                task.result = json.dumps(result, default=str)
                task.completed_at = datetime.utcnow()

                logger.info(f"Task {task.task_name} ({task.id}) completed successfully")

            except Exception as e:
                # Update task as failed
                task.status = "FAILURE"
                task.error = str(e)
                task.completed_at = datetime.utcnow()
                task.retry_count += 1

                logger.error(f"Task {task.task_name} ({task.id}) failed: {e}")

                # Retry logic (up to 3 retries)
                if task.retry_count < 3:
                    task.status = "PENDING"
                    task.scheduled_for = datetime.utcnow() + timedelta(minutes=5 * task.retry_count)
                    logger.info(f"Task {task.task_name} ({task.id}) scheduled for retry #{task.retry_count}")

            db.commit()
            return task.status == "SUCCESS"

        except Exception as e:
            logger.error(f"Failed to execute task {task.id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def worker_loop(self):
        """Main worker loop that processes tasks"""
        logger.info("Task worker started")

        while self.running:
            try:
                # Get pending tasks
                tasks = self.get_pending_tasks(self.max_workers)

                if not tasks:
                    time.sleep(5)  # Sleep for 5 seconds if no tasks
                    continue

                # Submit tasks to thread pool
                futures = []
                for task in tasks:
                    future = self.executor.submit(self.execute_task, task)
                    futures.append(future)

                # Wait for completion
                for future in futures:
                    try:
                        future.result(timeout=300)  # 5 minute timeout per task
                    except Exception as e:
                        logger.error(f"Task execution error: {e}")

            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(10)  # Sleep longer on errors

        logger.info("Task worker stopped")

    def start_worker(self):
        """Start the background task worker"""
        if self.running:
            logger.warning("Worker is already running")
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self.worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Task worker thread started")

    def stop_worker(self):
        """Stop the background task worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=30)
        self.executor.shutdown(wait=True)
        logger.info("Task worker stopped")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        db = self._get_db()
        try:
            task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
            if not task:
                return None

            return {
                'id': task.id,
                'task_name': task.task_name,
                'status': task.status,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'retry_count': task.retry_count,
                'result': json.loads(task.result) if task.result else None,
                'error': task.error
            }
        finally:
            db.close()

    def cleanup_old_tasks(self, days: int = 7):
        """Clean up old completed/failed tasks"""
        db = self._get_db()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            deleted = db.query(TaskQueue).filter(
                TaskQueue.status.in_(["SUCCESS", "FAILURE"]),
                TaskQueue.completed_at < cutoff
            ).delete()
            db.commit()
            logger.info(f"Cleaned up {deleted} old tasks")
            return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup old tasks: {e}")
            db.rollback()
            return 0
        finally:
            db.close()

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        db = self._get_db()
        try:
            stats = {}

            # Count by status
            for status in ["PENDING", "RUNNING", "SUCCESS", "FAILURE"]:
                count = db.query(TaskQueue).filter(TaskQueue.status == status).count()
                stats[status.lower()] = count

            # Recent activity
            recent_tasks = db.query(TaskQueue).filter(
                TaskQueue.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            stats['recent_24h'] = recent_tasks

            return stats
        finally:
            db.close()

# Singleton instance
supabase_queue = SupabaseTaskQueue()

# Decorator for task registration
def task(name: Optional[str] = None, priority: int = 5):
    """Decorator to register a function as a task"""
    def decorator(func):
        task_name = name or f"{func.__module__}.{func.__name__}"
        supabase_queue.register_task(task_name, func)

        # Add delay method to function for easy queuing
        def delay(*args, **kwargs):
            return supabase_queue.delay(task_name, *args, priority=priority, **kwargs)

        func.delay = delay
        func.apply_async = lambda *args, **kwargs: supabase_queue.apply_async(
            task_name, args=args, kwargs=kwargs, priority=priority
        )

        return func
    return decorator

# Cron-like scheduler
class SupabaseScheduler:
    """Simple cron-like scheduler using PostgreSQL"""

    def __init__(self, task_queue: SupabaseTaskQueue):
        self.task_queue = task_queue
        self.schedules: Dict[str, Dict] = {}
        self.running = False
        self.scheduler_thread = None

    def schedule(
        self,
        task_name: str,
        cron_expression: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ):
        """Schedule a task with cron-like expression (simplified)"""
        self.schedules[task_name] = {
            'cron': cron_expression,
            'args': args or [],
            'kwargs': kwargs or {},
            'last_run': None
        }

    def _should_run(self, schedule: Dict) -> bool:
        """Check if a scheduled task should run (simplified cron logic)"""
        # This is a simplified implementation
        # For production, consider using a proper cron parser like croniter
        now = datetime.utcnow()
        last_run = schedule.get('last_run')

        if not last_run:
            return True

        # Simple: run every hour if last run was more than an hour ago
        return (now - last_run) > timedelta(hours=1)

    def scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                now = datetime.utcnow()

                for task_name, schedule in self.schedules.items():
                    if self._should_run(schedule):
                        self.task_queue.delay(
                            task_name,
                            *schedule['args'],
                            **schedule['kwargs']
                        )
                        schedule['last_run'] = now

                time.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(60)

    def start(self):
        """Start the scheduler"""
        if self.running:
            return

        self.running = True
        self.scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Task scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        logger.info("Task scheduler stopped")

# Singleton scheduler
supabase_scheduler = SupabaseScheduler(supabase_queue)