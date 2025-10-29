"""
Application Configuration Settings

This module contains all environment variable configurations for the JobFlow Pro application.
Each setting is documented with its purpose and usage to help new developers understand
the application configuration.

Configuration is loaded from environment variables with sensible defaults for development.
For production deployment, ensure all required environment variables are set.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class defines all configuration needed for the application to run,
    including database connections, external API keys, and feature flags.
    """

    # ==========================================
    # Application Metadata
    # ==========================================

    PROJECT_NAME: str = "JobFlow Pro - Job Extraction & Management"
    """The display name of the application"""

    API_V1_STR: str = "/api/v1"
    """Base path for all API endpoints"""

    ENVIRONMENT: str = "development"
    """Current environment: development, staging, production"""

    DEBUG: bool = True
    """Enable debug mode for detailed error messages"""

    # ==========================================
    # Security Configuration
    # ==========================================

    SECRET_KEY: str = "dev-secret-key-change-in-production"
    """
    Secret key for JWT token signing and other cryptographic operations.
    MUST be a strong, unique value in production (32+ characters).
    """

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    """JWT token expiration time in minutes"""

    # ==========================================
    # CORS Configuration
    # ==========================================

    CORS_ORIGINS: List[str] = []
    """
    List of allowed origins for CORS requests.
    Example: ["https://frontend.example.com", "https://app.example.com"]
    """

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """
        Parse CORS origins from environment variable.
        Accepts comma-separated string or list format.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(f"Invalid CORS_ORIGINS format: {v}")

    # ==========================================
    # Database Configuration (Supabase PostgreSQL)
    # ==========================================

    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    """
    Complete database connection URI for Supabase PostgreSQL.
    Format: postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
    """

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def validate_database_uri(cls, v: Optional[str]) -> str:
        """
        Validate and return the database URI.
        In production, this should always be provided as an environment variable.
        """
        if not v:
            raise ValueError("SQLALCHEMY_DATABASE_URI is required")
        return v

    # ==========================================
    # Supabase Configuration
    # ==========================================

    SUPABASE_URL: str = ""
    """
    Supabase project URL.
    Format: https://[your-project-ref].supabase.co
    """

    SUPABASE_ANON_KEY: str = ""
    """
    Supabase anonymous key for client-side authentication.
    This is safe to expose in frontend applications.
    """

    SUPABASE_JWT_SECRET: str = ""
    """
    Supabase JWT secret for token verification.
    Keep this secret and never expose in frontend code.
    """

    # ==========================================
    # AI Service Configuration
    # ==========================================

    OPENAI_API_KEY: str = ""
    """OpenAI API key for AI-powered features like resume analysis and job matching"""

    @property
    def OPENAPI_KEY(self) -> str:
        """
        Backward compatibility alias for OPENAI_API_KEY.
        Some legacy code still uses OPENAPI_KEY.
        """
        return self.OPENAI_API_KEY

    @property
    def CELERY_BROKER_URL(self) -> str:
        """
        Backward compatibility for legacy Celery configuration.
        Returns dummy value since we now use Supabase task queue.
        """
        return "memory://"  # In-memory broker for compatibility

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """
        Backward compatibility for legacy Celery configuration.
        Returns dummy value since we now use Supabase task queue.
        """
        return "cache+memory://"  # In-memory backend for compatibility

    OPENAI_MODEL: str = "gpt-4o-mini"
    """OpenAI model to use for text generation (optimized for cost-efficiency)"""

    OPENAI_MAX_TOKENS: int = 4000
    """Maximum tokens for OpenAI API responses"""

    # ==========================================
    # Email Service Configuration
    # ==========================================

    RESEND_API_KEY: str = ""
    """
    Resend API key for transactional emails.
    Alternative to SMTP for better deliverability.
    """

    MAIL_FROM: str = "noreply@jobflow.com"
    """Default from email address for transactional emails"""

    MAIL_FROM_NAME: str = "JobFlow Pro"
    """Display name for email sender"""

    # ==========================================
    # Google OAuth Configuration (Email Agent)
    # ==========================================

    GOOGLE_CLIENT_ID: str = ""
    """Google OAuth client ID for Gmail integration"""

    GOOGLE_CLIENT_SECRET: str = ""
    """Google OAuth client secret for Gmail integration"""

    GOOGLE_REDIRECT_URI: str = ""
    """OAuth redirect URI for Google authentication flow"""

    GOOGLE_SCOPES: List[str] = [
        "openid",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/userinfo.email"
    ]
    """Gmail API scopes required for email scanning features"""

    # ==========================================
    # Email Processing Configuration
    # ==========================================

    EMAIL_CLASSIFICATION_MODEL: str = "gpt-4o-mini"
    """AI model for email classification and job status extraction"""

    EMAIL_SYNC_FREQUENCY_MINUTES: int = 15
    """How often to sync emails from Gmail (in minutes)"""

    EMAIL_CONFIDENCE_THRESHOLD: float = 0.8
    """Minimum confidence score for automatic email classification"""

    AUTO_UPDATE_THRESHOLD: float = 0.85
    """Confidence threshold for automatic job status updates"""

    # ==========================================
    # Logging Configuration
    # ==========================================

    LOG_LEVEL: str = "INFO"
    """Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"""

    # ==========================================
    # File Upload Configuration
    # ==========================================

    UPLOAD_DIR: str = "uploads"
    """Directory for file uploads (resumes, documents)"""

    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    """Maximum file upload size in bytes"""

    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    """Allowed file extensions for resume uploads"""

    # ==========================================
    # Feature Flags
    # ==========================================

    ENABLE_EMAIL_SCANNING: bool = True
    """Enable/disable email scanning functionality"""

    ENABLE_AI_FEATURES: bool = True
    """Enable/disable AI-powered features (requires OpenAI API key)"""

    ENABLE_ANALYTICS: bool = True
    """Enable/disable analytics and reporting features"""

    class Config:
        """Pydantic configuration"""
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Ignore unknown environment variables


# Global settings instance
settings = Settings()


def validate_production_config() -> List[str]:
    """
    Validate that all required configuration for production is present.

    Returns:
        List of missing or invalid configuration items
    """
    issues = []

    # Check required production settings
    if not settings.SQLALCHEMY_DATABASE_URI:
        issues.append("SQLALCHEMY_DATABASE_URI is required")

    if not settings.SUPABASE_URL:
        issues.append("SUPABASE_URL is required")

    if not settings.SUPABASE_ANON_KEY:
        issues.append("SUPABASE_ANON_KEY is required")

    if not settings.SUPABASE_JWT_SECRET:
        issues.append("SUPABASE_JWT_SECRET is required")

    if settings.SECRET_KEY == "dev-secret-key-change-in-production":
        issues.append("SECRET_KEY must be changed from default value")

    if len(settings.SECRET_KEY) < 32:
        issues.append("SECRET_KEY must be at least 32 characters long")

    # Check optional but recommended settings
    if settings.ENABLE_AI_FEATURES and not settings.OPENAI_API_KEY:
        issues.append("OPENAI_API_KEY is required when AI features are enabled")

    if not settings.RESEND_API_KEY:
        issues.append("RESEND_API_KEY is recommended for email functionality")

    return issues