import os
import json
import logging
from openai import AsyncOpenAI, RateLimitError, APIConnectionError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.schemas.jd import JDExtraction
from app.core.llm_logging import measure, estimate_cost

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger("llm")

EXTRACTOR_SYSTEM = """You parse job descriptions for hiring intelligence. Distinguish:
- must_have: explicitly required (years, hard skills, credentials)
- good_to_have: 'nice to have', 'plus', 'preferred'
- soft_skills: behavioral/interpersonal expectations
- seniority: junior | mid | senior | staff (infer from years/scope)
- primary_role_category: SWE | DS | PM | other
- country_hint: US | IN | other (infer from compensation currency, location, language style)
- red_flags: undisclosed comp, vague responsibilities, unrealistic stack breadth

Output strict JSON per schema."""


@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)))
async def extract_jd_requirements(jd_text: str) -> JDExtraction:
    async with measure("extractor"):
        resp = await _client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": EXTRACTOR_SYSTEM},
                {"role": "user", "content": f"Job description:\n\n{jd_text}\n\nExtract requirements."},
            ],
            temperature=0.1,
        )
    logger.info(
        {"event": "llm_cost", "label": "extractor", "cost_usd": estimate_cost(resp.usage)}
    )
    return JDExtraction.model_validate_json(resp.choices[0].message.content or "{}")
