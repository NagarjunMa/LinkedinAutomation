"""
Application Configuration Settings

This module contains all environment variable configurations for the JobFlow Pro application.
Each setting is documented with its purpose and usage to help new developers understand
the application configuration.

Configuration is loaded from environment variables with sensible defaults for development.
For production deployment, ensure all required environment variables are set.
"""

import json
from typing import List, Optional, Union
from urllib.parse import urlsplit

from pydantic import ConfigDict, field_validator, model_validator
from pydantic_settings import BaseSettings


def _is_exact_https_origin(origin: str) -> bool:
    if "*" in origin or any(character.isspace() for character in origin):
        return False
    parsed = urlsplit(origin)
    try:
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and port is None
        and parsed.username is None
        and parsed.password is None
        and parsed.path in ("", "/")
        and not parsed.query
        and not parsed.fragment
        and origin.rstrip("/") == f"https://{parsed.hostname}"
    )


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class defines all configuration needed for the application to run,
    including database connections, external API keys, and feature flags.
    """

    # ==========================================
    # Application Metadata
    # ==========================================

    PROJECT_NAME: str = "Prism Pro - Job Extraction & Management"
    """The display name of the application"""

    API_V1_STR: str = "/api/v1"
    """Base path for all API endpoints"""

    ENVIRONMENT: str = "development"
    """Current environment: development, staging, production"""

    DEBUG: bool = False
    """Enable debug mode for detailed error messages - disabled by default to reduce SQL logging"""

    FREEMIUM_MONTHLY_CREDITS: int = 90
    """Monthly freemium credit allowance. 90 credits covers ~30 JD tailor+export workflows."""

    ENABLE_BILLING: bool = False
    """Enable paid billing/webhook routes. Kept disabled for the freemium launch."""

    ADMIN_USER_IDS: str = ""
    """Comma-separated Supabase user IDs allowed to access admin-only endpoints."""

    PRISM_PRO_PUBLIC_PREVIEW_ONLY: bool = True
    """Fail closed by default: expose only public-preview backend routes."""

    PUBLIC_FRONTEND_ORIGIN: str = ""
    """Canonical browser origin allowed to call the public-preview API."""

    BACKEND_REPLICA_COUNT: int = 1
    """Declared platform replica count while rate limiting is process-local."""

    WEB_CONCURRENCY: int = 1
    """Uvicorn worker count; must remain one while rate limiting is process-local."""

    WAITLIST_RETENTION_DAYS: int = 180
    """Days after which a waitlist entry is eligible for deletion."""

    WAITLIST_CONSENT_VERSION: str = "2026-09-06"
    """Version of the waitlist contact consent accepted by the visitor."""

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

    CORS_ORIGINS: Union[str, List[str]] = []
    """
    List of allowed origins for CORS requests.
    Example: ["https://frontend.example.com", "https://app.example.com"]
    """

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Parse CORS origins from environment variable.
        Accepts comma-separated string or list format.
        """
        if isinstance(v, str):
            if not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            else:
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    # Fallback to comma split if JSON parse fails
                    return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
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

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
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

    SUPABASE_SERVICE_ROLE_KEY: str = ""
    """
    Supabase service role key for server-side operations.
    This is a privileged secret key — only use on the backend.
    """

    SUPABASE_STORAGE_BUCKET: str = "resume"
    """
    Supabase storage bucket name for PDF exports.
    """

    SUPABASE_SIGNED_URL_TTL_SECONDS: int = 60 * 60 * 24 * 7  # 7 days
    """
    TTL in seconds for signed download URLs generated for stored PDFs.
    """

    PDF_RENDER_TIMEOUT_S: int = 15
    """
    Timeout in seconds for Playwright PDF rendering operations.
    """

    # ==========================================
    # AI Service Configuration
    # ==========================================

    OPENAI_API_KEY: str = ""
    """OpenAI API key for AI-powered features like resume analysis and job matching"""

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

    MAIL_FROM: str = "noreply@prismpro.live"
    """Default from email address for transactional emails"""

    MAIL_FROM_NAME: str = "Prism Pro"
    """Display name for email sender"""

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

    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx"]
    """Allowed file extensions for resume uploads"""

    MAX_PDF_PAGES: int = 10
    """Maximum number of pages accepted by the resume parser"""

    MAX_EXTRACTED_TEXT_CHARS: int = 100_000
    """Maximum extracted resume text retained and parsed"""

    MAX_DOCX_ENTRIES: int = 2_000
    """Maximum number of files permitted inside a DOCX archive"""

    MAX_DOCX_UNCOMPRESSED_SIZE: int = 25 * 1024 * 1024
    """Maximum total uncompressed bytes permitted inside a DOCX archive"""

    MAX_DOCX_COMPRESSION_RATIO: int = 100
    """Maximum aggregate DOCX archive expansion ratio"""

    RESUME_PARSE_TIMEOUT_SECONDS: float = 15.0
    """Maximum wall-clock wait for a resume parser worker"""

    MAX_CONCURRENT_RESUME_PARSERS: int = 2
    """Maximum parser subprocesses allowed per backend instance"""

    RESUME_PARSE_QUEUE_TIMEOUT_SECONDS: float = 1.0
    """Maximum wait for parser capacity before returning a retry response"""

    @field_validator(
        "MAX_UPLOAD_SIZE",
        "MAX_PDF_PAGES",
        "MAX_EXTRACTED_TEXT_CHARS",
        "MAX_DOCX_ENTRIES",
        "MAX_DOCX_UNCOMPRESSED_SIZE",
        "MAX_DOCX_COMPRESSION_RATIO",
        "RESUME_PARSE_TIMEOUT_SECONDS",
        "MAX_CONCURRENT_RESUME_PARSERS",
        "RESUME_PARSE_QUEUE_TIMEOUT_SECONDS",
        "WAITLIST_RETENTION_DAYS",
        "BACKEND_REPLICA_COUNT",
        "WEB_CONCURRENCY",
    )
    def validate_positive_resume_budget(cls, value):
        if value <= 0:
            raise ValueError("Resume processing budgets must be positive")
        return value

    # ==========================================
    # Feature Flags
    # ==========================================

    ENABLE_AI_FEATURES: bool = True
    """Enable/disable AI-powered features (requires OpenAI API key)"""

    ENABLE_ANALYTICS: bool = True
    """Enable/disable analytics and reporting features"""

    ENABLE_LEGACY_JOB_EXTRACTION: bool = False
    """Mount deprecated URL extraction/demo endpoints. Disabled for MVP publication."""

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENVIRONMENT.lower() != "production":
            return self

        missing = []
        for name in (
            "SQLALCHEMY_DATABASE_URI",
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "CORS_ORIGINS",
            "PUBLIC_FRONTEND_ORIGIN",
        ):
            value = getattr(self, name)
            if value in ("", None, []):
                missing.append(name)

        if self.ENABLE_AI_FEATURES and not self.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")

        if self.ENABLE_BILLING:
            for name in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"):
                if not getattr(self, name, ""):
                    missing.append(name)

        database_uri = self.SQLALCHEMY_DATABASE_URI or ""
        if database_uri.startswith("sqlite"):
            raise ValueError("SQLALCHEMY_DATABASE_URI must use PostgreSQL in production")

        if any(origin.startswith(("http://localhost", "http://127.0.0.1")) for origin in self.CORS_ORIGINS):
            raise ValueError("CORS_ORIGINS must not include localhost origins in production")

        invalid_origins = [
            origin
            for origin in self.CORS_ORIGINS
            if not _is_exact_https_origin(origin)
        ]
        if invalid_origins:
            raise ValueError(
                "CORS_ORIGINS must contain exact HTTPS origins without paths, "
                "credentials, queries, fragments, or wildcards"
            )

        if self.PUBLIC_FRONTEND_ORIGIN and not _is_exact_https_origin(
            self.PUBLIC_FRONTEND_ORIGIN
        ):
            raise ValueError("PUBLIC_FRONTEND_ORIGIN must be an exact HTTPS origin")

        if self.PRISM_PRO_PUBLIC_PREVIEW_ONLY:
            if self.CORS_ORIGINS != [self.PUBLIC_FRONTEND_ORIGIN]:
                raise ValueError(
                    "Public preview requires CORS_ORIGINS to contain only "
                    "PUBLIC_FRONTEND_ORIGIN"
                )
            if self.BACKEND_REPLICA_COUNT != 1 or self.WEB_CONCURRENCY != 1:
                raise ValueError(
                    "Public preview requires one backend replica and one worker "
                    "while rate limiting is process-local"
                )

        if self.SUPABASE_STORAGE_BUCKET != "resume":
            raise ValueError("SUPABASE_STORAGE_BUCKET must be 'resume' in production")

        if not self.ADMIN_USER_IDS.strip():
            missing.append("ADMIN_USER_IDS")

        if self.SECRET_KEY == "dev-secret-key-change-in-production" or len(self.SECRET_KEY) < 32:
            missing.append("SECRET_KEY")

        if missing:
            raise ValueError(f"Missing required production settings: {', '.join(sorted(set(missing)))}")

        return self


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
    elif settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        issues.append("SQLALCHEMY_DATABASE_URI must use PostgreSQL in production")

    if not settings.SUPABASE_URL:
        issues.append("SUPABASE_URL is required")

    if not settings.SUPABASE_ANON_KEY:
        issues.append("SUPABASE_ANON_KEY is required")

    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        issues.append("SUPABASE_SERVICE_ROLE_KEY is required")

    if settings.SUPABASE_STORAGE_BUCKET != "resume":
        issues.append("SUPABASE_STORAGE_BUCKET must be 'resume'")

    if any(origin.startswith(("http://localhost", "http://127.0.0.1")) for origin in settings.CORS_ORIGINS):
        issues.append("CORS_ORIGINS must not include localhost origins in production")

    if any(not _is_exact_https_origin(origin) for origin in settings.CORS_ORIGINS):
        issues.append(
            "CORS_ORIGINS must contain exact HTTPS origins without paths, "
            "credentials, queries, fragments, or wildcards"
        )

    if not settings.PUBLIC_FRONTEND_ORIGIN:
        issues.append("PUBLIC_FRONTEND_ORIGIN is required")
    elif not _is_exact_https_origin(settings.PUBLIC_FRONTEND_ORIGIN):
        issues.append("PUBLIC_FRONTEND_ORIGIN must be an exact HTTPS origin")

    if settings.PRISM_PRO_PUBLIC_PREVIEW_ONLY:
        if settings.CORS_ORIGINS != [settings.PUBLIC_FRONTEND_ORIGIN]:
            issues.append(
                "Public preview requires CORS_ORIGINS to contain only "
                "PUBLIC_FRONTEND_ORIGIN"
            )
        if settings.BACKEND_REPLICA_COUNT != 1 or settings.WEB_CONCURRENCY != 1:
            issues.append(
                "Public preview requires one backend replica and one worker "
                "while rate limiting is process-local"
            )

    if not settings.ADMIN_USER_IDS.strip():
        issues.append("ADMIN_USER_IDS is required")

    if settings.SECRET_KEY == "dev-secret-key-change-in-production":
        issues.append("SECRET_KEY must be changed from default value")

    if len(settings.SECRET_KEY) < 32:
        issues.append("SECRET_KEY must be at least 32 characters long")

    # Check optional AI/billing settings that are required when enabled.
    if settings.ENABLE_AI_FEATURES and not settings.OPENAI_API_KEY:
        issues.append("OPENAI_API_KEY is required when AI features are enabled")

    if settings.ENABLE_BILLING:
        import os

        if not os.getenv("STRIPE_API_KEY") and not os.getenv("STRIPE_SECRET_KEY"):
            issues.append("Stripe secret key is required when ENABLE_BILLING=true")
        if not os.getenv("STRIPE_WEBHOOK_SECRET"):
            issues.append("STRIPE_WEBHOOK_SECRET is required when ENABLE_BILLING=true")

    return issues
