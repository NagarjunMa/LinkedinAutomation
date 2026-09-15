import logging
from itertools import chain
from openai import RateLimitError, APIConnectionError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.schemas.resume_v2 import ResumeDocumentJSON
from app.schemas.jd import BulletDiff, BulletOption, JDExtraction, DiffPlan, BulletTruthCheck
from app.services.resume.hallucination_guard import analyze_rewrite_truth, HallucinationError
from app.services.resume.content_fit import enrich_diff_plan_with_content_fit
from app.core.llm_logging import measure, log_cost
from app.core.openai_client import ModelRuntime, get_model_runtime


logger = logging.getLogger("llm")

TAILOR_SYSTEM = """You tailor a candidate's resume to a specific JD as a senior recruiter would.

Return a DiffPlan JSON object with these EXACT fields (all required, even when empty):
- match_score: int 0-100
- must_have_coverage_found: ARRAY of skill name strings (empty array if none)
- must_have_coverage_missing: ARRAY of skill name strings (empty array if none)
- good_to_have_coverage_found: ARRAY of skill name strings (empty array if none)
- good_to_have_coverage_missing: ARRAY of skill name strings (empty array if none)
- bullets: ARRAY of BulletDiff objects {bullet_id, old, new, reason, placeholders: [], options: []} (empty array if no rewrites)
  - new must match the recommended option text for backward compatibility.
  - options must contain exactly 3 choices when rewriting a bullet:
    1. option_id "conservative": clear, low-risk rewrite close to the original evidence.
    2. option_id "impact": impact-focused rewrite using only verified metrics or placeholders.
    3. option_id "keyword": JD keyword-aligned rewrite using only resume-supported skills.
  - Every option object must be {option_id, text, reason, placeholders: []}.
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

OPTIONS_SYSTEM = """You generate three safe alternatives for one resume bullet against one JD.

Return a BulletDiff JSON object with:
- bullet_id
- old
- new
- reason
- placeholders
- options

Rules:
- Return exactly three options with option_id values: conservative, impact, keyword.
- Set new to the recommended option text.
- NEVER fabricate numbers/metrics. Use placeholders like [X%], [N users].
- NEVER add a skill the candidate has no evidence of.
- Keep each option as one resume bullet."""

OPTIONS_USER = """Bullet id:
{bullet_id}

Original bullet:
{original}

Resume JSON:
{resume_json}

JD Requirements JSON:
{jd_json}

Generate exactly three alternatives."""


def _jd_skill_terms(jd: JDExtraction) -> list[str]:
    return [req.skill for req in [*jd.must_have, *jd.good_to_have] if req.skill]


def _resume_supported_skill_terms(doc: ResumeDocumentJSON) -> list[str]:
    bullet_text = [
        b.text
        for item in chain(doc.experience, doc.projects)
        for b in item.bullets
    ]
    return [
        *doc.skills.hard,
        *doc.skills.soft,
        doc.raw_text or "",
        *bullet_text,
    ]


def _attach_truth_checks(
    *,
    diff: BulletDiff,
    original: str,
    jd_skill_terms: list[str],
    resume_supported_skill_terms: list[str],
) -> None:
    candidates = [(diff, diff.new, diff.placeholders)] + [
        (option, option.text, option.placeholders) for option in diff.options
    ]
    for target, rewritten, placeholders in candidates:
        try:
            truth = analyze_rewrite_truth(
                original=original,
                rewritten=rewritten,
                placeholders=[p.model_dump() for p in placeholders],
                jd_skill_terms=jd_skill_terms,
                resume_supported_skill_terms=resume_supported_skill_terms,
            )
        except HallucinationError as e:
            raise HallucinationError(f"Bullet {diff.bullet_id}: {e}")
        target.truth_check = BulletTruthCheck.model_validate(truth)


@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)))
async def tailor_resume_to_jd(
    doc: ResumeDocumentJSON,
    jd: JDExtraction,
    user_id: str | None = None,
    *,
    runtime: ModelRuntime | None = None,
) -> DiffPlan:
    """Tailor a resume to a JD via schema-enforced parse() API."""
    runtime = runtime or get_model_runtime()
    manifest = runtime.manifests["tailor"]
    user = TAILOR_USER.format(
        resume_json=doc.model_dump_json(exclude={"raw_text"}),
        jd_json=jd.model_dump_json(),
    )
    async with measure("tailor", user_id=user_id):
        resp = await runtime.client_factory().beta.chat.completions.parse(
            model=manifest.model_snapshot,
            response_format=DiffPlan,
            messages=[{"role": "system", "content": TAILOR_SYSTEM},
                      {"role": "user", "content": user}],
            temperature=manifest.parameters.temperature,
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
    jd_terms = _jd_skill_terms(jd)
    resume_terms = _resume_supported_skill_terms(doc)
    for diff in plan.bullets:
        if not diff.options:
            diff.options = [
                BulletOption(
                    option_id="recommended",
                    text=diff.new,
                    reason=diff.reason,
                    placeholders=diff.placeholders,
                )
            ]
        original = bullet_lookup.get(diff.bullet_id, diff.old)
        _attach_truth_checks(
            diff=diff,
            original=original,
            jd_skill_terms=jd_terms,
            resume_supported_skill_terms=resume_terms,
        )
    return enrich_diff_plan_with_content_fit(doc, jd, plan)


@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)))
async def generate_bullet_options(
    *,
    doc: ResumeDocumentJSON,
    jd: JDExtraction,
    bullet_id: str,
    original: str,
    user_id: str | None = None,
    runtime: ModelRuntime | None = None,
) -> BulletDiff:
    """Generate three JD-aware alternatives for one bullet."""
    runtime = runtime or get_model_runtime()
    manifest = runtime.manifests["tailor_options"]
    user = OPTIONS_USER.format(
        bullet_id=bullet_id,
        original=original,
        resume_json=doc.model_dump_json(exclude={"raw_text"}),
        jd_json=jd.model_dump_json(),
    )
    async with measure("tailor_options", user_id=user_id):
        resp = await runtime.client_factory().beta.chat.completions.parse(
            model=manifest.model_snapshot,
            response_format=BulletDiff,
            messages=[{"role": "system", "content": OPTIONS_SYSTEM},
                      {"role": "user", "content": user}],
            temperature=manifest.parameters.temperature,
        )
    log_cost("tailor_options", resp.usage, user_id=user_id)
    diff = resp.choices[0].message.parsed
    if diff is None:
        raise ValueError("OpenAI returned no parsed content for bullet options")
    if not diff.options:
        diff.options = [
            BulletOption(
                option_id="recommended",
                text=diff.new,
                reason=diff.reason,
                placeholders=diff.placeholders,
            )
        ]
    diff.bullet_id = bullet_id
    diff.old = original
    _attach_truth_checks(
        diff=diff,
        original=original,
        jd_skill_terms=_jd_skill_terms(jd),
        resume_supported_skill_terms=_resume_supported_skill_terms(doc),
    )
    return diff
