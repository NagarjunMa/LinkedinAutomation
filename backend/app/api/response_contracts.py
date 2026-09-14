"""Opt-in response-validation handling for private document workflows."""

import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import ResponseValidationError
from fastapi.routing import APIRoute


class PrivateResponseRoute(APIRoute):
    """Contain contract failures without exposing validation inputs or tracebacks."""

    validation_logger = logging.getLogger(__name__)
    validation_log_message = "Response contract validation failed"
    validation_detail = "Response could not be processed"

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_response(request: Request):
            try:
                return await handler(request)
            except ResponseValidationError:
                # Validation can follow a committed write. Do not retry or log
                # the exception, inputs, request URL, or user/document identifiers.
                self.validation_logger.error(self.validation_log_message)
                raise HTTPException(500, self.validation_detail) from None

        return safe_response
