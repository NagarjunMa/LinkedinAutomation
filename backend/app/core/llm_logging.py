"""Aggregate, privacy-safe telemetry for manifest-backed model calls.

Only bounded numeric metadata and internal manifest identifiers enter ordinary
logs. User identifiers and provider error messages never enter a log record.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from contextvars import ContextVar
from decimal import Decimal

from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

from app.core.openai_client import ModelManifest

logger = logging.getLogger("llm")
_attempt_number: ContextVar[int] = ContextVar("llm_retry_attempt", default=1)


def _set_retry_attempt(number: int) -> None:
    """Called by Tenacity before each attempt; the next call resets it to one."""
    _attempt_number.set(number)


def _failure_category(error: BaseException) -> str:
    if isinstance(error, asyncio.CancelledError):
        return "cancelled"
    if isinstance(error, APITimeoutError):
        return "provider_timeout"
    if isinstance(error, APIConnectionError):
        return "provider_connection"
    if isinstance(error, RateLimitError):
        return "provider_rate_limit"
    if isinstance(error, APIStatusError):
        return "provider_status"
    if isinstance(error, ValueError):
        return "invalid_response"
    return "other"


def _token_counts(usage) -> tuple[int | None, int | None, int | None]:
    if usage is None:
        return None, None, None
    prompt = getattr(usage, "prompt_tokens", None)
    output = getattr(usage, "completion_tokens", None)
    details = getattr(usage, "prompt_tokens_details", None)
    cached = getattr(details, "cached_tokens", None)
    if type(prompt) is not int or prompt < 0 or type(output) is not int or output < 0:
        return None, None, None
    if type(cached) is not int or not 0 <= cached <= prompt:
        cached = None
    return prompt, output, cached


def estimate_cost(usage, manifest: ModelManifest | None = None, *,
                  response_model: str | None = None) -> Decimal | None:
    """Return an exact-snapshot estimate, or None when any input is unknown."""
    pricing = getattr(manifest, "pricing", None)
    if (pricing is None or response_model != manifest.model_snapshot
            or pricing.model_snapshot != manifest.model_snapshot):
        return None
    prompt, output, cached = _token_counts(usage)
    if prompt is None or output is None or cached is None:
        return None
    return (
        (prompt - cached) * pricing.input_usd_per_million
        + cached * pricing.cached_input_usd_per_million
        + output * pricing.output_usd_per_million
    ) / Decimal(1_000_000)


def log_cost(label: str, usage, user_id: str | None = None, *,
             manifest: ModelManifest | None = None,
             response_model: str | None = None) -> None:
    """Log token usage by operation; user_id is accepted but ignored."""
    prompt, output, cached = _token_counts(usage)
    cost = estimate_cost(usage, manifest, response_model=response_model)
    logger.info({
        "event": "llm_usage", "label": label,
        "model_snapshot": getattr(manifest, "model_snapshot", None),
        "pricing_version": manifest.pricing.version if cost is not None else None,
        "prompt_tokens": prompt, "completion_tokens": output,
        "cached_prompt_tokens": cached,
        "cost_usd": float(cost) if cost is not None else None,
        "cost_status": "estimated" if cost is not None else "unavailable",
        "retry_count": max(0, _attempt_number.get() - 1),
        "fallback_used": False,
    })


@asynccontextmanager
async def measure(label: str, user_id: str | None = None, *,
                  manifest: ModelManifest | None = None):
    """Measure one provider attempt without logging subject or error text."""
    start = time.perf_counter()
    failure = "none"
    try:
        yield
    except BaseException as error:
        failure = _failure_category(error)
        raise
    finally:
        logger.info({
            "event": "llm_call", "label": label,
            "model_snapshot": getattr(manifest, "model_snapshot", None),
            "latency_ms": int((time.perf_counter() - start) * 1000),
            "failure_category": failure,
            "retry_count": max(0, _attempt_number.get() - 1),
            "fallback_used": False,
        })
