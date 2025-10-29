from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Database engine configuration optimized for Railway + Supabase
engine_options = {
    "pool_pre_ping": True,
    "pool_recycle": 300,  # Recycle connections every 5 minutes
    "pool_size": 5,       # Small pool for Railway resources
    "max_overflow": 10,   # Allow some overflow connections
    "echo": settings.DEBUG,  # Log SQL in debug mode
}

# Add SSL and connection options for production
if settings.ENVIRONMENT == "production":
    # Force SSL and add connection parameters for better Railway compatibility
    database_uri = settings.SQLALCHEMY_DATABASE_URI

    # Add SSL and other connection parameters if not present
    if "sslmode=" not in database_uri:
        separator = "&" if "?" in database_uri else "?"
        database_uri += f"{separator}sslmode=require"

    # Add connection timeout and other stability parameters
    if "connect_timeout=" not in database_uri:
        separator = "&" if "?" in database_uri else "?"
        database_uri += f"{separator}connect_timeout=10"

    # Use the modified URI
    engine = create_engine(database_uri, **engine_options)
else:
    # Development mode - use as-is
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, **engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 