"""OpenAI Responses transport for Career Interview proposals."""

import asyncio
from contextvars import ContextVar
from hashlib import sha256
import hmac
import json
import logging
from pathlib import Path
import re
from time import monotonic

from jsonschema import Draft202012Validator
from openai import APIError, APIStatusError, APITimeoutError, OpenAIError
from openai.types.responses import Response
from pydantic import TypeAdapter

from app.application.career_model import CareerModelRequest, CareerModelResult
from app.core.model_retry import is_transient_model_error
from app.core.openai_client import ModelRuntime, OpenAIConfigurationError
from app.schemas.career.interview import CareerTurnProposal
from app.schemas.career.lineage import ApplicationCommit, CareerRunManifest, RunFailure, RunMetadata, StoredRun


def _strict_schema(node: dict) -> dict:
    # The provider accepts a subset of JSON Schema. Domain validators run after parsing.
    schema = {key: node[key] for key in ("type", "$ref", "enum") if key in node}
    if "const" in node:
        schema["enum"] = [node["const"]]
    if "properties" in node:
        schema["properties"] = {name: _strict_schema(value) for name, value in node["properties"].items()}
        schema["additionalProperties"] = False
        schema["required"] = list(schema["properties"])
    if "$defs" in node:
        schema["$defs"] = {name: _strict_schema(value) for name, value in node["$defs"].items()}
    if "items" in node:
        schema["items"] = _strict_schema(node["items"])
    if "anyOf" in node:
        schema["anyOf"] = [_strict_schema(value) for value in node["anyOf"]]
    return schema


