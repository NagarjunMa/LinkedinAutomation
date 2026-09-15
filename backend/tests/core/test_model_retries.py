"""Count real SDK HTTP attempts, not just calls hidden behind an SDK mock."""

import asyncio
from datetime import datetime, timezone
from email.utils import format_datetime
from unittest.mock import AsyncMock

import httpx
import pytest
import respx
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, RateLimitError
from tenacity import RetryError, wait_none

from app.core.openai_client import ModelRuntime
from tests.core.test_model_manifests import case, fake_provider

OPERATIONS = ["evaluator", "rewriter", "extractor", "tailor", "tailor_options"]
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def completion(content):
    return httpx.Response(200, json={
        "id": "synthetic", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    })


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch):
    # Remove SDK delay without changing its attempt policy; application wait is
    # independently overridden below while keeping production stop/predicate rules.
    monkeypatch.setattr("openai._base_client.anyio.sleep", AsyncMock())


@pytest.mark.asyncio
@pytest.mark.parametrize("name", OPERATIONS)
@pytest.mark.parametrize("failure", ["rate", "slow_down", "connection", "timeout"])
@pytest.mark.parametrize("recovers", [False, True])
async def test_transient_attempts_are_bounded_without_nested_retries(name, failure, recovers):
    fn, args, *_, result = case(name)
    expected_limit = 2 if name == "rewriter" else 3
    request = httpx.Request("POST", OPENAI_URL)
    if failure in {"connection", "timeout"}:
        effect = (httpx.ConnectError if failure == "connection" else httpx.ReadTimeout)("synthetic", request=request)
        error_type = APIConnectionError if failure == "connection" else APITimeoutError
    else:
        effect = httpx.Response(429, json={"error": {
            "message": "synthetic", "code": "slow_down" if failure == "slow_down" else "rate_limit_exceeded",
            "type": "rate_limit_error" if failure == "slow_down" else "tokens",
        }})
        error_type = RateLimitError
    message = result.choices[0].message
    success = completion(message.parsed.model_dump_json() if message.parsed is not None else message.content)
    with respx.mock as router:
        route = router.post(OPENAI_URL).mock(side_effect=[effect, success] if recovers else effect)
        async with AsyncOpenAI(api_key="test") as sdk:
            runtime = ModelRuntime(client_factory=lambda: sdk)
            if recovers:
                await fn.retry_with(wait=wait_none())(**args, runtime=runtime)
                assert route.call_count == 2
            else:
                with pytest.raises(RetryError) as caught:
                    await fn.retry_with(wait=wait_none())(**args, runtime=runtime)
                assert isinstance(caught.value.last_attempt.exception(), error_type)
                assert route.call_count == expected_limit
            assert sdk.max_retries == 2, "Shared/injected SDK configuration must not be mutated"


@pytest.mark.asyncio
@pytest.mark.parametrize("name", OPERATIONS)
@pytest.mark.parametrize("status,code,error_type", [
    (400, "invalid_request", "invalid_request_error"),
    (401, "invalid_api_key", "invalid_request_error"),
    (403, "permission_denied", "invalid_request_error"),
    (500, "internal_error", "server_error"),
    (429, "credit_balance_exhausted", "insufficient_quota"),
    (429, "insufficient_quota", "insufficient_quota"),
    (429, "organization_spend_limit_exceeded", "insufficient_quota"),
    (429, "project_spend_limit_exceeded", "insufficient_quota"),
    (429, "organization_usage_limit_exceeded", "insufficient_quota"),
    (429, "unknown", "unknown"),
])
async def test_errors_outside_explicit_retry_policy_are_not_retried(name, status, code, error_type):
    fn, args, *_ = case(name)
    with respx.mock as router:
        route = router.post(OPENAI_URL).respond(status, json={"error": {
            "message": "private-provider-text", "code": code, "type": error_type,
        }})
        async with AsyncOpenAI(api_key="test") as sdk:
            with pytest.raises(APIStatusError):
                await fn.retry_with(wait=wait_none())(**args, runtime=ModelRuntime(client_factory=lambda: sdk))
        assert route.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("name", OPERATIONS)
@pytest.mark.parametrize("content", ["{", "{}"])
async def test_malformed_or_schema_invalid_response_is_not_retried(name, content):
    fn, args, *_ = case(name)
    with respx.mock as router:
        route = router.post(OPENAI_URL).mock(return_value=completion(content))
        async with AsyncOpenAI(api_key="test") as sdk:
            with pytest.raises(ValueError):
                await fn.retry_with(wait=wait_none())(**args, runtime=ModelRuntime(client_factory=lambda: sdk))
        assert route.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("name", OPERATIONS)
async def test_cancellation_is_never_retried(name):
    fn, args, *_ = case(name)
    client, call = fake_provider(None)
    call.side_effect = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        await fn.retry_with(wait=wait_none())(**args, runtime=ModelRuntime(client_factory=lambda: client))
    call.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("name", OPERATIONS)
@pytest.mark.parametrize("headers,should_retry,delay", [
    ({"retry-after": "3"}, True, 3),
    ({"retry-after-ms": "2500"}, True, 2.5),
    ({"retry-after": format_datetime(datetime.fromtimestamp(1003, tz=timezone.utc), usegmt=True)}, True, 3),
    ({"retry-after": "60"}, False, None),
    ({"retry-after": "nan"}, False, None),
    ({"retry-after": "infinity"}, False, None),
    ({"retry-after": "invalid"}, False, None),
    ({"x-should-retry": "false"}, False, None),
])
async def test_provider_retry_delay_respected_or_fails_within_bound(name, headers, should_retry, delay, monkeypatch):
    fn, args, *_, result = case(name)
    monkeypatch.setattr("time.time", lambda: 1000)
    sleep = AsyncMock()
    message = result.choices[0].message
    success = completion(message.parsed.model_dump_json() if message.parsed is not None else message.content)
    with respx.mock as router:
        route = router.post(OPENAI_URL).mock(side_effect=[httpx.Response(429, headers=headers, json={"error": {
            "message": "synthetic", "code": "rate_limit_exceeded", "type": "tokens",
        }}), success])
        async with AsyncOpenAI(api_key="test") as sdk:
            call = fn.retry_with(sleep=sleep)
            if should_retry:
                await call(**args, runtime=ModelRuntime(client_factory=lambda: sdk))
                assert route.call_count == 2
                sleep.assert_awaited_once_with(delay)
            else:
                with pytest.raises(RateLimitError):
                    await call(**args, runtime=ModelRuntime(client_factory=lambda: sdk))
                assert route.call_count == 1
                sleep.assert_not_awaited()
