"""Public, content-free errors for the resume/JD transport boundary."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class APIFieldError(BaseModel):
    location: Literal["body", "path", "query"]
    code: Literal["invalid"] = "invalid"


class APIErrorEnvelope(BaseModel):
    code: Literal[
        "invalid_request", "authentication_required", "insufficient_credits",
        "access_denied", "resource_not_found", "method_not_allowed",
        "resource_conflict", "request_too_large", "unsupported_media_type",
        "rate_limited", "service_unavailable", "internal_error",
    ]
    message: str = Field(max_length=200)
    request_id: UUID
    retryable: bool
    detail: str = Field(max_length=200, description="Safe compatibility alias for message")
    field_errors: list[APIFieldError] | None = Field(default=None, max_length=3)


ERROR_RESPONSES = {
    status: {"model": APIErrorEnvelope, "headers": {
        "X-Request-ID": {"schema": {"type": "string", "format": "uuid"}},
    }}
    for status in ("4XX", "422", "5XX")
}