_PROMPT = (Path(__file__).resolve().parents[1] / "prompts" / "career" / "turn_v1.txt").read_bytes()
_RESPONSE_SCHEMA = _strict_schema(CareerTurnProposal.model_json_schema())
_RESPONSE_VALIDATOR = Draft202012Validator(_RESPONSE_SCHEMA)
_SCHEMA_HASH = sha256(json.dumps(_RESPONSE_SCHEMA, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
_IN_CAREER_REQUEST = ContextVar("in_career_provider_request", default=False)


def _allow_sdk_log(_record: logging.LogRecord) -> bool:
    return not _IN_CAREER_REQUEST.get()


# The pinned SDK can include request bodies and exceptions in debug records.
logging.getLogger("openai._base_client").addFilter(_allow_sdk_log)


def _parse_response(response: Response, snapshot: str) -> tuple[CareerTurnProposal | None, RunFailure | None]:
    if (
        getattr(response, "object", None) != "response"
        or getattr(response, "model", None) != snapshot
        or getattr(response, "error", None) is not None
    ):
        return None, "provider_error"
    status = getattr(response, "status", None)
    incomplete = getattr(response, "incomplete_details", None)
    if status == "incomplete":
        if getattr(incomplete, "reason", None) == "content_filter":
            return None, "proposal_rejected"
        return None, "schema_invalid"
    if status != "completed" or incomplete is not None:
        return None, "provider_error"
    output = getattr(response, "output", None)
    if not isinstance(output, list) or any(getattr(item, "type", None) not in ("message", "reasoning") for item in output):
        return None, "schema_invalid"
    messages = [item for item in output if item.type == "message"]
    if len(messages) != 1:
        return None, "schema_invalid"
    message = messages[0]
    if getattr(message, "role", None) != "assistant" or getattr(message, "status", None) != "completed":
        return None, "schema_invalid"
    content = getattr(message, "content", None)
    if not isinstance(content, list):
        return None, "schema_invalid"
    if any(getattr(item, "type", None) == "refusal" for item in content):
        return None, "proposal_rejected"
    if len(content) != 1 or getattr(content[0], "type", None) != "output_text":
        return None, "schema_invalid"
    text = getattr(content[0], "text", None)
    if not isinstance(text, str) or len(text) > 65536:
        return None, "schema_invalid"
    try:
        raw = json.loads(text)
        if _RESPONSE_VALIDATOR.is_valid(raw):
            return CareerTurnProposal.model_validate(raw), None
    except (ValueError, RecursionError):
        pass
    return None, "schema_invalid"


def _token_count(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


class OpenAICareerModel:
    def __init__(
        self, runtime: ModelRuntime, *, model_snapshot: str, application_commit: str, safety_key: bytes,
        max_output_tokens: int = 1200, timeout_ms: int = 8000,
    ):
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+-\d{4}-\d{2}-\d{2}", model_snapshot):
            raise ValueError("Career model must use a dated OpenAI snapshot")
        if not isinstance(safety_key, bytes) or len(safety_key) < 32:
            raise ValueError("Career safety identifier requires a dedicated key of at least 32 bytes")
        self._runtime = runtime
        self._safety_key = safety_key
        self._application_commit = TypeAdapter(ApplicationCommit).validate_python(application_commit)
        self._manifest = CareerRunManifest(
            schema_version=1, provider="openai", transport="responses", model_snapshot=model_snapshot,
            prompt_name="career-turn", prompt_version="1", prompt_hash=sha256(_PROMPT).hexdigest(),
            response_schema_version="CareerTurnProposal.v1", schema_hash=_SCHEMA_HASH,
            policy_version="career-interview.v1", max_output_tokens=max_output_tokens, timeout_ms=timeout_ms,
            store_response=False,
        )

    @property
    def manifest(self) -> CareerRunManifest:
        return self._manifest

    async def propose(self, request: CareerModelRequest) -> CareerModelResult:
        started = monotonic()
        manifest = self.manifest
        timeout = manifest.timeout_ms / 1000
        safety_id = hmac.digest(
            self._safety_key, f"prismpro:career-safety:v1:{request.owner_id}".encode(), "sha256",
        ).hex()
        response = None
        proposal = None
        request_id = None
        retryable = False
        log_context = _IN_CAREER_REQUEST.set(True)
        try:
            async with asyncio.timeout(timeout):
                client = self._runtime.single_attempt_client()
                if str(client.base_url) != "https://api.openai.com/v1/":
                    raise ValueError("Career proposals require the configured OpenAI API origin")
                response = await client.post(
                    "/responses", cast_to=Response,
                    body={
                        "model": manifest.model_snapshot,
                        "instructions": _PROMPT.decode("utf-8"),
                        "input": [{"role": "user", "content": request.context}],
                        "text": {"format": {"type": "json_schema", "name": "career_turn_proposal",
                                            "schema": _RESPONSE_SCHEMA, "strict": True}},
                        "max_output_tokens": manifest.max_output_tokens,
                        "safety_identifier": safety_id,
                        "store": False,
                    },
                    options={"timeout": timeout, "follow_redirects": False},
                )
            request_id = getattr(response, "_request_id", None)
            proposal, failure = _parse_response(response, manifest.model_snapshot)
        except (TimeoutError, APITimeoutError):
            failure = "model_timeout"
            retryable = True
        except APIError as error:
            retryable = is_transient_model_error(error)
            unavailable = retryable or isinstance(error, APIStatusError) and error.status_code in (401, 403, 429)
            failure = "model_unavailable" if unavailable else "provider_error"
            request_id = getattr(error, "request_id", None)
        except (OpenAIConfigurationError, OpenAIError):
            failure = "model_unavailable"
        except (ValueError, RecursionError):
            failure = "provider_error"
        finally:
            _IN_CAREER_REQUEST.reset(log_context)

        usage = getattr(response, "usage", None)
        metadata = RunMetadata(
            schema_version=1, application_commit=self._application_commit,
            provider_request_id=request_id if isinstance(request_id, str)
            and re.fullmatch(r"req_[A-Za-z0-9_-]{1,100}", request_id) else None,
            input_tokens=_token_count(getattr(usage, "input_tokens", None)),
            output_tokens=_token_count(getattr(usage, "output_tokens", None)),
            latency_ms=int((monotonic() - started) * 1000), failure=failure,
        )
        return CareerModelResult(
            run=StoredRun(schema_version=1, manifest=manifest, metadata=metadata),
            proposal=proposal, retryable=retryable,
        )
