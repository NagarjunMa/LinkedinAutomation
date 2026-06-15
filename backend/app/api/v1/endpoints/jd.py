"""JD analyze endpoint — extract requirements + tailor resume diff plan."""
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.services.jd.extractor import extract_jd_requirements
from app.services.jd.tailor import generate_bullet_options, tailor_resume_to_jd
from app.services.resume.hallucination_guard import HallucinationError
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.jd_evaluation import JDEvaluation
from app.schemas.resume_v2 import ResumeDocumentJSON, ApplyTailorRequest, ApplyTailorResponse
from app.schemas.jd import BulletDiff, JDExtraction
from app.middleware.credits import credit_transaction
from app.api.v1.endpoints.resumes_v2 import apply_changes

router = APIRouter(prefix="/jd", tags=["jd"])

# ---------------------------------------------------------------------------
# Template resolution helpers
# ---------------------------------------------------------------------------

_COUNTRY_MAP = {"US": "us", "IN": "in"}
_ROLE_MAP = {"SWE": "swe", "DS": "ds", "PM": "pm"}


def _resolve_template(country_hint: str, role_category: str) -> str:
    """Map JDExtraction country/role hints to a template id like 'us-swe'."""
    country = _COUNTRY_MAP.get(country_hint, "us")
    role = _ROLE_MAP.get(role_category, "swe")
    return f"{country}-{role}"


