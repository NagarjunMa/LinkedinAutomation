from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "JobFlow Pro - Job Extraction & Management"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    CORS_ORIGINS: List[AnyHttpUrl] = []  # Will be loaded from environment
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "linkedin_jobs"
    SQLALCHEMY_DATABASE_URI: str | None = None
    
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: str | None, values: dict[str, any]) -> str:
        if isinstance(v, str):
            return v
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB')}"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Celery Configuration
    CELERY_BROKER_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    CELERY_RESULT_BACKEND: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    
    # AI Configuration
    OPENAPI_KEY: str = ""  # OpenAI API key
    OPENAI_MODEL: str = "gpt-4o-mini"  # Cost-efficient model
    OPENAI_MAX_TOKENS: int = 4000  # Token limit for responses
    
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Email Agent Configuration - Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""  # Will be loaded from environment
    GOOGLE_SCOPES: List[str] = [
        "openid",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/userinfo.email"
    ]
    EMAIL_CLASSIFICATION_MODEL: str = "gpt-4o-mini"
    EMAIL_SYNC_FREQUENCY_MINUTES: int = 15
    EMAIL_CONFIDENCE_THRESHOLD: float = 0.8
    AUTO_UPDATE_THRESHOLD: float = 0.85
    DEBUG_EMAIL_PROCESSING: bool = True
    LOG_LEVEL: str = "DEBUG"

    # Email Service Configuration - Resend
    RESEND_API_KEY: str = ""  # Resend API Key
    MAIL_FROM: str = "noreply.jobflow@gmail.com"
    MAIL_FROM_NAME: str = "JobFlow Pro"

    # Fallback SMTP Configuration (if needed)
    MAIL_USERNAME: str = "noreply.jobflow@gmail.com"
    MAIL_PASSWORD: str = ""  # App-specific password for Gmail
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    # File Upload Configuration
    UPLOAD_DIR: str = "uploads"  # Base upload directory
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings() 