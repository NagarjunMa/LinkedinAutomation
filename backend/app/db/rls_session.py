from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from contextvars import ContextVar
from typing import Optional

# Context variable to store current user ID
current_user_id: ContextVar[Optional[str]] = ContextVar('current_user_id', default='demo_user')

# Create engine and session factory
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for getting DB session with RLS context"""
    db = SessionLocal()
    
    try:
        # Set the current user ID for RLS policies
        user_id = current_user_id.get()
        db.execute(text(f"SET app.current_user_id = '{user_id}'"))
        db.commit()  # Commit the setting change
        
        yield db
    finally:
        db.close()

def set_current_user(user_id: str):
    """Set the current user for RLS policies"""
    current_user_id.set(user_id) 