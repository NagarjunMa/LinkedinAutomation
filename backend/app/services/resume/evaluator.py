import json
import logging
from openai import RateLimitError, APIConnectionError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.schemas.resume_v2 import ResumeDocumentJSON, EvaluationReport
from app.core.llm_logging import measure, log_cost
from app.core.openai_client import ModelRuntime, get_model_runtime

logger = logging.getLogger("llm")


SYSTEM_PROMPT = """You are a Senior Recruiter with 15+ years of experience hiring at FAANG and high-growth startups in both US and Indian markets. You evaluate resumes the way you would in a real screening: brutally honest, specific, and actionable. You apply:
- Google's XYZ formula: "Accomplished [X] as measured by [Y], by doing [Z]"
- 7-second scan rule: would the reader grasp impact from the top of the page?
- ATS parsing reality: keyword density, structural simplicity
- Country-aware tone (US: action-first; India: scope + action)
- Raw ATS text is the ground truth when structured JSON is incomplete.

For EVERY bullet, decide if it has issues. Flag with severity:
- "critical": vague, responsibility-only, weak verb, or unclear outcome
- "warning": acceptable but could be stronger or more measurable
- "info": already strong

Categories: quantification | verb | structure | clarity | redundancy | ats

Never invent metrics. Never fabricate facts.
Do not automatically mark every unquantified bullet as critical; judge severity by clarity, action, outcome, and role relevance.
Do not flag missing dates if dates are present in the raw ATS text.
Do not flag empty bullets if bullets are present in the raw ATS text but absent from structured JSON.
If structured JSON is incomplete but raw ATS text is readable, set parser_confidence lower and explain the parser concern separately instead of lowering resume quality for parser failure.

Scoring rules:
- overall_score is a calibrated recruiter readiness score, not an average of parser warnings.
- score_breakdown.content_quality measures clarity, structure, action verbs, and concise writing.
- score_breakdown.role_fit measures alignment with the target role using only evidence in the resume.
- score_breakdown.evidence_strength measures quantified outcomes, scope, complexity, and proof.
- score_breakdown.recruiter_readability measures 7-second scan value, signal density, and noise.
- score_explanation must cite resume evidence or clearly say what is missing. Never use generic canned evidence.
- top_actions_before_applying should be the 1-5 highest-impact fixes a user should make before applying."""

USER_PROMPT_TEMPLATE = """Target role: {target_role}

Structured resume JSON:
{resume_json}

Raw ATS text:
{raw_text}

Evaluate the resume. Return STRICTLY this JSON schema:
{{
  "overall_score": int 0-100,
  "readiness_label": "ready" | "minor_edits" | "needs_work",
  "score_breakdown": {{
    "content_quality": int 0-100,
    "role_fit": int 0-100,
    "evidence_strength": int 0-100,
    "recruiter_readability": int 0-100
  }},
  "score_explanation": [
    {{
      "category": "content_quality" | "role_fit" | "evidence_strength" | "recruiter_readability",
      "score": int 0-100,
      "reason": str,
      "evidence": [str, ...],
      "before_applying_action": str
    }},
    ...
  ],
  "top_actions_before_applying": [str, ...],
  "parser_confidence": "high" | "medium" | "low",
  "bullet_flags": [{{"bullet_id": str, "severity": str, "reason": str, "category": str}}, ...],
  "format_issues": [{{"type": str, "location": str, "fix_hint": str}}, ...],
  "summary_critique": str or null,
  "skill_gaps": [str, ...]
}}"""


@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)))
async def evaluate_resume(
    doc: ResumeDocumentJSON,
    target_role: str,
    user_id: str | None = None,
    *,
    runtime: ModelRuntime | None = None,
) -> EvaluationReport:
    runtime = runtime or get_model_runtime()
    manifest = runtime.manifests["evaluator"]
    payload = doc.model_dump_json(exclude={"raw_text"})
    user_msg = USER_PROMPT_TEMPLATE.format(
        target_role=target_role,
        resume_json=payload,
        raw_text=(doc.raw_text or "")[:12000],
    )
    async with measure("evaluator", user_id=user_id):
        resp = await runtime.client_factory().chat.completions.create(
            model=manifest.model_snapshot,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=manifest.parameters.temperature,
        )
    log_cost("evaluator", resp.usage, user_id=user_id)
    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)
    return EvaluationReport.model_validate(data)
