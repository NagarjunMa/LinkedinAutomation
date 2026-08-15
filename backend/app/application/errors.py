"""Transport-neutral errors raised by application services."""


class ApplicationError(RuntimeError):
    """Base class for stable use-case failures."""


class ResourceNotFoundError(ApplicationError):
    """The requested owned resource is unavailable to the caller."""


class AuthorizationError(ApplicationError):
    """The caller is authenticated but cannot perform the operation."""


class ResourceConflictError(ApplicationError):
    """The operation conflicts with another owner's use of a resource."""


class InvalidOperationError(ApplicationError):
    """The request is structurally valid but cannot be performed."""


class OperationRejectedError(ApplicationError):
    """A safety guard rejected generated content."""


class ResourceBusyError(ApplicationError):
    """A bounded worker pool cannot accept more work right now."""


class ExternalServiceError(ApplicationError):
    """An external dependency or recoverable workflow failed."""


class RenderError(ApplicationError):
    """A PDF render failed after an audit record was prepared."""


class InsufficientBalanceError(ApplicationError):
    """The user cannot fund the requested operation."""


class CreditReconciliationError(ExternalServiceError):
    """A failed paid operation could not be refunded automatically."""
