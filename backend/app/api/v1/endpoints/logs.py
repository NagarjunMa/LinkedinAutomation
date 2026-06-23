"""
Frontend Logging Endpoint
Centralizes frontend error logging to backend's enhanced logging system
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging
import json
from app.core.enhanced_logging import enhanced_logger
from app.core.rate_limiter import RateLimiter
from app.core.auth import decode_supabase_jwt

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Rate limiter to prevent log spam (100 logs per minute per IP)
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

class FrontendLogSchema(BaseModel):
    """Schema for frontend log entries"""
    errorId: str = Field(..., description="Unique error identifier")
    message: str = Field(..., max_length=5000, description="Error message")
    stack: Optional[str] = Field(None, max_length=20000, description="Error stack trace")
    componentStack: Optional[str] = Field(None, max_length=10000, description="React component stack")
    url: str = Field(..., max_length=2000, description="URL where error occurred")
    userAgent: str = Field(..., max_length=1000, description="Browser user agent")
    userId: Optional[str] = Field(None, description="User ID if authenticated")
    sessionId: Optional[str] = Field(None, description="Session identifier")
    level: str = Field(default="error", description="Log level")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context data")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Client timestamp")

    @field_validator('level')
    def validate_level(cls, v):
        allowed_levels = ['error', 'warn', 'info', 'debug']
        if v not in allowed_levels:
            return 'error'  # Default to error for safety
        return v

    @field_validator('metadata')
    def validate_metadata(cls, v):
        if v is None:
            return {}
        # Ensure metadata doesn't exceed reasonable size
        try:
            serialized = json.dumps(v)
            if len(serialized) > 5000:  # 5KB limit
                return {"error": "metadata_too_large", "size": len(serialized)}
        except (TypeError, ValueError):
            return {"error": "metadata_not_serializable"}
        return v

class FrontendLogBatchSchema(BaseModel):
    """Schema for batch log entries"""
    logs: List[FrontendLogSchema] = Field(..., max_length=10, description="Batch of log entries")

    @field_validator('logs')
    def validate_logs(cls, v):
        if len(v) > 10:
            # Truncate to prevent abuse
            return v[:10]
        return v

class LogResponse(BaseModel):
    """Response schema for log endpoints"""
    success: bool
    message: str
    processed: int
    errors: Optional[List[str]] = None

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def get_logger() -> logging.Logger:
    """Get the frontend logger instance"""
    return logging.getLogger('frontend')


def get_verified_log_user_id(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[str]:
    """Return the JWT subject for log attribution, ignoring caller-supplied IDs."""
    if not credentials:
        return None
    try:
        payload = decode_supabase_jwt(credentials.credentials)
    except Exception:
        return None
    return payload.get("sub")

@router.post("/frontend", response_model=LogResponse)
async def log_frontend_error(
    log_entry: FrontendLogSchema,
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Log a single frontend error to the centralized logging system
    """
    client_ip = get_client_ip(request)

    # Apply rate limiting
    try:
        rate_limiter.check_rate_limit(client_ip)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for frontend logging"
        )

    try:
        frontend_logger = get_logger()
        verified_user_id = get_verified_log_user_id(credentials)

        # Create log context
        log_context = {
            'frontend_error': True,
            'error_id': log_entry.errorId,
            'client_ip': client_ip,
            'user_id': verified_user_id,
            'session_id': log_entry.sessionId,
            'url': log_entry.url,
            'user_agent': log_entry.userAgent,
            'component_stack': log_entry.componentStack,
            'client_timestamp': log_entry.timestamp.isoformat(),
            'server_timestamp': datetime.now(timezone.utc).isoformat(),
            'metadata': log_entry.metadata
        }

        # Add authentication context if available and verified
        if verified_user_id:
            log_context['authenticated'] = True

        # Log based on level
        log_message = f"Frontend {log_entry.level}: {log_entry.message}"

        if log_entry.level == 'error':
            if log_entry.stack:
                # Create a synthetic exception-like log entry
                log_context['stack_trace'] = log_entry.stack
            frontend_logger.error(log_message, extra=log_context)
        elif log_entry.level == 'warn':
            frontend_logger.warning(log_message, extra=log_context)
        elif log_entry.level == 'info':
            frontend_logger.info(log_message, extra=log_context)
        else:  # debug
            frontend_logger.debug(log_message, extra=log_context)

        return LogResponse(
            success=True,
            message="Log entry recorded successfully",
            processed=1
        )

    except Exception as e:
        # Log the logging error (meta!)
        backend_logger = logging.getLogger('backend.logging')
        backend_logger.error(
            "Failed to process frontend log entry",
            extra={
                'error': str(e),
                'error_id': log_entry.errorId,
                'client_ip': client_ip,
                'url': log_entry.url
            }
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process log entry"
        )

@router.post("/frontend/batch", response_model=LogResponse)
async def log_frontend_errors_batch(
    batch: FrontendLogBatchSchema,
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Log multiple frontend errors in a single request (more efficient)
    """
    client_ip = get_client_ip(request)

    # Apply rate limiting (stricter for batch)
    try:
        rate_limiter.check_rate_limit(client_ip, cost=len(batch.logs))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for batch frontend logging"
        )

    processed = 0
    errors = []
    frontend_logger = get_logger()
    verified_user_id = get_verified_log_user_id(credentials)

    for log_entry in batch.logs:
        try:
            # Create log context for each entry
            log_context = {
                'frontend_error': True,
                'batch_processing': True,
                'error_id': log_entry.errorId,
                'client_ip': client_ip,
                'user_id': verified_user_id,
                'session_id': log_entry.sessionId,
                'url': log_entry.url,
                'user_agent': log_entry.userAgent,
                'component_stack': log_entry.componentStack,
                'client_timestamp': log_entry.timestamp.isoformat(),
                'server_timestamp': datetime.now(timezone.utc).isoformat(),
                'metadata': log_entry.metadata
            }

            if verified_user_id:
                log_context['authenticated'] = True

            # Log based on level
            log_message = f"Frontend {log_entry.level}: {log_entry.message}"

            if log_entry.level == 'error':
                if log_entry.stack:
                    log_context['stack_trace'] = log_entry.stack
                frontend_logger.error(log_message, extra=log_context)
            elif log_entry.level == 'warn':
                frontend_logger.warning(log_message, extra=log_context)
            elif log_entry.level == 'info':
                frontend_logger.info(log_message, extra=log_context)
            else:  # debug
                frontend_logger.debug(log_message, extra=log_context)

            processed += 1

        except Exception as e:
            error_msg = f"Failed to process log entry {log_entry.errorId}: {str(e)}"
            errors.append(error_msg)

    if errors:
        # Log batch processing issues
        backend_logger = logging.getLogger('backend.logging')
        backend_logger.warning(
            f"Batch frontend logging had {len(errors)} failures",
            extra={
                'total_logs': len(batch.logs),
                'processed': processed,
                'failed': len(errors),
                'client_ip': client_ip,
                'errors': errors[:5]  # Limit error details
            }
        )

    return LogResponse(
        success=processed > 0,
        message=f"Processed {processed}/{len(batch.logs)} log entries",
        processed=processed,
        errors=errors if errors else None
    )

@router.get("/frontend/health")
async def frontend_logging_health():
    """
    Health check endpoint for frontend logging service
    """
    try:
        # Test that we can create log entries
        test_logger = get_logger()
        test_logger.info(
            "Frontend logging health check",
            extra={
                'health_check': True,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )

        return {
            "status": "healthy",
            "service": "frontend-logging",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "enhanced_logging_available": enhanced_logger is not None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Frontend logging service unhealthy: {str(e)}"
        )
