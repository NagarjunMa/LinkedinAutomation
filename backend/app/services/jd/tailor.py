import os
import logging
from itertools import chain
from openai import AsyncOpenAI, RateLimitError, APIConnectionError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.schemas.resume_v2 import ResumeDocumentJSON
from app.schemas.jd import JDExtraction, DiffPlan
from app.services.resume.hallucination_guard import check_no_unprompted_numbers, HallucinationError
from app.core.llm_logging import measure, log_cost


_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger("llm")

TAILOR_SYSTEM = """You tailor a candidate's resume to a specific JD as a senior recruiter would.

Return a DiffPlan JSON object with these EXACT fields (all required, even when empty):
- match_score: int 0-100
- must_have_coverage_found: ARRAY of skill name strings (empty array if none)
- must_have_coverage_missing: ARRAY of skill name strings (empty array if none)
- good_to_have_coverage_found: ARRAY of skill name strings (empty array if none)
- good_to_have_coverage_missing: ARRAY of skill name strings (empty array if none)
- bullets: ARRAY of BulletDiff objects {bullet_id, old, new, reason, placeholders: []} (empty array if no rewrites)
- skills_reorder: OBJECT {new_order: [str], rationale: str} or null. Do NOT return the raw skills dict — use the new_order/rationale shape.
- summary_rewrite: OBJECT {old: str|null, new: str, reason: str} or null. Do NOT return a bare string — wrap in the object shape.
- suggested_additions: ARRAY of {section: str, item: str, reason: str} (empty array if none)

RULES:
- NEVER fabricate numbers/metrics. Use placeholders like [X%], [N users].
- NEVER add a skill the candidate has no evidence of. If JD requires Kubernetes and resume has zero K8s evidence, add to must_have_coverage_missing, NOT suggested_additions.
- Country-aware tone.
- Use empty arrays [] for empty coverage lists, NEVER omit fields."""

TAILOR_USER = """Resume JSON:
{resume_json}

JD Requirements JSON:
{jd_json}

Produce the DiffPlan."""


@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)))
async def tailor_resume_to_jd(
    doc: ResumeDocumentJSON,
    jd: JDExtraction,
    user_id: str | None = None,
) -> DiffPlan:
    """Tailor a resume to a JD via schema-enforced parse() API."""
    user = TAILOR_USER.format(
        resume_json=doc.model_dump_json(exclude={"raw_text"}),
        jd_json=jd.model_dump_json(),
    )
    async with measure("tailor", user_id=user_id):
        resp = await _client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            response_format=DiffPlan,
            messages=[{"role": "system", "content": TAILOR_SYSTEM},
                      {"role": "user", "content": user}],
            temperature=0.3,
        )
    log_cost("tailor", resp.usage, user_id=user_id)
    plan = resp.choices[0].message.parsed
    if plan is None:
        raise ValueError("OpenAI returned no parsed content for JD tailor")
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
                placeholders=[p.model_dump() for p in diff.placeholders],
            )
        except HallucinationError as e:
            raise HallucinationError(f"Bullet {diff.bullet_id}: {e}")
    return plan
