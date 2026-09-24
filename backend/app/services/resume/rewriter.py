import json
import logging
from typing import Optional
from app.core.model_retry import retry_model_call
from app.schemas.resume_v2 import RewriteResult
from app.services.resume.hallucination_guard import check_no_unprompted_numbers
from app.core.llm_logging import measure, log_cost
from app.core.openai_client import ModelRuntime, get_model_runtime

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


@retry_model_call(attempts=2, max_wait=4)
async def rewrite_bullet(
    original: str,
    target_role: str,
    jd_context: Optional[str] = None,
    country: str = "US",
    user_id: str | None = None,
    *,
    runtime: ModelRuntime | None = None,
) -> RewriteResult:
    runtime = runtime or get_model_runtime()
    manifest = runtime.manifests["rewriter"]
    user = REWRITER_USER.format(
        original=original, target_role=target_role,
        country=country, jd_context=jd_context or "",
    )
    async with measure("rewriter", manifest=manifest):
        resp = await runtime.single_attempt_client().chat.completions.create(
            model=manifest.model_snapshot,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": REWRITER_SYSTEM},
                      {"role": "user", "content": user}],
            temperature=manifest.parameters.temperature,
        )
        log_cost("rewriter", resp.usage, manifest=manifest, response_model=getattr(resp, "model", None))
        data = json.loads(resp.choices[0].message.content or "{}")
        result = RewriteResult.model_validate(data)
        check_no_unprompted_numbers(
            original=original,
            rewritten=result.rewritten,
            placeholders=[p.model_dump() for p in result.placeholders],
        )
        return result
