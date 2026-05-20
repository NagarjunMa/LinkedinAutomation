import os
import json
from openai import AsyncOpenAI
from app.schemas.jd import JDExtraction

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EXTRACTOR_SYSTEM = """You parse job descriptions for hiring intelligence. Distinguish:
- must_have: explicitly required (years, hard skills, credentials)
- good_to_have: 'nice to have', 'plus', 'preferred'
- soft_skills: behavioral/interpersonal expectations
- seniority: junior | mid | senior | staff (infer from years/scope)
- primary_role_category: SWE | DS | PM | other
- country_hint: US | IN | other (infer from compensation currency, location, language style)
- red_flags: undisclosed comp, vague responsibilities, unrealistic stack breadth

Output strict JSON per schema."""


async def extract_jd_requirements(jd_text: str) -> JDExtraction:
    resp = await _client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTOR_SYSTEM},
            {"role": "user", "content": f"Job description:\n\n{jd_text}\n\nExtract requirements."},
        ],
        temperature=0.1,
    )
    return JDExtraction.model_validate_json(resp.choices[0].message.content or "{}")
