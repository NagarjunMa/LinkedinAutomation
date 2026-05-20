import os
import json
import logging
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.schemas.resume import ResumeDocumentJSON, EvaluationReport
from app.core.llm_logging import measure, estimate_cost

logger = logging.getLogger("llm")


SYSTEM_PROMPT = """You are a Senior Recruiter with 15+ years of experience hiring at FAANG and high-growth startups in both US and Indian markets. You evaluate resumes the way you would in a real screening: brutally honest, specific, and actionable. You apply:
- Google's XYZ formula: "Accomplished [X] as measured by [Y], by doing [Z]"
- 7-second scan rule: would the reader grasp impact from the top of the page?
- ATS parsing reality: keyword density, structural simplicity
- Country-aware tone (US: action-first; India: scope + action)

For EVERY bullet, decide if it has issues. Flag with severity:
- "critical": missing quantification, weak verb, or unclear impact
- "warning": acceptable but improvable
- "info": already strong

Categories: quantification | verb | structure | clarity | redundancy | ats

Never invent metrics. Never fabricate facts. If a bullet lacks numbers, flag it; don't fill in numbers yourself."""

USER_PROMPT_TEMPLATE = """Target role: {target_role}

Resume JSON:
{resume_json}

Evaluate the resume. Return STRICTLY this JSON schema:
{{
  "overall_score": int 0-100,
  "bullet_flags": [{{"bullet_id": str, "severity": str, "reason": str, "category": str}}, ...],
  "format_issues": [{{"type": str, "location": str, "fix_hint": str}}, ...],
  "summary_critique": str or null,
  "skill_gaps": [str, ...]
}}"""


_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((TimeoutError,)))
async def evaluate_resume(doc: ResumeDocumentJSON, target_role: str) -> EvaluationReport:
    payload = doc.model_dump_json(exclude={"raw_text"})
    user_msg = USER_PROMPT_TEMPLATE.format(target_role=target_role, resume_json=payload)
    async with measure("evaluator"):
        resp = await _client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
        )
    logger.info(
        {"event": "llm_cost", "label": "evaluator", "cost_usd": estimate_cost(resp.usage)}
    )
    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)
    return EvaluationReport.model_validate(data)
