"""Bounded response normalization, including early security-middleware denials."""

import logging
from uuid import uuid4

from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.error_mapping import safe_error_envelope

logger = logging.getLogger(__name__)
PREFIXES = ("/api/v1/resumes", "/api/v1/jd")


class WorkflowErrorMiddleware:
    def __init__(self, app: ASGIApp, *, cors_options: dict):
        self.app = app
        # Reuse exactly the existing policy, but cover early failures for these
        # routes too. Unrelated routes keep their original middleware behavior.
        self.workflow_app = CORSMiddleware(self.handle, **cors_options)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        path = scope.get("path", "")
        if scope["type"] != "http" or not any(path == p or path.startswith(p + "/") for p in PREFIXES):
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        if "origin" in headers:
            # Apply response headers only. The existing inner CORS middleware
            # must retain preflight handling AFTER preview/rate/size enforcement.
            await self.workflow_app.simple_response(scope, receive, send, request_headers=headers)
        else:
            await self.handle(scope, receive, send)

    async def handle(self, scope: Scope, receive: Receive, send: Send):
        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        started = False
        replaced = False

        def error_response(status: int) -> JSONResponse:
            logger.warning("Workflow request failed", extra={"request_id": request_id, "status_code": status})
            return JSONResponse(
                safe_error_envelope(status, request_id).model_dump(mode="json", exclude_none=True),
                status_code=status,
                headers={"X-Request-ID": request_id, "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
            )

        async def send_response(message: Message):
            nonlocal started, replaced
            if message["type"] == "http.response.start":
                started = True
                if message["status"] >= 400:
                    replaced = True
                    response = error_response(message["status"])
                    # Preserve protocol, cookies, rate-limit and security headers;
                    # discard representation metadata for the replaced body.
                    excluded = {
                        b"content-type", b"content-length", b"content-encoding",
                        b"content-range", b"content-disposition", b"etag",
                        b"content-md5", b"digest", b"x-request-id", b"cache-control",
                    }
                    response.raw_headers.extend(
                        (k, v) for k, v in message.get("headers", [])
                        if k.lower() not in excluded
                    )
                    await response(scope, receive, send)
                    return
                headers = [
                    (k, v) for k, v in message.get("headers", [])
                    if k.lower() != b"x-request-id"
                ]
                message = {**message, "headers": headers + [(b"x-request-id", request_id.encode())]}
            if not replaced:
                await send(message)

        try:
            await self.app(scope, receive, send_response)
        except Exception:
            # Do not log exception text/tracebacks: they may contain documents,
            # provider bodies or SQL. Headers already sent cannot be rewritten.
            if started:
                logger.error("Workflow response interrupted", extra={"request_id": request_id})
                if replaced:
                    return
                raise RuntimeError("Workflow response interrupted") from None
            await error_response(500)(scope, receive, send)
