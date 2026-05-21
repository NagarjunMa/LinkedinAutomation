import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import pytest
import respx
import httpx
import json
from app.services.jd.tailor import tailor_resume_to_jd
from app.schemas.resume_v2 import ResumeDocumentJSON, Contact, ExperienceEntry, ProjectEntry, Bullet, Skills
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


@pytest.mark.asyncio
@respx.mock
async def test_tailor_guards_project_bullets():
    """Hallucination guard must fire for project bullets using the ACTUAL stored text.

    Before the fix, project bullets were excluded from bullet_lookup so the
    guard fell back to ``diff.old`` (the LLM's claimed original).  A malicious
    or confused LLM can fabricate the same number in both ``diff.old`` and
    ``diff.new``, making the guard a no-op:

        actual stored text: "Built a CLI"        (no numbers)
        diff.old (LLM claim): "Built a CLI with 1M users"   (fabricated)
        diff.new:             "Built a CLI with 5M users"   (fabricated rewrite)

    With the bug, original = diff.old → {1M}, new_nums = {5M}, leaked = {5M}...
    actually that still catches it. The real bypass is:

        diff.old (LLM claim): "Built a CLI with 5M users"   (same as new)
        diff.new:             "Built a CLI with 5M users"

    or more subtly, diff.old claims a number that is also in diff.new so
    ``leaked`` is empty.  With the fix, original = actual stored "Built a CLI"
    (no numbers) so any number in diff.new is leaked.

    This test exercises: stored bullet has no numbers, LLM claims diff.old has
    the same fabricated number as diff.new → leaked is empty WITHOUT the fix,
    non-empty WITH the fix.
    """
    # LLM claims the original already had "5M" (fabricated in diff.old),
    # and the rewrite also has "5M" — so diff.old-based check sees no new numbers.
    # But the actual stored text "Built a CLI" has no numbers, so the fix catches it.
    payload = {
        "id": "x", "object": "chat.completion", "created": 0, "model": "gpt-4o-2024-08-06",
        "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps({
                "match_score": 70,
                "must_have_coverage_found": [],
                "must_have_coverage_missing": [],
                "good_to_have_coverage_found": [],
                "good_to_have_coverage_missing": [],
                "bullets": [{"bullet_id": "proj-b1",
                             "old": "Built a CLI with 5M downloads",
                             "new": "Built a CLI with 5M downloads serving enterprise clients",
                             "reason": "added context",
                             "placeholders": []}],
                "skills_reorder": None,
                "summary_rewrite": None,
                "suggested_additions": []
            })}}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    respx.route(url=OPENAI_URL).mock(return_value=httpx.Response(200, json=payload))

    # Resume has NO experience entries — only a projects entry with the bullet.
    # The stored text has NO numbers — the "5M" in diff.old is fabricated.
    doc = ResumeDocumentJSON(
        contact=Contact(name="C"),
        experience=[],
        projects=[ProjectEntry(
            name="Toolbox",
            bullets=[Bullet(id="proj-b1", text="Built a CLI", raw_text="Built a CLI")],
        )],
        skills=Skills(hard=["Python"]),
        raw_text="Built a CLI",
    )
    jd = JDExtraction(
        must_have=[], good_to_have=[], soft_skills=[], seniority="mid",
        primary_role_category="SWE", country_hint="US", red_flags=[])

    from app.services.resume.hallucination_guard import HallucinationError
    with pytest.raises(HallucinationError):
        await tailor_resume_to_jd(doc, jd)
