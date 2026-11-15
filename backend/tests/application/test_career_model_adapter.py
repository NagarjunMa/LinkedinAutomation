import asyncio
import hashlib
import json
import logging
from pathlib import Path

import httpx
import pytest
from openai import AsyncOpenAI, DefaultAsyncHttpxClient
from pydantic import ValidationError

from app.application.career_model import CareerModel, CareerModelRequest
from app.core.openai_client import DEFAULT_MANIFESTS, ModelRuntime
from app.schemas.career.lineage import RunMetadata, StoredRun
from app.services.career_model_openai import OpenAICareerModel

SNAPSHOT = "gpt-4.1-mini-2025-04-14"
COMMIT = "a" * 40
OWNER = "synthetic-user-a"
CONTEXT = "Private synthetic project context"
KEY = b"synthetic-test-key" * 2
PROPOSAL = {
    "schema_version": 1,
    "question": "How did you check the result?",
    "question_intent": "probe",
    "target_evidence_slot": "validation",
    "evidence_proposals": [],
    "contradiction_candidates": [],
    "recommended_action": "continue",
}


def provider_payload(*, content=None, status="completed", model=SNAPSHOT):
    if content is None:
        content = [{"type": "output_text", "text": json.dumps(PROPOSAL), "annotations": []}]
    return {
        "id": "resp_synthetic",
        "object": "response",
        "created_at": 1,
        "status": status,
        "model": model,
        "output": [{"id": "msg_synthetic", "type": "message", "role": "assistant",
                    "status": status, "content": content}],
        "usage": {"input_tokens": 51, "output_tokens": 17, "total_tokens": 68,
                  "input_tokens_details": {"cached_tokens": 0},
                  "output_tokens_details": {"reasoning_tokens": 0}},
    }


def source_link():
    return {
        "source_id": "source-a", "source_version": 1, "relationship": "supports",
        "locator": "chars:0-10", "extraction": "model", "excerpt": CONTEXT, "excerpt_sha256": None,
    }


async def invoke(handler, *, timeout_ms=8000, owner=OWNER, safety_key=KEY, snapshot=SNAPSHOT,
                 base_url="https://api.openai.com/v1/"):
    async with AsyncOpenAI(
        api_key="synthetic-fixture",
        base_url=base_url,
        max_retries=4,
        http_client=DefaultAsyncHttpxClient(transport=httpx.MockTransport(handler)),
    ) as client:
        adapter: CareerModel = OpenAICareerModel(
            ModelRuntime(client_factory=lambda: client),
            model_snapshot=snapshot, application_commit=COMMIT,
            safety_key=safety_key, max_output_tokens=750, timeout_ms=timeout_ms,
        )
        return await adapter.propose(CareerModelRequest(owner_id=owner, context=CONTEXT))


