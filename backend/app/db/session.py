from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

_database_uri = settings.SQLALCHEMY_DATABASE_URI
_is_sqlite = _database_uri.startswith("sqlite")

# Database engine configuration optimized for Railway + Supabase
engine_options = {
    "pool_pre_ping": True,
    "echo": settings.DEBUG,  # Log SQL in debug mode
}

if not _is_sqlite:
    # PostgreSQL-only pool options — not valid for SQLite
    engine_options.update({
        "pool_recycle": 300,  # Recycle connections every 5 minutes
        "pool_size": 5,       # Small pool for Railway resources
        "max_overflow": 10,   # Allow some overflow connections
    })
else:
    # SQLite requires check_same_thread=False for test usage
    engine_options["connect_args"] = {"check_same_thread": False}

# Add SSL and connection options for production
if settings.ENVIRONMENT == "production" and not _is_sqlite:
    # Force SSL and add connection parameters for better Railway compatibility
    database_uri = _database_uri

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
    engine = create_engine(_database_uri, **engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 