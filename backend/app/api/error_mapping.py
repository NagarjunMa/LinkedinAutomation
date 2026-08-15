"""Translate transport-neutral application errors into stable HTTP responses."""

from fastapi import HTTPException

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
