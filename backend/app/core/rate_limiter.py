"""
Rate limiting configuration for AI endpoints.
Prevents abuse and controls costs for expensive AI operations.
"""

import logging
from fastapi import Request, HTTPException
import time
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RateLimiter:
    """Custom rate limiter for AI endpoints with per-user and per-endpoint limits."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        # Store request timestamps per user and endpoint
        self.requests = defaultdict(lambda: defaultdict(deque))
        # Store request timestamps per IP for simple rate limiting
        self.ip_requests = defaultdict(deque)
        # Default rate limits
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Store last cleanup time
        self.last_cleanup = time.time()
        # Cleanup interval (1 hour)
        self.cleanup_interval = 3600

    def _cleanup_old_requests(self):
        """Remove old request records to prevent memory growth."""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            cutoff_time = current_time - 86400  # Keep only last 24 hours
            # Cleanup user-endpoint requests
            for user_requests in self.requests.values():
                for endpoint_requests in user_requests.values():
                    while endpoint_requests and endpoint_requests[0] < cutoff_time:
                        endpoint_requests.popleft()
            # Cleanup IP requests
            for ip_requests in self.ip_requests.values():
                while ip_requests and ip_requests[0] < cutoff_time:
                    ip_requests.popleft()
            self.last_cleanup = current_time

    def check_endpoint_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is within rate limit.

        Args:
            user_id: User identifier
            endpoint: API endpoint name
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if within limit, False if exceeded
        """
        self._cleanup_old_requests()

        current_time = time.time()
        cutoff_time = current_time - window_seconds

        # Get user's request history for this endpoint
        request_times = self.requests[user_id][endpoint]

        # Remove old requests outside the window
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()

        # Check if limit exceeded
        if len(request_times) >= max_requests:
            return False

        # Add current request
        request_times.append(current_time)
        return True

    def get_reset_time(
        self,
        user_id: str,
        endpoint: str,
        window_seconds: int
    ) -> int:
        """Get seconds until rate limit resets."""
        if not self.requests[user_id][endpoint]:
            return 0

        oldest_request = self.requests[user_id][endpoint][0]
        reset_time = oldest_request + window_seconds
        current_time = time.time()

        return max(0, int(reset_time - current_time))

    def check_rate_limit(self, identifier: str, cost: int = 1) -> bool:
        """
        Simple rate limiting by identifier (IP address or user ID).

        Args:
            identifier: IP address or user identifier
            cost: Request cost (for batch operations)

        Returns:
            True if within limit, False if exceeded

        Raises:
            Exception: If rate limit is exceeded
        """
        self._cleanup_old_requests()

        current_time = time.time()
        cutoff_time = current_time - self.window_seconds

        # Get request history for this identifier
        request_times = self.ip_requests[identifier]

        # Remove old requests outside the window
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()

        # Calculate current request count (considering cost)
        current_count = len(request_times)

        # Check if adding this request would exceed limit
        if current_count + cost > self.max_requests:
            raise Exception(f"Rate limit exceeded for {identifier}")

        # Add request(s) to history
        for _ in range(cost):
            request_times.append(current_time)

        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limit configurations for different AI operations
RATE_LIMITS = {
    "resume_evaluation": {
        "max_requests": 50,
        "window_seconds": 3600,  # 50 evaluations per hour
        "error_message": "Resume evaluation limit exceeded. Maximum 5 evaluations per hour."
    },
    "question_answering": {
        "max_requests": 20,
        "window_seconds": 3600,  # 20 Q&A sessions per hour
        "error_message": "Question answering limit exceeded. Maximum 20 sessions per hour."
    },
    "cover_letter": {
        "max_requests": 10,
        "window_seconds": 3600,  # 10 cover letters per hour
        "error_message": "Cover letter generation limit exceeded. Maximum 10 per hour."
    },
    "referral_message": {
        "max_requests": 30,
        "window_seconds": 3600,  # 30 referral messages per hour
        "error_message": "Referral message limit exceeded. Maximum 30 per hour."
    },
    "profile_parsing": {
        "max_requests": 50,
        "window_seconds": 3600,  # 50 profile parsing per hour
        "error_message": "Profile parsing limit exceeded. Maximum 50 per hour."
    },
    "ai_insights": {
        "max_requests": 10,
        "window_seconds": 3600,  # 10 AI insights per hour
        "error_message": "AI insights limit exceeded. Maximum 10 per hour."
    }
}


def rate_limit_decorator(endpoint_name: str):
    """
    Decorator for rate limiting AI endpoints.

    Args:
        endpoint_name: Name of the endpoint to rate limit
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Extract user_id from request (adjust based on your auth implementation)
            user_id = kwargs.get("user_id") or "anonymous"

            # Get rate limit config
            config = RATE_LIMITS.get(endpoint_name, {
                "max_requests": 10,
                "window_seconds": 3600,
                "error_message": "Rate limit exceeded. Please try again later."
            })

            # Check rate limit
            if not rate_limiter.check_endpoint_rate_limit(
                user_id,
                endpoint_name,
                config["max_requests"],
                config["window_seconds"]
            ):
                reset_time = rate_limiter.get_reset_time(
                    user_id,
                    endpoint_name,
                    config["window_seconds"]
                )

                logger.warning(f"Rate limit exceeded for user {user_id} on {endpoint_name}")

                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": config["error_message"],
                        "reset_in_seconds": reset_time,
                        "limit": config["max_requests"],
                        "window": config["window_seconds"]
                    },
                    headers={
                        "X-RateLimit-Limit": str(config["max_requests"]),
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(reset_time)
                    }
                )

            # Call the original function
            return await func(request, *args, **kwargs)

        return wrapper
    return decorator


def check_ai_rate_limit(user_id: str, operation: str) -> None:
    """
    Check rate limit for AI operations and raise exception if exceeded.

    Args:
        user_id: User identifier
        operation: Type of AI operation

    Raises:
        HTTPException: If rate limit is exceeded
    """
    config = RATE_LIMITS.get(operation, {
        "max_requests": 10,
        "window_seconds": 3600,
        "error_message": "Rate limit exceeded. Please try again later."
    })

    if not rate_limiter.check_endpoint_rate_limit(
        user_id,
        operation,
        config["max_requests"],
        config["window_seconds"]
    ):
        reset_time = rate_limiter.get_reset_time(
            user_id,
            operation,
            config["window_seconds"]
        )

        logger.warning(f"Rate limit exceeded for user {user_id} on {operation}")

        raise HTTPException(
            status_code=429,
            detail={
                "error": config["error_message"],
                "reset_in_seconds": reset_time,
                "limit": config["max_requests"],
                "window": config["window_seconds"]
            }
        )
