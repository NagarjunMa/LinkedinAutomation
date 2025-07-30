from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "LinkedIn Job Scraper"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]  # Frontend URL
    
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
    
    # LinkedIn Scraping Configuration
    LINKEDIN_SCRAPE_INTERVAL: int = 3600  # 1 hour in seconds
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    
    # Job Aggregation APIs
    RSS_APP_API_KEY: str = ""
    INDEED_API_KEY: str = ""
    
    # Job Search Configuration
    MAX_JOBS_PER_SEARCH: int = 500  # Increased to allow all deduplicated jobs
    JOB_CACHE_TIMEOUT: int = 3600  # 1 hour
    
    # AI Configuration
    OPENAPI_KEY: str = ""  # OpenAI API key
    OPENAI_MODEL: str = "gpt-4o-mini"  # Cost-efficient model
    OPENAI_MAX_TOKENS: int = 1000  # Token limit for responses
    
    # Legacy LinkedIn fields (now optional)
    LINKEDIN_EMAIL: str = ""
    LINKEDIN_PASSWORD: str = ""
    LINKEDIN_COOKIE: str = ""
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Email Agent Configuration - Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/email-agent/oauth/callback"
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
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Allow extra fields during migration

settings = Settings() 