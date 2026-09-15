"""Translate transport-neutral application errors into stable HTTP responses."""

from fastapi import HTTPException
from app.schemas.api_errors import APIErrorEnvelope

from app.application.errors import (
    ApplicationError,
    AuthorizationError,
    ExternalServiceError,
    InsufficientBalanceError,
    InvalidOperationError,
    OperationRejectedError,
    RenderError,
    ResourceBusyError,
    ResourceConflictError,
    ResourceNotFoundError,
)


def to_http_exception(error: ApplicationError) -> HTTPException:
    if isinstance(error, InsufficientBalanceError):
        status_code = 402
    elif isinstance(error, AuthorizationError):
        status_code = 403
    elif isinstance(error, ResourceNotFoundError):
        status_code = 404
    elif isinstance(error, ResourceConflictError):
        status_code = 409
    elif isinstance(error, InvalidOperationError):
        status_code = 422
    elif isinstance(error, OperationRejectedError):
        status_code = 422
    elif isinstance(error, ResourceBusyError):
        status_code = 429
    elif isinstance(error, ExternalServiceError):
        status_code = 503
    elif isinstance(error, RenderError):
        status_code = 500
    else:
        status_code = 500
    return HTTPException(status_code=status_code, detail=str(error))


def safe_error_envelope(status_code: int, request_id: str) -> APIErrorEnvelope:
    """Map existing HTTP outcomes without trusting exception or validation text."""
    code, message = {
        400: ("invalid_request", "Check the request and try again."),
        401: ("authentication_required", "Sign in to continue."),
        402: ("insufficient_credits", "Insufficient credits."),
        403: ("access_denied", "Access is unavailable for this request."),
        404: ("resource_not_found", "Resource not found."),
        405: ("method_not_allowed", "Request method not allowed."),
        409: ("resource_conflict", "The request conflicts with the current state."),
        413: ("request_too_large", "The uploaded file or request is too large."),
        415: ("unsupported_media_type", "This file or content type is not supported."),
        422: ("invalid_request", "Check the request and try again."),
        429: ("rate_limited", "Request limit reached. Please wait before trying again."),
        502: ("service_unavailable", "The service is currently unavailable."),
        503: ("service_unavailable", "The service is currently unavailable."),
        504: ("service_unavailable", "The service is currently unavailable."),
    }.get(status_code, ("internal_error", "Request failed. Please try again when ready."))
    # Status alone cannot prove a mutation was rolled back, or distinguish
    # temporary provider throttling from exhausted quota. Never authorize replay.
    return APIErrorEnvelope(code=code, message=message, detail=message,
                            request_id=request_id, retryable=False)
