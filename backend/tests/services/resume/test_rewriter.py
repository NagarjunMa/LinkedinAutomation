import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import pytest
import respx
import httpx
import json
from app.services.resume.rewriter import rewrite_bullet

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


@pytest.mark.asyncio
@respx.mock
async def test_rewriter_returns_result_with_placeholders():
    mock_payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "rewritten": "Engineered an event-driven pipeline serving [N events/day], reducing latency by [X%]",
                "placeholders": [{"token": "[N events/day]", "what": "daily event volume"},
                                 {"token": "[X%]", "what": "latency reduction"}],
                "applied_changes": ["XYZ structure", "stronger verb 'Engineered'"]
            })}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=mock_payload))
    result = await rewrite_bullet(
        original="Built a data pipeline",
        target_role="Senior SWE",
        jd_context=None,
    )
    assert "[N events/day]" in result.rewritten
    assert len(result.placeholders) == 2


@pytest.mark.asyncio
@respx.mock
async def test_rewriter_blocks_hallucinated_numbers():
    mock_payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "rewritten": "Engineered an event-driven pipeline serving 5M events/day, reducing latency by 40%",
                "placeholders": [],
                "applied_changes": []
            })}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=mock_payload))
    from app.services.resume.hallucination_guard import HallucinationError
    with pytest.raises(HallucinationError):
        await rewrite_bullet(original="Built a data pipeline",
                             target_role="Senior SWE", jd_context=None)
