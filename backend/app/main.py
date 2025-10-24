from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from sqlalchemy import text

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.logging import setup_logging
from app.models.job import Base
from app.db.session import engine
from app.middleware.security import create_security_middleware_stack
# from app.core.error_handlers import setup_error_handlers

# Setup enhanced logging system
from app.core.enhanced_logging import setup_enhanced_logging, health_monitor, log_security_event

# Initialize enhanced logging
enhanced_logger = setup_enhanced_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    yield
    # Shutdown
    logger.info("Shutting down application...")

Base.metadata.create_all(bind=engine)

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
allowed_origins = [
    "http://localhost:3000",  # Development frontend
    "http://127.0.0.1:3000",
    "https://jobflowpro.com",  # Production frontend
    "https://www.jobflowpro.com",
]

# In development, allow all origins for easier testing
if not is_production:
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
        'burst_size': 20 if is_production else 50,
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
        'max_request_size': 50 * 1024 * 1024,  # 50MB for resume uploads
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

# Temporarily disable complex security middleware stack due to middleware chaining issue
# create_security_middleware_stack(
#     app,
#     enable_rate_limiting=True,
#     enable_request_validation=True,
#     enable_security_headers=True,
#     enable_request_logging=True,
#     **security_config
# )

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
async def get_metrics():
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