@pytest.mark.asyncio
async def test_responses_request_is_private_bounded_and_tied_to_exact_manifest():
    sent = []

    def handle(request):
        assert request.url.path == "/v1/responses"
        assert request.extensions["timeout"]["read"] == 8
        sent.append(json.loads(request.content))
        return httpx.Response(200, json=provider_payload(), headers={"x-request-id": "req_synthetic"})

    result = await invoke(handle)
    assert result.proposal.model_dump() == PROPOSAL
    assert not result.retryable
    run = result.run
    assert (run.metadata.application_commit, run.metadata.provider_request_id) == (COMMIT, "req_synthetic")
    assert (run.metadata.input_tokens, run.metadata.output_tokens, run.metadata.retry_count) == (51, 17, 0)
    assert run.metadata.failure is None
    assert StoredRun.model_validate_json(run.model_dump_json()) == run
    assert CONTEXT not in run.model_dump_json() and OWNER not in run.model_dump_json()
    wire, = sent
    assert wire["model"] == run.manifest.model_snapshot == SNAPSHOT
    assert wire["store"] is False and wire["max_output_tokens"] == run.manifest.max_output_tokens == 750
    assert "tools" not in wire and "previous_response_id" not in wire
    assert wire["input"] == [{"role": "user", "content": CONTEXT}]
    assert OWNER not in json.dumps(wire)
    assert wire["safety_identifier"] != hashlib.sha256(OWNER.encode()).hexdigest()
    assert len(wire["safety_identifier"]) == 64
    prompt_file = Path(__file__).parents[2] / "app/prompts/career/turn_v1.txt"
    assert wire["instructions"] == prompt_file.read_text(encoding="utf-8")
    assert run.manifest.prompt_hash == hashlib.sha256(wire["instructions"].encode()).hexdigest()
    assert run.manifest.prompt_version == "1"
    assert run.manifest.policy_version == "career-interview.v1"
    schema = wire["text"]["format"]["schema"]
    assert wire["text"]["format"]["strict"] is True
    assert run.manifest.schema_hash == hashlib.sha256(
        json.dumps(schema, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert set(schema["properties"]) == set(schema["required"])
    assert schema["additionalProperties"] is False
    assert all("oneOf" not in part for part in schema["$defs"].values())


@pytest.mark.asyncio
async def test_replacement_snapshot_accepts_canonical_nested_evidence_and_records_the_call():
    snapshot = "gpt-4.1-2025-04-14"
    proposal = {**PROPOSAL, "evidence_proposals": [{
        "claim": CONTEXT, "category": "action", "qualifiers": [], "sources": [source_link()],
    }]}
    content = [{"type": "output_text", "text": json.dumps(proposal), "annotations": []}]

    def handle(request):
        assert json.loads(request.content)["model"] == snapshot
        return httpx.Response(200, json=provider_payload(model=snapshot, content=content))

    result = await invoke(handle, snapshot=snapshot)
    assert result.proposal.model_dump() == proposal
    assert result.run.manifest.model_snapshot == snapshot
    assert CONTEXT not in repr(result)


@pytest.mark.asyncio
async def test_safety_identifier_is_stable_per_owner_and_secret():
    sent = []

    def handle(request):
        sent.append(json.loads(request.content)["safety_identifier"])
        return httpx.Response(200, json=provider_payload())

    await invoke(handle)
    await invoke(handle)
    await invoke(handle, owner="synthetic-user-b")
    await invoke(handle, safety_key=b"x" * 32)
    assert sent[0] == sent[1]
    assert len({sent[0], sent[2], sent[3]}) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(("case", "failure"), [
    ("refusal", "proposal_rejected"),
    ("incomplete", "schema_invalid"),
    ("syntax", "schema_invalid"),
    ("missing_arrays", "schema_invalid"),
    ("bad_link", "schema_invalid"),
    ("multiple_texts", "schema_invalid"),
    ("partial_message", "schema_invalid"),
    ("model_changed", "provider_error"),
])
async def test_untrusted_provider_results_fail_closed(case, failure):
    valid = {"type": "output_text", "text": json.dumps(PROPOSAL), "annotations": []}
    data = provider_payload()
    if case == "refusal":
        data["output"][0]["content"] = [{"type": "refusal", "refusal": CONTEXT}]
    elif case == "incomplete":
        data["status"] = "incomplete"
    elif case == "syntax":
        data["output"][0]["content"] = [{**valid, "text": CONTEXT}]
    elif case == "missing_arrays":
        del_fields = {key: value for key, value in PROPOSAL.items() if key != "evidence_proposals"}
        data["output"][0]["content"] = [{**valid, "text": json.dumps(del_fields)}]
    elif case == "bad_link":
        bad = {**PROPOSAL, "evidence_proposals": [{
            "claim": CONTEXT, "category": "action", "qualifiers": [],
            "sources": [{**source_link(), "excerpt_sha256": "b" * 64}],
        }]}
        data["output"][0]["content"] = [{**valid, "text": json.dumps(bad)}]
    elif case == "multiple_texts":
        data["output"][0]["content"].append(valid)
    elif case == "partial_message":
        data["output"][0]["status"] = "incomplete"
    elif case == "model_changed":
        data["model"] = "gpt-other-2026-01-01"
    result = await invoke(lambda _: httpx.Response(200, json=data))
    assert result.proposal is None
    assert result.run.metadata.failure == failure
    assert not result.retryable and CONTEXT not in result.run.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize("override", [
    {"object": "unexpected"},
    {"error": {"code": "server_error", "message": CONTEXT}},
    {"incomplete_details": {"reason": "content_filter"}},
])
async def test_inconsistent_completion_indicators_discard_the_proposal(override):
    payload = provider_payload() | override
    result = await invoke(lambda _: httpx.Response(200, json=payload))
    assert result.proposal is None
    assert result.run.metadata.failure == "provider_error"
    assert not result.retryable and CONTEXT not in result.run.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize(("code", "error_type", "retryable"), [
    ("rate_limit_exceeded", "rate_limit_exceeded", True),
    ("rate_limit_exceeded", None, True),
    ("insufficient_quota", "insufficient_quota", False),
    (["malformed-provider-code"], None, False),
    ("rate_limit_exceeded", ["insufficient_quota"], False),
])
async def test_provider_error_is_sanitized_and_sdk_never_retries(code, error_type, retryable, caplog):
    caplog.set_level(logging.INFO)
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(429, json={"error": {"message": CONTEXT, "code": code, "type": error_type}})

    result = await invoke(handle)
    assert len(calls) == 1
    assert result.proposal is None
    assert result.run.metadata.failure == "model_unavailable"
    assert result.retryable is retryable
    assert CONTEXT not in caplog.text and CONTEXT not in repr(result)
    assert OWNER not in caplog.text


@pytest.mark.asyncio
async def test_sdk_default_redirects_cannot_resend_candidate_context():
    calls = []

    def handle(request):
        calls.append(request.url.host)
        return httpx.Response(307, headers={"location": "https://other-provider.invalid/redirect"})

    result = await invoke(handle)
    assert calls == ["api.openai.com"]
    assert result.run.metadata.failure == "provider_error" and not result.retryable


@pytest.mark.asyncio
async def test_configured_foreign_api_origin_is_rejected_before_dispatch():
    def handle(_):
        pytest.fail("The adapter sent candidate text outside the OpenAI API")

    result = await invoke(handle, base_url="https://other-provider.invalid/v1/")
    assert result.run.metadata.failure == "provider_error" and not result.retryable


@pytest.mark.asyncio
async def test_sdk_debug_logs_cannot_capture_private_request_or_provider_error(caplog):
    caplog.set_level(logging.DEBUG, logger="openai._base_client")
    result = await invoke(lambda _: httpx.Response(400, json={"error": {"message": CONTEXT}}))
    assert result.run.metadata.failure == "provider_error"
    logging.getLogger("openai._base_client").debug("synthetic-public-marker")
    assert "synthetic-public-marker" in caplog.text
    assert CONTEXT not in caplog.text and OWNER not in caplog.text


@pytest.mark.asyncio
async def test_malformed_response_envelope_returns_a_sanitized_failure():
    nested = b'{"nested":' + b"[" * 1500 + b"0" + b"]" * 1500 + b"}"
    result = await invoke(lambda _: httpx.Response(
        200, content=nested, headers={"content-type": "application/json"},
    ))
    assert result.proposal is None
    assert result.run.metadata.failure == "provider_error" and not result.retryable


@pytest.mark.asyncio
async def test_wall_clock_deadline_cancels_the_only_attempt():
    cancelled = asyncio.Event()

    async def handle(_):
        try:
            await asyncio.sleep(2)
        finally:
            cancelled.set()

    result = await invoke(handle, timeout_ms=40)
    assert cancelled.is_set()
    assert result.run.metadata.failure == "model_timeout" and result.retryable


@pytest.mark.asyncio
async def test_caller_cancellation_propagates():
    started = asyncio.Event()

    async def handle(_):
        started.set()
        await asyncio.sleep(2)

    task = asyncio.create_task(invoke(handle))
    await asyncio.wait_for(started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.parametrize("override", [
    {"model_snapshot": "gpt-4.1-mini"},
    {"application_commit": "main"},
    {"safety_key": b"short"},
    {"max_output_tokens": 4097},
    {"timeout_ms": 0},
])
def test_invalid_release_settings_do_not_create_a_client(override):
    def forbidden():
        pytest.fail("The adapter should not open a client here")

    values = {"model_snapshot": SNAPSHOT, "application_commit": COMMIT, "safety_key": KEY}
    with pytest.raises(ValueError):
        OpenAICareerModel(ModelRuntime(client_factory=forbidden), **(values | override))


def test_private_input_is_bounded_and_omitted_from_diagnostics():
    request = CareerModelRequest(owner_id=OWNER, context=CONTEXT)
    assert CONTEXT not in repr(request) and OWNER not in repr(request)
    with pytest.raises(ValidationError) as error:
        CareerModelRequest(owner_id=OWNER, context=CONTEXT * 2000)
    assert CONTEXT not in str(error.value)


def test_legacy_run_keeps_its_previous_wire_shape():
    legacy = {
        "schema_version": 1,
        "manifest": DEFAULT_MANIFESTS["evaluator"].model_dump(mode="json"),
        "metadata": RunMetadata(schema_version=1, application_commit="old-commit", latency_ms=0).model_dump(mode="json"),
    }
    assert StoredRun.model_validate(legacy).model_dump(mode="json") == legacy
