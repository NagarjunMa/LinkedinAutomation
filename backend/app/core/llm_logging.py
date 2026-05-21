"""Structured LLM latency + cost telemetry.

Usage in services:
    from app.core.llm_logging import measure, estimate_cost, log_cost

    async with measure("evaluator", user_id=user_id):
        resp = await _client.chat.completions.create(...)
    log_cost("evaluator", resp.usage, user_id=user_id)
"""
import logging
import time
from contextlib import asynccontextmanager

logger = logging.getLogger("llm")

# Cost per token for gpt-4o-2024-08-06
# (placeholder values for observability; verify against current OpenAI pricing)
PRICE_PROMPT = 0.0025 / 1000   # $0.0025 per 1K prompt tokens
PRICE_OUTPUT = 0.01 / 1000     # $0.01 per 1K output tokens


def estimate_cost(usage) -> float:
    """Estimate USD cost from an OpenAI usage object.

    Expects usage.prompt_tokens and usage.completion_tokens.
    Returns 0.0 if usage is None.
    """
    if usage is None:
        return 0.0
    return usage.prompt_tokens * PRICE_PROMPT + usage.completion_tokens * PRICE_OUTPUT


def log_cost(label: str, usage, user_id: str | None = None) -> None:
    """Log per-call cost with optional user attribution.

    Emits a structured INFO record on the ``llm`` logger including
    ``user_id`` so that log aggregators can compute per-user spend.
    """
    logger.info(
        {"event": "llm_cost", "label": label,
         "cost_usd": estimate_cost(usage), "user_id": user_id}
    )


@asynccontextmanager
async def measure(label: str, user_id: str | None = None):
    """Async context manager that logs LLM call latency on exit."""
    start = time.perf_counter()
    yield
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        {"event": "llm_call", "label": label, "user_id": user_id, "latency_ms": int(elapsed)}
    )
