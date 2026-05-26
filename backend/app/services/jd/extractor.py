import os
import json
import logging
from openai import AsyncOpenAI, RateLimitError, APIConnectionError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.schemas.jd import JDExtraction
from app.core.llm_logging import measure, estimate_cost, log_cost

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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

If a field has no items, return an EMPTY ARRAY []. Never use a dict where an array is required.
Every item in must_have / good_to_have MUST be an object with all three fields populated."""


@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)))
async def extract_jd_requirements(jd_text: str, user_id: str | None = None) -> JDExtraction:
    """Extract structured JD requirements via schema-enforced parse()."""
    async with measure("extractor", user_id=user_id):
        resp = await _client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            response_format=JDExtraction,
            messages=[
                {"role": "system", "content": EXTRACTOR_SYSTEM},
                {"role": "user", "content": f"Job description:\n\n{jd_text}\n\nExtract requirements."},
            ],
            temperature=0.1,
        )
    log_cost("extractor", resp.usage, user_id=user_id)
    parsed = resp.choices[0].message.parsed
    if parsed is None:
        raise ValueError("OpenAI returned no parsed content for JD extraction")
    return parsed
