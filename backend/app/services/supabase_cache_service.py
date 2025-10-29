"""
Supabase PostgreSQL-based Caching Service
Replaces Redis with PostgreSQL for caching, sessions, and temporary data storage
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import func, text
from app.db.base_class import Base

logger = logging.getLogger(__name__)

class CacheEntry(Base):
    """PostgreSQL table for caching key-value pairs"""
    __tablename__ = "cache_entries"

    key = Column(String(255), primary_key=True, index=True)
    value = Column(Text, nullable=False)  # JSON serialized data
    expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=func.now())
    tags = Column(JSON, default=list)  # For cache invalidation by tags

class TaskQueue(Base):
    """PostgreSQL table for Celery-like task queue"""
    __tablename__ = "task_queue"

    id = Column(String(255), primary_key=True)  # Task ID
    task_name = Column(String(255), nullable=False, index=True)
    args = Column(JSON, default=list)
    kwargs = Column(JSON, default=dict)
    status = Column(String(50), default="PENDING", index=True)  # PENDING, RUNNING, SUCCESS, FAILURE
    result = Column(Text, nullable=True)  # JSON serialized result
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    priority = Column(Integer, default=5, index=True)  # 1=highest, 10=lowest
    scheduled_for = Column(DateTime, nullable=True, index=True)  # For delayed tasks

class SessionStore(Base):
    """PostgreSQL table for session storage"""
    __tablename__ = "session_store"

    session_id = Column(String(255), primary_key=True, index=True)
    data = Column(Text, nullable=False)  # JSON serialized session data
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SupabaseCacheService:
    """PostgreSQL-based caching service using Supabase"""

    def __init__(self):
        self.default_ttl = 3600  # 1 hour default TTL

    def _get_db(self) -> Session:
        """Get database session"""
        from app.db.session import SessionLocal
        db = SessionLocal()
        return db

    def _serialize_value(self, value: Any) -> str:
        """Serialize value to JSON string"""
        try:
            return json.dumps(value, default=str)
        except Exception as e:
            logger.error(f"Failed to serialize cache value: {e}")
            return json.dumps(str(value))

    def _deserialize_value(self, value: str) -> Any:
        """Deserialize JSON string to value"""
        try:
            return json.loads(value)
        except Exception as e:
            logger.error(f"Failed to deserialize cache value: {e}")
            return value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Set cache entry with optional TTL and tags"""
        db = self._get_db()
        try:
            expires_at = None
            if ttl or self.default_ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)

            serialized_value = self._serialize_value(value)

            # Upsert cache entry
            cache_entry = db.query(CacheEntry).filter(CacheEntry.key == key).first()
            if cache_entry:
                cache_entry.value = serialized_value
                cache_entry.expires_at = expires_at
                cache_entry.updated_at = func.now()
                cache_entry.tags = tags or []
            else:
                cache_entry = CacheEntry(
                    key=key,
                    value=serialized_value,
                    expires_at=expires_at,
                    tags=tags or []
                )
                db.add(cache_entry)

            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get(self, key: str) -> Optional[Any]:
        """Get cache entry and update access statistics"""
        db = self._get_db()
        try:
            cache_entry = db.query(CacheEntry).filter(CacheEntry.key == key).first()

            if not cache_entry:
                return None

            # Check if expired
            if cache_entry.expires_at and cache_entry.expires_at < datetime.utcnow():
                self.delete(key)
                return None

            # Update access statistics
            cache_entry.access_count += 1
            cache_entry.last_accessed = func.now()
            db.commit()

            return self._deserialize_value(cache_entry.value)
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
        finally:
            db.close()

    def delete(self, key: str) -> bool:
        """Delete cache entry"""
        db = self._get_db()
        try:
            deleted = db.query(CacheEntry).filter(CacheEntry.key == key).delete()
            db.commit()
            return deleted > 0
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def exists(self, key: str) -> bool:
        """Check if cache key exists and is not expired"""
        return self.get(key) is not None

    def clear_expired(self) -> int:
        """Clear expired cache entries"""
        db = self._get_db()
        try:
            deleted = db.query(CacheEntry).filter(
                CacheEntry.expires_at < datetime.utcnow()
            ).delete()
            db.commit()
            logger.info(f"Cleared {deleted} expired cache entries")
            return deleted
        except Exception as e:
            logger.error(f"Failed to clear expired entries: {e}")
            db.rollback()
            return 0
        finally:
            db.close()

    def clear_by_tags(self, tags: List[str]) -> int:
        """Clear cache entries by tags"""
        db = self._get_db()
        try:
            # Find entries that contain any of the specified tags
            deleted = 0
            for tag in tags:
                result = db.query(CacheEntry).filter(
                    func.json_array_contains(CacheEntry.tags, tag)
                ).delete()
                deleted += result

            db.commit()
            logger.info(f"Cleared {deleted} cache entries by tags: {tags}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to clear cache by tags {tags}: {e}")
            db.rollback()
            return 0
        finally:
            db.close()

    def flush_all(self) -> bool:
        """Clear all cache entries"""
        db = self._get_db()
        try:
            db.query(CacheEntry).delete()
            db.commit()
            logger.info("Flushed all cache entries")
            return True
        except Exception as e:
            logger.error(f"Failed to flush cache: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        db = self._get_db()
        try:
            total_entries = db.query(CacheEntry).count()
            expired_entries = db.query(CacheEntry).filter(
                CacheEntry.expires_at < datetime.utcnow()
            ).count()

            most_accessed = db.query(CacheEntry).order_by(
                CacheEntry.access_count.desc()
            ).limit(10).all()

            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'active_entries': total_entries - expired_entries,
                'most_accessed_keys': [
                    {'key': entry.key, 'access_count': entry.access_count}
                    for entry in most_accessed
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
        finally:
            db.close()

    # Convenience methods for common patterns
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple cache entries"""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple cache entries"""
        success = True
        for key, value in mapping.items():
            if not self.set(key, value, ttl):
                success = False
        return success

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric cache value"""
        current = self.get(key)
        if current is None:
            current = 0
        try:
            new_value = int(current) + amount
            self.set(key, new_value)
            return new_value
        except (ValueError, TypeError):
            return None

    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement numeric cache value"""
        return self.incr(key, -amount)

# Singleton instance
supabase_cache = SupabaseCacheService()

# Decorator for method caching
def cache_result(key_template: str, ttl: int = 3600, tags: Optional[List[str]] = None):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from template and arguments
            cache_key = key_template.format(*args, **kwargs)

            # Try to get from cache first
            cached_result = supabase_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            supabase_cache.set(cache_key, result, ttl, tags)
            return result
        return wrapper
    return decorator