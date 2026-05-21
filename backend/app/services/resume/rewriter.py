import os
import json
import logging
from typing import Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type
from app.schemas.resume_v2 import RewriteResult, Placeholder
from app.services.resume.hallucination_guard import check_no_unprompted_numbers, HallucinationError
from app.core.llm_logging import measure, estimate_cost, log_cost

logger = logging.getLogger("llm")


REWRITER_SYSTEM = """You are a Senior Recruiter rewriting resume bullets at recruiter-grade quality.

RULES (non-negotiable):
1. Never invent numbers, scale, or facts not present in the original bullet.
   If quantification is missing, use a placeholder token like [X%], [N users], [$Y revenue].
   The user will fill these in.
2. Strengthen verbs (Built → Engineered/Architected/Led/Shipped).
3. Apply Google's XYZ structure: Accomplished X as measured by Y, by doing Z.
4. No buzzwords ('synergies', 'leverage', 'utilize'). Direct verbs only.
5. One line per bullet. Max ~25 words.
6. Country-aware tone:
   - US target: action-first, impact-front.
   - India target: scope + action, slightly more context allowed.

OUTPUT: strict JSON:
{
  "rewritten": str,
  "placeholders": [{"token": str, "what": str}],
  "applied_changes": [str, ...]
}"""


REWRITER_USER = """Original bullet:
{original}

Target role: {target_role}
Target country: {country}
JD context (may be empty): {jd_context}

Rewrite the bullet."""


_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4),
       retry=retry_if_not_exception_type(HallucinationError))
async def rewrite_bullet(
    original: str,
    target_role: str,
    jd_context: Optional[str] = None,
    country: str = "US",
    user_id: str | None = None,
) -> RewriteResult:
    user = REWRITER_USER.format(
        original=original, target_role=target_role,
        country=country, jd_context=jd_context or "",
    )
    async with measure("rewriter", user_id=user_id):
        resp = await _client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": REWRITER_SYSTEM},
                      {"role": "user", "content": user}],
            temperature=0.4,
        )
    log_cost("rewriter", resp.usage, user_id=user_id)
    data = json.loads(resp.choices[0].message.content or "{}")
    result = RewriteResult.model_validate(data)
    check_no_unprompted_numbers(
        original=original,
        rewritten=result.rewritten,
        placeholders=[p.model_dump() for p in result.placeholders],
    )
    return result
