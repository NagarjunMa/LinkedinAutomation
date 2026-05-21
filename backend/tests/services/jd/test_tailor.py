import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import pytest
import respx
import httpx
import json
from app.services.jd.tailor import tailor_resume_to_jd
from app.schemas.resume_v2 import ResumeDocumentJSON, Contact, ExperienceEntry, Bullet, Skills
from app.schemas.jd import JDExtraction, Requirement

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


@pytest.mark.asyncio
@respx.mock
async def test_tailor_returns_diff_plan():
    payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "match_score": 75,
                "must_have_coverage_found": ["Python"],
                "must_have_coverage_missing": ["Kubernetes"],
                "good_to_have_coverage_found": [],
                "good_to_have_coverage_missing": [],
                "bullets": [{"bullet_id": "b1", "old": "Did stuff",
                             "new": "Shipped Python microservices on AWS",
                             "reason": "JD calls for Python; bullet was vague",
                             "placeholders": []}],
                "skills_reorder": {"new_order": ["Python", "AWS"], "rationale": "Lead with JD-matched"},
                "summary_rewrite": None,
                "suggested_additions": []
            })}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=payload))
    doc = ResumeDocumentJSON(
        contact=Contact(name="A"), experience=[ExperienceEntry(
            company="Acme", role="SWE", bullets=[Bullet(id="b1", text="Did stuff", raw_text="Did stuff")])],
        skills=Skills(hard=["Python"]), raw_text="...")
    jd = JDExtraction(
        must_have=[Requirement(skill="Python", evidence_from_jd="x", type="technical")],
        good_to_have=[], soft_skills=[], seniority="mid",
        primary_role_category="SWE", country_hint="US", red_flags=[])
    plan = await tailor_resume_to_jd(doc, jd)
    assert plan.match_score == 75
    assert plan.bullets[0].bullet_id == "b1"


@pytest.mark.asyncio
@respx.mock
async def test_tailor_blocks_hallucinated_numbers_in_bullet():
    """Hallucination guard should raise if a bullet rewrite introduces new numbers."""
    payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "match_score": 60,
                "must_have_coverage_found": [],
                "must_have_coverage_missing": [],
                "good_to_have_coverage_found": [],
                "good_to_have_coverage_missing": [],
                "bullets": [{"bullet_id": "b1", "old": "Built a feature",
                             "new": "Built a feature used by 5M users daily",
                             "reason": "added scale",
                             "placeholders": []}],
                "skills_reorder": None,
                "summary_rewrite": None,
                "suggested_additions": []
            })}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.route(url=OPENAI_URL).mock(
        return_value=httpx.Response(200, json=payload))
    doc = ResumeDocumentJSON(
        contact=Contact(name="B"), experience=[ExperienceEntry(
            company="Corp", role="Dev", bullets=[Bullet(id="b1", text="Built a feature", raw_text="Built a feature")])],
        skills=Skills(hard=[]), raw_text="...")
    jd = JDExtraction(
        must_have=[], good_to_have=[], soft_skills=[], seniority="mid",
        primary_role_category="SWE", country_hint="US", red_flags=[])
    from app.services.resume.hallucination_guard import HallucinationError
    with pytest.raises(HallucinationError):
        await tailor_resume_to_jd(doc, jd)
