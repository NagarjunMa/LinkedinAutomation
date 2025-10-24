"""
Standardized Error Handling for FastAPI
Provides consistent error responses and logging
"""

import logging
import traceback
import uuid
from typing import Any, Dict, Optional, Union
from datetime import datetime

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError


logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom API error with enhanced information"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self._generate_error_code()
        self.details = details or {}
        self.user_message = user_message or self._generate_user_message()
        self.timestamp = datetime.now().isoformat()
        self.error_id = str(uuid.uuid4())
        super().__init__(self.message)

    def _generate_error_code(self) -> str:
        """Generate error code based on status code"""
        code_mapping = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMITED",
            500: "INTERNAL_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
            504: "GATEWAY_TIMEOUT"
        }
        return code_mapping.get(self.status_code, "UNKNOWN_ERROR")

    def _generate_user_message(self) -> str:
        """Generate user-friendly message based on status code"""
        user_messages = {
            400: "The request was invalid. Please check your input and try again.",
            401: "Authentication is required to access this resource.",
            403: "You don't have permission to access this resource.",
            404: "The requested resource was not found.",
            405: "This method is not allowed for this resource.",
            409: "The request conflicts with the current state of the resource.",
            422: "The provided data is invalid. Please check your input.",
            429: "Too many requests. Please wait a moment and try again.",
            500: "An internal error occurred. Please try again later.",
            502: "The server is temporarily unavailable. Please try again later.",
            503: "The service is temporarily unavailable. Please try again later.",
            504: "The request timed out. Please try again later."
        }
        return user_messages.get(self.status_code, "An unexpected error occurred.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response"""
        return {
            "error": self.error_code,
            "message": self.user_message,
            "details": self.details,
            "timestamp": self.timestamp,
            "error_id": self.error_id,
            "status_code": self.status_code
        }


class ErrorResponse:
    """Standardized error response builder"""

    @staticmethod
    def create_response(
        error: Union[APIError, Exception],
        request: Optional[Request] = None,
        include_traceback: bool = False
    ) -> JSONResponse:
        """Create standardized error response"""

        # Get request ID if available
        request_id = None
        if request and hasattr(request.state, 'request_id'):
            request_id = request.state.request_id

        if isinstance(error, APIError):
            # Custom API error
            response_data = error.to_dict()
            if request_id:
                response_data["request_id"] = request_id

            # Log error details
            logger.error(
                f"API Error: {error.error_code} - {error.message}",
                extra={
                    "error_id": error.error_id,
                    "status_code": error.status_code,
                    "details": error.details,
                    "request_id": request_id
                }
            )

            return JSONResponse(
                status_code=error.status_code,
                content=response_data
            )

        elif isinstance(error, HTTPException):
            # FastAPI HTTP exception
            api_error = APIError(
                message=str(error.detail),
                status_code=error.status_code
            )
            response_data = api_error.to_dict()
            if request_id:
                response_data["request_id"] = request_id

            logger.error(
                f"HTTP Exception: {error.status_code} - {error.detail}",
                extra={"request_id": request_id}
            )

            return JSONResponse(
                status_code=error.status_code,
                content=response_data
            )

        else:
            # Generic exception
            api_error = APIError(
                message=str(error),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            response_data = api_error.to_dict()
            if request_id:
                response_data["request_id"] = request_id

            # Include traceback in development
            if include_traceback:
                response_data["traceback"] = traceback.format_exc()

            logger.error(
                f"Unhandled Exception: {str(error)}",
                extra={
                    "error_id": api_error.error_id,
                    "request_id": request_id,
                    "traceback": traceback.format_exc()
                }
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=response_data
            )


# Exception handlers for FastAPI


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handler for custom API errors"""
    return ErrorResponse.create_response(exc, request)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for HTTP exceptions"""
    return ErrorResponse.create_response(exc, request)


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handler for Starlette HTTP exceptions"""
    # Convert to FastAPI HTTPException
    fastapi_exc = HTTPException(status_code=exc.status_code, detail=exc.detail)
    return ErrorResponse.create_response(fastapi_exc, request)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for request validation errors"""
    # Format validation errors
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })

    api_error = APIError(
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        details={"validation_errors": errors},
        user_message="The provided data is invalid. Please check the highlighted fields."
    )

    return ErrorResponse.create_response(api_error, request)


async def pydantic_validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handler for Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })

    api_error = APIError(
        message="Data validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        details={"validation_errors": errors}
    )

    return ErrorResponse.create_response(api_error, request)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unhandled exceptions"""
    include_traceback = getattr(request.app.state, 'debug_mode', False)
    return ErrorResponse.create_response(exc, request, include_traceback)


# Pre-defined common errors

class AuthenticationError(APIError):
    """Authentication required error"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_REQUIRED",
            user_message="Please log in to access this resource."
        )


class PermissionError(APIError):
    """Permission denied error"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PERMISSION_DENIED",
            user_message="You don't have permission to perform this action."
        )


class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, resource: str = "Resource", resource_id: str = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" with ID: {resource_id}"

        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            user_message=f"The requested {resource.lower()} was not found."
        )


class ConflictError(APIError):
    """Resource conflict error"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            user_message="This action conflicts with the current state. Please refresh and try again."
        )


class RateLimitError(APIError):
    """Rate limit exceeded error"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
            user_message="Too many requests. Please wait a moment and try again."
        )


class ServiceUnavailableError(APIError):
    """Service unavailable error"""
    def __init__(self, service: str = "Service", retry_after: int = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=f"{service} is temporarily unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            details=details,
            user_message="The service is temporarily unavailable. Please try again later."
        )


# Utility functions

def setup_error_handlers(app) -> None:
    """Setup all error handlers for the FastAPI app"""

    # Custom API errors
    app.add_exception_handler(APIError, api_error_handler)

    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_error_handler)

    # Generic exceptions (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)


def create_error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response"""
    error = APIError(
        message=message,
        status_code=status_code,
        error_code=error_code,
        details=details
    )
    return JSONResponse(
        status_code=status_code,
        content=error.to_dict()
    )