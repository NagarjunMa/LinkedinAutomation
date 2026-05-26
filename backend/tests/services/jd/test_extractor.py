import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import pytest
import respx
import httpx
import json
from app.services.jd.extractor import extract_jd_requirements

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


@pytest.mark.asyncio
@respx.mock
async def test_extractor_returns_requirements():
    payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "must_have": [{"skill": "Python", "evidence_from_jd": "5+ yrs Python", "type": "technical"}],
                "good_to_have": [],
                "soft_skills": ["communication"],
                "seniority": "senior",
                "primary_role_category": "SWE",
                "country_hint": "US",
                "red_flags": [],
            })}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=payload))
    result = await extract_jd_requirements("Senior Python role at Stripe...")
    assert any(r.skill == "Python" for r in result.must_have)
    assert result.seniority == "senior"


@pytest.mark.asyncio
@respx.mock
async def test_extractor_returns_company_name_when_present():
    payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "must_have": [{"skill": "Python", "evidence_from_jd": "5+ yrs", "type": "technical"}],
                "good_to_have": [],
                "soft_skills": [],
                "seniority": "senior",
                "primary_role_category": "SWE",
                "country_hint": "US",
                "red_flags": [],
                "company_name": "Stripe",
            })}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=payload))
    result = await extract_jd_requirements("Senior Python at Stripe...")
    assert result.company_name == "Stripe"


@pytest.mark.asyncio
@respx.mock
async def test_extractor_returns_null_company_when_blind():
    payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "must_have": [{"skill": "Python", "evidence_from_jd": "5+ yrs", "type": "technical"}],
                "good_to_have": [],
                "soft_skills": [],
                "seniority": "mid",
                "primary_role_category": "SWE",
                "country_hint": "US",
                "red_flags": [],
                "company_name": None,
            })}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=payload))
    result = await extract_jd_requirements("Confidential client — blind post...")
    assert result.company_name is None
