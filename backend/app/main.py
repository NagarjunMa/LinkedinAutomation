from dotenv import load_dotenv

# Load .env into os.environ before any app modules import — keeps os.getenv()
# callers working without requiring uvicorn --env-file. On Railway/Vercel/Docker
# this is a no-op when no .env file is present; platform env vars are already
# in os.environ. See TECH_DEBT.md for the longer-term settings.X migration.
load_dotenv()

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from sqlalchemy import text

from app.core.config import settings, validate_production_config
from app.core.auth import require_admin_user
from app.api.v1.api import api_router
from app.db.session import engine
# from app.core.error_handlers import setup_error_handlers

# Setup enhanced logging system
from app.core.enhanced_logging import setup_enhanced_logging, health_monitor, validate_railway_config

# Initialize enhanced logging
enhanced_logger = setup_enhanced_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Prism Pro application...")

    if is_production:
        production_issues = validate_production_config()
        if production_issues:
            issue_list = "; ".join(production_issues)
            logger.error("Production configuration validation failed: %s", issue_list)
            raise RuntimeError(f"Production configuration validation failed: {issue_list}")


    # Validate Railway configuration if deployed
    if "RAILWAY_DEPLOYMENT_ID" in os.environ:
        config_valid = validate_railway_config()
        if not config_valid:
            logger.error("Railway configuration validation failed - some features may not work")
        else:
            logger.info("Railway configuration validated successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")

# Determine if running in production
is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Job Extraction & Management API",
    version="1.0.0",
    lifespan=lifespan,
    # Hide docs in production for security
    docs_url="/docs" if not is_production else None,
    redoc_url="/redoc" if not is_production else None,
    openapi_url="/openapi.json" if not is_production else None,
)

# Store production state in app for middleware access
app.state.is_production = is_production
app.state.debug_mode = not is_production

# Setup error handlers first (temporarily disabled)
# setup_error_handlers(app)

# Enhanced CORS middleware with tighter security
allowed_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else [
    "http://localhost:3000",  # Development frontend
    "http://127.0.0.1:3000",
]

# In development, allow all origins for easier testing if no specific origins are set
if not is_production and not settings.CORS_ORIGINS:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID",
        "X-API-Key"
    ],
    expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-Remaining"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Setup comprehensive security middleware stack
security_config = {
    'rate_limit': {
        'requests_per_minute': 100 if is_production else 1000,
        'requests_per_hour': 2000 if is_production else 10000,
        'burst_size': 20 if is_production else 1000,
        'route_limits': {
            '/api/v1/resumes/upload': {
                'requests_per_minute': 6 if is_production else 1000,
                'requests_per_hour': 60 if is_production else 10000,
                'burst_size': 3 if is_production else 1000,
            },
            '/api/v1/resumes': {
                'requests_per_minute': 20 if is_production else 1000,
                'requests_per_hour': 200 if is_production else 10000,
                'burst_size': 8 if is_production else 1000,
            },
            '/api/v1/jd/analyze': {
                'requests_per_minute': 8 if is_production else 1000,
                'requests_per_hour': 80 if is_production else 10000,
                'burst_size': 4 if is_production else 1000,
            },
            '/api/v1/jd': {
                'requests_per_minute': 20 if is_production else 1000,
                'requests_per_hour': 200 if is_production else 10000,
                'burst_size': 8 if is_production else 1000,
            },
            '/api/v1/exports': {
                'requests_per_minute': 10 if is_production else 1000,
                'requests_per_hour': 100 if is_production else 10000,
                'burst_size': 4 if is_production else 1000,
            },
            '/api/v1/tailored-resumes': {
                'requests_per_minute': 20 if is_production else 1000,
                'requests_per_hour': 200 if is_production else 10000,
                'burst_size': 8 if is_production else 1000,
            },
        },
        'whitelist_ips': [
            '127.0.0.1',
            '::1',
            '10.0.0.0/8',
            '172.16.0.0/12',
            '192.168.0.0/16'
        ] if not is_production else [],
        'rate_limit_by_user': True
    },
    'validation': {
        'max_request_size': 50 * 1024 * 1024,
        # Allow multipart framing while rejecting declared oversized resume
        # uploads before Starlette parses the request body.
        'route_size_limits': {
            '/api/v1/resumes/upload': settings.MAX_UPLOAD_SIZE + 1024 * 1024,
        },
        'blocked_user_agents': ['sqlmap', 'nikto', 'nmap'] if is_production else [],
        'require_user_agent': is_production
    },
    'headers': {
        'csp_directives': {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data: blob:",
            "font-src": "'self' data:",
            "connect-src": "'self'",
            "frame-src": "'none'",
            "object-src": "'none'",
        }
    },
    'logging': {
        'log_request_body': not is_production,  # Only in development
        'log_response_body': False  # Never log response bodies
    }
}

# Add basic security headers middleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.middleware.security import RateLimitMiddleware, RequestValidationMiddleware

class BasicSecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Add essential security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

app.add_middleware(BasicSecurityHeadersMiddleware)

# Activate request protection without the older body-logging middleware. These
# middlewares do not consume request bodies, so uploads remain safe.
app.add_middleware(RequestValidationMiddleware, **security_config["validation"])
app.add_middleware(RateLimitMiddleware, **security_config["rate_limit"])

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with metrics"""
    try:
        health_metrics = health_monitor.get_health_metrics()

        # Test database connectivity
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        health_metrics.update({
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "environment": os.getenv("ENVIRONMENT", "development")
        })

        logger.info("Health check successful", extra={"metrics": health_metrics})
        return JSONResponse(content=health_metrics, status_code=200)

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "version": "1.0.0"
            },
            status_code=503
        )

@app.get("/metrics")
async def get_metrics(_: str = Depends(require_admin_user)):
    """Detailed metrics endpoint for monitoring"""
    try:
        metrics = health_monitor.get_health_metrics()

        # Add basic system info
        import platform
        metrics.update({
            "system": {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "hostname": platform.node()
            }
        })

        return JSONResponse(content=metrics, status_code=200)
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}", exc_info=True)
        return JSONResponse(
            content={"error": "Metrics unavailable"},
            status_code=500
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to JobFlow Pro - AI-Powered Job Extraction & Management API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
