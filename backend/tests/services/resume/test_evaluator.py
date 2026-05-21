import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import pytest
import respx
import httpx
import json
from app.services.resume.evaluator import evaluate_resume
from app.schemas.resume_v2 import ResumeDocumentJSON, Contact, ExperienceEntry, Bullet, Skills

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def make_doc():
    return ResumeDocumentJSON(
        contact=Contact(name="A B", email="a@b.com"),
        experience=[ExperienceEntry(company="Acme", role="SWE",
            bullets=[Bullet(id="b1", text="Did stuff", raw_text="Did stuff"),
                     Bullet(id="b2", text="Improved performance 30%", raw_text="...")])],
        skills=Skills(hard=["Python"]),
        raw_text="...",
    )


@pytest.mark.asyncio
@respx.mock
async def test_evaluator_returns_report():
    mock_payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{
            "index": 0, "finish_reason": "stop",
            "message": {"role": "assistant",
                "content": json.dumps({
                    "overall_score": 60,
                    "bullet_flags": [
                        {"bullet_id": "b1", "severity": "critical",
                         "reason": "no quantification, vague verb",
                         "category": "quantification"}
                    ],
                    "format_issues": [],
                    "summary_critique": None,
                    "skill_gaps": [],
                })}
        }],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=mock_payload)
    )
    report = await evaluate_resume(make_doc(), target_role="SWE")
    assert report.overall_score == 60
    assert any(f.bullet_id == "b1" and f.severity == "critical" for f in report.bullet_flags)


@pytest.mark.asyncio
@respx.mock
async def test_evaluator_logs_cost(caplog):
    """Verify that cost logging event is emitted after a successful evaluate call."""
    import logging
    mock_payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{
            "index": 0, "finish_reason": "stop",
            "message": {"role": "assistant",
                "content": json.dumps({
                    "overall_score": 70,
                    "bullet_flags": [],
                    "format_issues": [],
                    "summary_critique": None,
                    "skill_gaps": [],
                })}
        }],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=mock_payload)
    )
    with caplog.at_level(logging.INFO, logger="llm"):
        await evaluate_resume(make_doc(), target_role="SWE")
    messages = [r.message for r in caplog.records]
    assert any("llm_cost" in str(m) for m in messages), (
        f"Expected 'llm_cost' log record from llm logger; got: {messages}"
    )


@pytest.mark.asyncio
@respx.mock
async def test_evaluator_invalid_schema_raises():
    bad = {"id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o",
           "choices": [{"index": 0, "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "{\"overall_score\": \"not-an-int\"}"}}],
           "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=bad)
    )
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        await evaluate_resume(make_doc(), target_role="SWE")
