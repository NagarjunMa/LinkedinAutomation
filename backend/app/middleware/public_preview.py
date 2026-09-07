"""Fail-closed access policy for the public promotional deployment."""

from collections.abc import Collection

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response


class PublicPreviewAccessMiddleware(BaseHTTPMiddleware):
    """Deny product API access while allowing a small explicit public surface."""

    def __init__(
        self,
        app,
        *,
        enabled: bool = True,
        allowed_paths: Collection[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.allowed_paths = frozenset(
            allowed_paths or {"/health", "/api/v1/waitlist"}
        )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        path = request.url.path.rstrip("/") or "/"
        if self.enabled and path not in self.allowed_paths:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Product access is unavailable during the private preview."
                },
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                    "Pragma": "no-cache",
                    "X-Robots-Tag": "noindex, nofollow, nosnippet, noarchive",
                },
            )

        return await call_next(request)
