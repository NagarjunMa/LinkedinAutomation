import logging
from app.core.model_retry import retry_model_call
from app.schemas.jd import JDExtraction
from app.core.llm_logging import measure, log_cost
from app.core.openai_client import ModelRuntime, get_model_runtime

logger = logging.getLogger("llm")

EXTRACTOR_SYSTEM = """You parse job descriptions for hiring intelligence.

Return a JSON object matching the JDExtraction schema EXACTLY:
- must_have: ARRAY of objects, each {skill: str, evidence_from_jd: str, type: "technical"|"experience"|"credential"}
- good_to_have: SAME shape — ARRAY of those objects, NOT plain strings, NOT a dict
- soft_skills: ARRAY of strings
- seniority: one of "junior" | "mid" | "senior" | "staff"
- primary_role_category: "SWE" | "DS" | "PM" | "other"
- country_hint: "US" | "IN" | "other"
- red_flags: ARRAY of strings
- company_name: best-effort extraction of the hiring company's name from the JD body. If the JD is a blind recruiter post and the company is not named, return null.
- job_title: best-effort extraction of the human-readable role title from the JD, such as "Senior Backend Engineer". If unclear, return null.

If a field has no items, return an EMPTY ARRAY []. Never use a dict where an array is required.
Every item in must_have / good_to_have MUST be an object with all three fields populated."""


@retry_model_call()
async def extract_jd_requirements(
    jd_text: str, user_id: str | None = None, *, runtime: ModelRuntime | None = None,
) -> JDExtraction:
    """Extract structured JD requirements via schema-enforced parse()."""
    runtime = runtime or get_model_runtime()
    manifest = runtime.manifests["extractor"]
    async with measure("extractor", manifest=manifest):
        resp = await runtime.single_attempt_client().beta.chat.completions.parse(
            model=manifest.model_snapshot,
            response_format=JDExtraction,
            messages=[
                {"role": "system", "content": EXTRACTOR_SYSTEM},
                {"role": "user", "content": f"Job description:\n\n{jd_text}\n\nExtract requirements."},
            ],
            temperature=manifest.parameters.temperature,
        )
        log_cost("extractor", resp.usage, manifest=manifest, response_model=getattr(resp, "model", None))
        parsed = resp.choices[0].message.parsed
        if parsed is None:
            raise ValueError("OpenAI returned no parsed content for JD extraction")
        return parsed
