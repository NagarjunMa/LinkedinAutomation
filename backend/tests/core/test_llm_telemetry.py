"""Privacy and truthful-cost behavior at the ordinary LLM logging boundary."""

import logging
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
from openai import APIConnectionError
from pydantic import ValidationError
from tenacity import wait_none

from app.core.llm_logging import estimate_cost, log_cost, measure
from app.core.model_retry import retry_model_call
from app.core.openai_client import DEFAULT_MANIFESTS, ModelManifest


@pytest.mark.asyncio
async def test_failed_call_keeps_safe_failure_category_without_error_text(caplog):
    with caplog.at_level(logging.INFO, logger="llm"):
        with pytest.raises(ValueError, match="PRIVATE-JD"):
            async with measure("extractor", user_id="private-user"):
                raise ValueError("PRIVATE-JD")

    messages = [record.msg for record in caplog.records if record.name == "llm"]
    assert len(messages) == 1
    assert messages[0]["failure_category"] == "invalid_response"
    assert messages[0]["retry_count"] == 0
    assert "PRIVATE-JD" not in caplog.text
    assert "private-user" not in caplog.text
    assert "PRIVATE-JD" not in str([record.__dict__ for record in caplog.records])
    assert "private-user" not in str([record.__dict__ for record in caplog.records])


def test_missing_manifest_price_never_creates_a_cost(caplog):
    usage = SimpleNamespace(prompt_tokens=100, completion_tokens=50)
    with caplog.at_level(logging.INFO, logger="llm"):
        log_cost("evaluator", usage, user_id="private-user")

    payload = next(record.msg for record in caplog.records if record.name == "llm")
    assert payload["prompt_tokens"] == 100
    assert payload["completion_tokens"] == 50
    assert payload["cost_usd"] is None
    assert payload["cost_status"] == "unavailable"
    assert "private-user" not in caplog.text


def test_exact_snapshot_price_accounts_for_cached_input(caplog):
    manifest = DEFAULT_MANIFESTS["evaluator"]
    usage = SimpleNamespace(
        prompt_tokens=1_000, completion_tokens=200,
        prompt_tokens_details=SimpleNamespace(cached_tokens=400),
    )
    assert estimate_cost(usage, manifest, response_model=manifest.model_snapshot) == Decimal("0.004")
    with caplog.at_level(logging.INFO, logger="llm"):
        log_cost("evaluator", usage, manifest=manifest, response_model=manifest.model_snapshot)
    payload = next(record.msg for record in caplog.records if record.name == "llm")
    assert payload["cost_usd"] == 0.004
    assert payload["cost_status"] == "estimated"
    assert payload["cached_prompt_tokens"] == 400
    assert payload["pricing_version"] == manifest.pricing.version


def test_mismatched_snapshot_and_incomplete_usage_never_get_priced():
    manifest = DEFAULT_MANIFESTS["evaluator"]
    usage = SimpleNamespace(prompt_tokens=1_000, completion_tokens=200,
                            prompt_tokens_details=SimpleNamespace(cached_tokens=0))
    assert estimate_cost(usage, manifest, response_model="different-model") is None
    assert estimate_cost(SimpleNamespace(prompt_tokens=1_000, completion_tokens=200),
                         manifest, response_model=manifest.model_snapshot) is None
    bad_usage = SimpleNamespace(prompt_tokens=True, completion_tokens=200,
                                prompt_tokens_details=SimpleNamespace(cached_tokens=0))
    assert estimate_cost(bad_usage, manifest, response_model=manifest.model_snapshot) is None
    custom = ModelManifest(**{**manifest.model_dump(), "pricing": None,
                              "model_snapshot": "private-model"})
    assert estimate_cost(usage, custom, response_model="private-model") is None
    with pytest.raises(ValidationError, match="pricing must match"):
        ModelManifest(**{**manifest.model_dump(), "model_snapshot": "different-model"})


@pytest.mark.asyncio
async def test_retry_telemetry_records_each_attempt_without_provider_text(caplog):
    calls = 0

    @retry_model_call(attempts=2)
    async def operation():
        nonlocal calls
        calls += 1
        async with measure("evaluator"):
            if calls == 1:
                raise APIConnectionError(message="PRIVATE-JD", request=httpx.Request(
                    "POST", "https://api.openai.com/v1/chat/completions"))

    with caplog.at_level(logging.INFO, logger="llm"):
        await operation.retry_with(wait=wait_none())()

    records = [r.msg for r in caplog.records if r.name == "llm"]
    assert [(r["failure_category"], r["retry_count"]) for r in records] == [
        ("provider_connection", 0), ("none", 1),
    ]
    assert all(r["fallback_used"] is False for r in records)
    assert "PRIVATE-JD" not in caplog.text
