import pytest

from app.api.error_mapping import to_http_exception
from app.application.errors import (
    ApplicationError,
    ExternalServiceError,
    InsufficientBalanceError,
    InvalidOperationError,
    OperationRejectedError,
    RenderError,
    ResourceBusyError,
    ResourceNotFoundError,
)


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (InsufficientBalanceError("credits"), 402),
        (ResourceNotFoundError("missing"), 404),
        (InvalidOperationError("invalid"), 422),
        (OperationRejectedError("rejected"), 422),
        (ResourceBusyError("busy"), 429),
        (ExternalServiceError("provider"), 503),
        (RenderError("render"), 500),
        (ApplicationError("unknown"), 500),
    ],
)
def test_application_errors_map_to_stable_http_statuses(error, status_code):
    response = to_http_exception(error)
    assert response.status_code == status_code
    assert response.detail == str(error)
