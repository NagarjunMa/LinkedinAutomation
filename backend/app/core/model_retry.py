"""One bounded retry policy for the current resume/JD model call paths."""

import math
import time
from email.utils import parsedate_to_datetime

from openai import APIConnectionError, RateLimitError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.llm_logging import _set_retry_attempt


def is_transient_model_error(error: BaseException) -> bool:
    if isinstance(error, APIConnectionError):
        # APITimeoutError is an APIConnectionError subclass.
        return True
    if isinstance(error, RateLimitError):
        # HTTP 429 also represents depleted credits/spend limits. Unknown codes
        # fail closed; neither schema/grounding failures nor billing errors repair
        # themselves through another model call.
        return (
            error.type != "insufficient_quota"
            and error.code in {"rate_limit_exceeded", "slow_down"}
            and error.response.headers.get("x-should-retry") != "false"
        )
    return False


def _retry_after(error: BaseException | None) -> float | None:
    if not isinstance(error, RateLimitError):
        return None
    headers = error.response.headers
    raw = headers.get("retry-after-ms", headers.get("retry-after"))
    if raw is None:
        return None
    try:
        if "retry-after-ms" in headers:
            seconds = float(raw) / 1000
        else:
            try:
                seconds = float(raw)
            except ValueError:
                seconds = parsedate_to_datetime(raw).timestamp() - time.time()
        if math.isfinite(seconds):
            return max(0, seconds)
    except (ValueError, TypeError, OverflowError):
        pass
    # An unusable provider delay must not create a rapid or unbounded retry loop.
    return math.inf


def retry_model_call(*, attempts: int = 3, max_wait: int = 10):
    """Preserve each operation's total-attempt budget; SDK retries must be off."""
    backoff = wait_exponential(multiplier=1, min=1, max=max_wait)

    def should_retry(error: BaseException) -> bool:
        if not is_transient_model_error(error):
            return False
        delay = _retry_after(error)
        # A longer server cooldown cannot fit this synchronous operation's wait
        # budget. Fail rather than ignore the cooldown or hold the request open.
        return delay is None or delay <= max_wait

    def wait(retry_state):
        delay = _retry_after(retry_state.outcome.exception())
        return max(backoff(retry_state), delay or 0)

    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait,
        retry=retry_if_exception(should_retry),
        before=lambda state: _set_retry_attempt(state.attempt_number),
    )
