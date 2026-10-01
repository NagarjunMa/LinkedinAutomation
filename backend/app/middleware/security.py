"""
Enhanced Security Middleware for FastAPI
Provides comprehensive security headers, rate limiting, and request validation
"""

import time
import uuid
import logging
import hashlib
from typing import Dict, Optional, List
from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
import ipaddress


logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add comprehensive security headers to all responses
    """

    def __init__(self, app, csp_directives: Optional[Dict[str, str]] = None):
        super().__init__(app)
        self.csp_directives = csp_directives or self._default_csp()

    def _default_csp(self) -> Dict[str, str]:
        """Default Content Security Policy directives"""
        return {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data: blob:",
            "font-src": "'self' data:",
            "connect-src": "'self'",
            "frame-src": "'none'",
            "object-src": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "frame-ancestors": "'none'",
            "upgrade-insecure-requests": ""
        }

    def _build_csp_header(self) -> str:
        """Build Content Security Policy header value"""
        directives = []
        for directive, value in self.csp_directives.items():
            if value:
                directives.append(f"{directive} {value}")
            else:
                directives.append(directive)
        return "; ".join(directives)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Security Headers
        security_headers = {
            # Content Security Policy
            "Content-Security-Policy": self._build_csp_header(),

            # Content Type Options
            "X-Content-Type-Options": "nosniff",

            # Frame Options
            "X-Frame-Options": "DENY",

            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Permissions Policy
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",

            # Cache Control for API responses
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",

            # Remove server information
            "Server": "",

            # Request ID for tracking
            "X-Request-ID": getattr(request.state, 'request_id', str(uuid.uuid4()))
        }

        # Add HSTS in production
        if hasattr(request.state, 'is_production') and request.state.is_production:
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Apply headers
        for header, value in security_headers.items():
            response.headers[header] = value

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with multiple strategies
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
        whitelist_ips: Optional[List[str]] = None,
        blacklist_ips: Optional[List[str]] = None,
        rate_limit_by_user: bool = True,
        route_limits: Optional[Dict[str, Dict[str, int]]] = None,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        self.whitelist_ips = set(whitelist_ips or [])
        self.blacklist_ips = set(blacklist_ips or [])
        self.rate_limit_by_user = rate_limit_by_user
        self.route_limits = route_limits or {}

        # Rate limiting storage
        self.request_counts: Dict[str, deque] = defaultdict(deque)
        self.burst_counts: Dict[str, int] = defaultdict(int)
        self.blocked_ips: Dict[str, datetime] = {}

        # Cleanup interval
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Try to get user ID from request state (set by auth middleware)
        if self.rate_limit_by_user and hasattr(request.state, 'user_id'):
            return f"user:{request.state.user_id}"

        # Auth dependencies run after middleware, so use a hash of the bearer
        # token as the stable authenticated caller key without logging secrets.
        authorization = request.headers.get("Authorization", "")
        if authorization.lower().startswith("bearer "):
            token_hash = hashlib.sha256(authorization.encode("utf-8")).hexdigest()[:32]
            return f"token:{token_hash}"

        # Fall back to the direct peer. Do not trust client-supplied
        # X-Forwarded-For here; proxy-aware identity needs a trusted proxy list.
        return request.client.host if request.client else "unknown"

    def _is_whitelisted(self, client_ip: str) -> bool:
        """Check if IP is whitelisted"""
        try:
            ip = ipaddress.ip_address(client_ip)
            for whitelist_ip in self.whitelist_ips:
                if ip in ipaddress.ip_network(whitelist_ip, strict=False):
                    return True
        except ValueError:
            pass
        return False

    def _is_blacklisted(self, client_ip: str) -> bool:
        """Check if IP is blacklisted"""
        try:
            ip = ipaddress.ip_address(client_ip)
            for blacklist_ip in self.blacklist_ips:
                if ip in ipaddress.ip_network(blacklist_ip, strict=False):
                    return True
        except ValueError:
            pass
        return False

    def _cleanup_old_requests(self):
        """Remove old request records"""
        if time.time() - self.last_cleanup < self.cleanup_interval:
            return

        current_time = time.time()
        hour_ago = current_time - 3600

        for client_id in list(self.request_counts.keys()):
            # Clean requests older than 1 hour
            while (self.request_counts[client_id] and
                   self.request_counts[client_id][0] < hour_ago):
                self.request_counts[client_id].popleft()

            # Remove empty deques
            if not self.request_counts[client_id]:
                del self.request_counts[client_id]

        # Clean blocked IPs
        expired_blocks = [
            ip for ip, block_time in self.blocked_ips.items()
            if datetime.now() - block_time > timedelta(hours=1)
        ]
        for ip in expired_blocks:
            del self.blocked_ips[ip]

        self.last_cleanup = current_time

    def _get_limits_for_path(self, path: str) -> tuple[int, int, int, Optional[str]]:
        matched_prefix = None
        matched_config = None
        for prefix, config in self.route_limits.items():
            if path.startswith(prefix) and (matched_prefix is None or len(prefix) > len(matched_prefix)):
                matched_prefix = prefix
                matched_config = config
        if not matched_config:
            return self.requests_per_minute, self.requests_per_hour, self.burst_size, None
        return (
            matched_config.get("requests_per_minute", self.requests_per_minute),
            matched_config.get("requests_per_hour", self.requests_per_hour),
            matched_config.get("burst_size", self.burst_size),
            matched_prefix,
        )

    def _check_rate_limit(
        self,
        client_id: str,
        *,
        requests_per_minute: int,
        requests_per_hour: int,
        burst_size: int,
    ) -> bool:
        """Check if request should be rate limited"""
        current_time = time.time()
        minute_ago = current_time - 60

        # Count requests in the last minute and hour
        requests_last_minute = sum(
            1 for req_time in self.request_counts[client_id]
            if req_time > minute_ago
        )
        requests_last_hour = len(self.request_counts[client_id])

        # Check burst limit
        if requests_last_minute >= burst_size:
            logger.warning(f"Burst limit exceeded for {client_id}: {requests_last_minute} requests/minute")
            return False

        # Check minute limit
        if requests_last_minute >= requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_id}: {requests_last_minute} requests/minute")
            return False

        # Check hour limit
        if requests_last_hour >= requests_per_hour:
            logger.warning(f"Hour limit exceeded for {client_id}: {requests_last_hour} requests/hour")
            return False

        return True

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Add request ID to state
        if not hasattr(request.state, "request_id"):
            request.state.request_id = str(uuid.uuid4())

        # Cleanup old records periodically
        self._cleanup_old_requests()

        client_ip = request.client.host if request.client else "unknown"
        base_client_id = self._get_client_identifier(request)
        requests_per_minute, requests_per_hour, burst_size, route_prefix = self._get_limits_for_path(request.url.path)
        client_id = f"{base_client_id}:route:{route_prefix}" if route_prefix else base_client_id

        # Check blacklist
        if self._is_blacklisted(client_ip):
            logger.warning(f"Blocked blacklisted IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Access denied", "request_id": request.state.request_id}
            )

        # Skip rate limiting for whitelisted IPs
        if not self._is_whitelisted(client_ip):
            # Check if IP is temporarily blocked
            if client_ip in self.blocked_ips:
                block_time = self.blocked_ips[client_ip]
                if datetime.now() - block_time < timedelta(hours=1):
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "IP temporarily blocked due to excessive requests",
                            "retry_after": 3600,
                            "request_id": request.state.request_id
                        }
                    )
                else:
                    del self.blocked_ips[client_ip]

            # Check rate limits
            if not self._check_rate_limit(
                client_id,
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour,
                burst_size=burst_size,
            ):
                # Block IP if too many violations
                self.burst_counts[client_id] += 1
                if self.burst_counts[client_id] > 5:  # 5 violations = temporary block
                    self.blocked_ips[client_ip] = datetime.now()
                    logger.warning(f"Temporarily blocking IP {client_ip} due to repeated violations")

                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": 60,
                        "request_id": request.state.request_id
                    },
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + 60))
                    }
                )

        # Record the request
        self.request_counts[client_id].append(time.time())

        # Process request
        response = await call_next(request)

        # Add rate limiting headers
        minute_ago = time.time() - 60
        remaining_requests = max(0, requests_per_minute - sum(
            1 for req_time in self.request_counts[client_id]
            if req_time > minute_ago
        ))

        response.headers["X-RateLimit-Limit"] = str(requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining_requests)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request validation and sanitization
    """

    def __init__(
        self,
        app,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        route_size_limits: Optional[Dict[str, int]] = None,
        streamed_body_paths: Optional[List[str]] = None,
        blocked_user_agents: Optional[List[str]] = None,
        require_user_agent: bool = True
    ):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.route_size_limits = route_size_limits or {}
        self.streamed_body_paths = frozenset(streamed_body_paths or [])
        self.blocked_user_agents = blocked_user_agents or [
            "curl", "wget", "python-requests", "postman"  # Block common automation tools
        ]
        self.require_user_agent = require_user_agent

    def _is_suspicious_request(self, request: Request) -> tuple[bool, str]:
        """Check for suspicious request patterns"""

        # Check User-Agent
        user_agent = request.headers.get("User-Agent", "").lower()
        if self.require_user_agent and not user_agent:
            return True, "Missing User-Agent header"

        for blocked_ua in self.blocked_user_agents:
            if blocked_ua.lower() in user_agent:
                return True, f"Blocked User-Agent: {blocked_ua}"

        # Check for SQL injection patterns in URL
        url_str = str(request.url)
        suspicious_patterns = [
            "union select", "drop table", "insert into", "delete from",
            "script>", "<iframe", "javascript:", "vbscript:",
            "../", "..\\", "/etc/passwd", "/proc/", "cmd.exe"
        ]

        for pattern in suspicious_patterns:
            if pattern in url_str.lower():
                return True, f"Suspicious pattern in URL: {pattern}"

        # Check for excessive header size
        total_header_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if total_header_size > 8192:  # 8KB header limit
            return True, "Headers too large"

        return False, ""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check request size
        request_limit = self.max_request_size
        matching_prefixes = [
            prefix for prefix in self.route_size_limits
            if request.url.path == prefix
            or request.url.path.startswith(f"{prefix.rstrip('/')}/")
        ]
        if matching_prefixes:
            longest_prefix = max(matching_prefixes, key=len)
            request_limit = self.route_size_limits[longest_prefix]
        else:
            longest_prefix = None

        content_length = request.headers.get("Content-Length")
        try:
            parsed_content_length = int(content_length) if content_length else 0
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid Content-Length header",
                    "request_id": getattr(request.state, 'request_id', str(uuid.uuid4()))
                }
            )

        if parsed_content_length < 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid Content-Length header",
                    "request_id": getattr(request.state, 'request_id', str(uuid.uuid4()))
                }
            )

        if parsed_content_length > request_limit:
            client_host = request.client.host if request.client else "unknown"
            logger.warning(f"Request too large: {content_length} bytes from {client_host}")
            return JSONResponse(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                content={
                    "error": "Request entity too large",
                    "max_size": request_limit,
                    "request_id": getattr(request.state, 'request_id', str(uuid.uuid4()))
                }
            )

        # Content-Length is optional and cannot be trusted as the only limit for
        # a public endpoint. For explicitly small routes, consume at most the
        # configured budget and cache the accepted body for FastAPI to replay.
        # Large upload routes remain streaming and keep their existing behavior.
        if longest_prefix in self.streamed_body_paths:
            body_parts = []
            received_size = 0
            async for chunk in request.stream():
                received_size += len(chunk)
                if received_size > request_limit:
                    client_host = request.client.host if request.client else "unknown"
                    logger.warning(
                        "Streamed request exceeded %s bytes from %s",
                        request_limit,
                        client_host,
                    )
                    return JSONResponse(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        content={
                            "error": "Request entity too large",
                            "max_size": request_limit,
                            "request_id": getattr(
                                request.state, "request_id", str(uuid.uuid4())
                            ),
                        },
                    )
                body_parts.append(chunk)

            # BaseHTTPMiddleware passes a cached request downstream. Populating
            # its body cache lets the endpoint parse the already-validated bytes.
            request._body = b"".join(body_parts)

        # Check for suspicious patterns
        is_suspicious, reason = self._is_suspicious_request(request)
        if is_suspicious:
            logger.warning(f"Suspicious request blocked: {reason} from {request.client.host}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid request",
                    "request_id": getattr(request.state, 'request_id', str(uuid.uuid4()))
                }
            )

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced request logging for security monitoring
    """

    def __init__(self, app, log_request_body: bool = False, log_response_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

        # Log request
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")

        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "timestamp": datetime.now().isoformat()
        }

        # Skip request body logging to avoid middleware conflicts
        # The request body can only be read once, and this might interfere with FastAPI's body parsing

        logger.info(f"Request: {log_data}")

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            response_log = {
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": f"{process_time:.4f}s"
            }

            logger.info(f"Response: {response_log}")

            # Add timing header
            response.headers["X-Process-Time"] = f"{process_time:.4f}"

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed: {request_id}, error: {str(e)}, time: {process_time:.4f}s")
            raise


# Utility function to create a comprehensive security middleware stack
def create_security_middleware_stack(
    app,
    enable_rate_limiting: bool = True,
    enable_request_validation: bool = True,
    enable_security_headers: bool = True,
    enable_request_logging: bool = True,
    **kwargs
) -> None:
    """
    Add comprehensive security middleware stack to FastAPI app

    Args:
        app: FastAPI application instance
        enable_rate_limiting: Enable rate limiting middleware
        enable_request_validation: Enable request validation middleware
        enable_security_headers: Enable security headers middleware
        enable_request_logging: Enable request logging middleware
        **kwargs: Additional configuration for middlewares
    """

    # Add middlewares in reverse order (last added = first executed)

    if enable_request_logging:
        app.add_middleware(RequestLoggingMiddleware, **kwargs.get('logging', {}))

    if enable_security_headers:
        app.add_middleware(SecurityHeadersMiddleware, **kwargs.get('headers', {}))

    if enable_request_validation:
        app.add_middleware(RequestValidationMiddleware, **kwargs.get('validation', {}))

    if enable_rate_limiting:
        app.add_middleware(RateLimitMiddleware, **kwargs.get('rate_limit', {}))