def _slugify(text: str) -> str:
    """Lowercase, replace non-alphanumeric with hyphens, collapse repeats, strip ends.

    Falls back to 'user' if the result is empty.
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug or "user"


def _find_bullet_text(doc: ResumeDocumentJSON, bullet_id: str) -> Optional[str]:
    for item in [*doc.experience, *doc.projects]:
        for bullet in item.bullets:
            if bullet.id == bullet_id:
                return bullet.text
    return None


class AnalyzeRequest(BaseModel):
    resume_document_id: str
    jd_text: str = Field(..., min_length=50)


@router.post("/analyze")
async def analyze(
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """POST /jd/analyze — extract JD requirements, tailor resume, persist result.

    Costs 2 credits. Returns extracted_requirements + diff_plan.
    """
    doc_row = db.get(ResumeDocument, body.resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Resume document not found")

    result_payload = None
    with credit_transaction(db, current_user_id, amount=2, reason="tailor"):
        jd_ext = await extract_jd_requirements(body.jd_text, user_id=current_user_id)
        doc = ResumeDocumentJSON.model_validate(doc_row.parsed_json)
        try:
            plan = await tailor_resume_to_jd(doc, jd_ext, user_id=current_user_id)
        except HallucinationError as e:
            raise HTTPException(status_code=422, detail=f"Tailor rejected: {e}")

        row = JDEvaluation(
            id=str(uuid.uuid4()),
            user_id=current_user_id,
            resume_document_id=body.resume_document_id,
            jd_text=body.jd_text,
            extracted_requirements=jd_ext.model_dump(),
            diff_plan=plan.model_dump(),
            match_score=plan.match_score,
        )
        db.add(row)
        result_payload = {
            "jd_evaluation_id": row.id,
            "extracted_requirements": jd_ext.model_dump(),
            "diff_plan": plan.model_dump(),
        }
    db.commit()
    return result_payload


# ---------------------------------------------------------------------------
# Task 6: POST /jd/{jd_evaluation_id}/apply
# ---------------------------------------------------------------------------

@router.post("/{jd_evaluation_id}/apply", response_model=ApplyTailorResponse)
async def apply_tailor(
    jd_evaluation_id: str,
    body: ApplyTailorRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """POST /jd/{id}/apply — apply accepted changes, persist ResumeVersion, render preview.

    Credit cost: 0.

    Logic (Q6.A invariant):
    - Loads the base ResumeDocument (NEVER a version row) so that multiple JD
      applies on the same document are always independent.
    - Applies accepted_changes via apply_changes().
    - Resolves the template from extracted_requirements.country_hint + primary_role_category.
    - INSERTs a new ResumeVersion with jd_evaluation_id, accepted_at, template_id.
    - Renders preview HTML; on failure returns empty string + warning (no 500).
    - Returns ApplyTailorResponse.
    """
    # Ownership check
    jd_row = db.get(JDEvaluation, jd_evaluation_id)
    if not jd_row or jd_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="JD evaluation not found")

    # Load the base document (Q6.A: NEVER a version row)
    doc_row = db.get(ResumeDocument, jd_row.resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Resume document not found")

    # Apply accepted changes to the BASE document
    base_doc = ResumeDocumentJSON.model_validate(doc_row.parsed_json)
    new_doc = apply_changes(base_doc, body.accepted_changes)

    # Resolve template
    ext_req = jd_row.extracted_requirements or {}
    country_hint = ext_req.get("country_hint", "US")
    role_category = ext_req.get("primary_role_category", "SWE")
    suggested_template = _resolve_template(country_hint, role_category)

    # Determine the template_id to persist (use override if provided)
    template_id = body.template_id or suggested_template
    company_name: Optional[str] = ext_req.get("company_name")
    target_role_title: Optional[str] = ext_req.get("job_title") or role_category

    # Split suggested_template e.g. "us-swe" into country_code + role_code
    country_code, role_code = suggested_template.split("-")
    _country_upper = country_code.upper()   # "US" or "IN"
    _role_lower = role_code.lower()          # "swe", "ds", "pm"

    # INSERT new ResumeVersion
    version_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    version = ResumeVersion(
        id=version_id,
        resume_document_id=doc_row.id,
        parent_version_id=None,
        change_set=[c.model_dump() for c in body.accepted_changes],
        parsed_json=new_doc.model_dump(),
        jd_evaluation_id=jd_evaluation_id,
        accepted_at=now,
        template_id=template_id,
        company_name=company_name,
        target_role_title=target_role_title,
        role_category=role_category,
        seniority=ext_req.get("seniority"),
        country_hint=country_hint,
        match_score=jd_row.match_score,
        source_jd_text=jd_row.jd_text,
    )
    db.add(version)
    db.commit()

    # Render preview HTML — on any exception, return empty + warning
    preview_html = ""
    warning: Optional[str] = None
    try:
        from app.services.pdf.template_engine import render_html_only
        # Validate country/role; fall back to us/swe if unsupported
        from app.services.pdf.template_engine import _VALID_COUNTRIES, _VALID_ROLES
        if _country_upper not in _VALID_COUNTRIES or _role_lower not in _VALID_ROLES:
            _country_upper = "US"
            _role_lower = "swe"
        preview_html = render_html_only(new_doc, country=_country_upper, role=_role_lower)
    except Exception as exc:
        warning = f"Preview render failed: {exc}"

    # Compute filename hint
    contact_name = new_doc.contact.name or ""
    parts = []
    if contact_name:
        parts.append(_slugify(contact_name))
    if company_name:
        parts.append(_slugify(company_name))
    parts.append(role_code)
    filename_hint = "-".join(parts) + ".pdf"

    return ApplyTailorResponse(
        version_id=version_id,
        preview_html=preview_html,
        company_name=company_name,
        target_role_title=target_role_title,
        suggested_template=suggested_template,
        filename_hint=filename_hint,
        warning=warning,
    )


@router.post("/{jd_evaluation_id}/bullets/{bullet_id}/options", response_model=BulletDiff)
async def regenerate_bullet_options(
    jd_evaluation_id: str,
    bullet_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Regenerate three zero-credit options for one JD-tailored bullet."""
    jd_row = db.get(JDEvaluation, jd_evaluation_id)
    if not jd_row or jd_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="JD evaluation not found")

    doc_row = db.get(ResumeDocument, jd_row.resume_document_id)
    if not doc_row or doc_row.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Resume document not found")

    doc = ResumeDocumentJSON.model_validate(doc_row.parsed_json)
    original = _find_bullet_text(doc, bullet_id)
    if original is None:
        raise HTTPException(status_code=404, detail="Bullet not found")

    try:
        jd = JDExtraction.model_validate(jd_row.extracted_requirements)
        return await generate_bullet_options(
            doc=doc,
            jd=jd,
            bullet_id=bullet_id,
            original=original,
            user_id=current_user_id,
        )
    except HallucinationError as exc:
        raise HTTPException(status_code=422, detail=f"Rewrite rejected: {exc}") from exc
