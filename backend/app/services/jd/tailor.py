import os
import json
import logging
from itertools import chain
from openai import AsyncOpenAI, RateLimitError, APIConnectionError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.schemas.resume_v2 import ResumeDocumentJSON
from app.schemas.jd import JDExtraction, DiffPlan
from app.services.resume.hallucination_guard import check_no_unprompted_numbers, HallucinationError
from app.core.llm_logging import measure, estimate_cost


_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger("llm")

TAILOR_SYSTEM = """You tailor a candidate's resume to a specific JD as a senior recruiter would.

Produce a DIFF PLAN:
- Match score (0-100) based on must_have/good_to_have coverage.
- For each bullet, decide whether it should be rewritten for this JD. If so, propose the new bullet.
- Reorder skills list to lead with JD-matched ones. Provide rationale.
- Optionally rewrite the summary for the target role.
- Suggest additions ONLY if the candidate has evidence (in projects/experience) but the skill is not surfaced.

RULES:
- NEVER fabricate numbers/metrics. Use placeholders like [X%], [N users].
- NEVER add a skill the candidate has no evidence of. If JD requires Kubernetes and resume has zero K8s evidence, add to must_have_coverage_missing, NOT suggested_additions.
- Country-aware tone."""

TAILOR_USER = """Resume JSON:
{resume_json}

JD Requirements JSON:
{jd_json}

Produce the DiffPlan."""


@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)))
async def tailor_resume_to_jd(doc: ResumeDocumentJSON, jd: JDExtraction) -> DiffPlan:
    user = TAILOR_USER.format(
        resume_json=doc.model_dump_json(exclude={"raw_text"}),
        jd_json=jd.model_dump_json(),
    )
    async with measure("tailor"):
        resp = await _client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": TAILOR_SYSTEM},
                      {"role": "user", "content": user}],
            temperature=0.3,
        )
    logger.info(
        {"event": "llm_cost", "label": "tailor", "cost_usd": estimate_cost(resp.usage)}
    )
    plan = DiffPlan.model_validate_json(resp.choices[0].message.content or "{}")
    # Hallucination guard on each bullet rewrite.
    # Include both experience AND project bullets so the guard always uses the
    # actual stored text rather than falling back to diff.old (the LLM's own
    # claimed original, which can itself be fabricated).
    bullet_lookup = {
        b.id: b.text
        for item in chain(doc.experience, doc.projects)
        for b in item.bullets
    }
    for diff in plan.bullets:
        original = bullet_lookup.get(diff.bullet_id, diff.old)
        try:
            check_no_unprompted_numbers(
                original=original,
                rewritten=diff.new,
                placeholders=diff.placeholders,
            )
        except HallucinationError as e:
            raise HallucinationError(f"Bullet {diff.bullet_id}: {e}")
    return plan
