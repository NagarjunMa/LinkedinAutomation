"""Application orchestration for JD analysis and evidence-safe tailoring."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.application.errors import OperationRejectedError, ResourceNotFoundError
from app.application.credits import paid_operation
from app.core.openai_client import ModelRuntime, get_model_runtime
from app.models.jd_evaluation import JDEvaluation
from app.models.resume_document import ResumeVersion
from app.repositories.jd_repository import JDEvaluationRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.jd import BulletDiff, JDExtraction
from app.schemas.resume_v2 import ApplyTailorRequest, ApplyTailorResponse, ResumeDocumentJSON
from app.services.jd.extractor import extract_jd_requirements
from app.services.jd.tailor import generate_bullet_options, tailor_resume_to_jd
from app.services.pdf.export_options import slugify_filename_part
from app.services.pdf.template_engine import (
    _VALID_COUNTRIES,
    _VALID_ROLES,
    render_html_only,
)
from app.services.resume.changes import apply_changes, find_bullet_text
from app.services.resume.hallucination_guard import HallucinationError


_COUNTRY_MAP = {"US": "us", "IN": "in"}
_ROLE_MAP = {"SWE": "swe", "DS": "ds", "PM": "pm"}


class JDTailoringApplicationService:
    def __init__(self, session: Session, *, runtime: ModelRuntime | None = None):
        self.session = session
        self.resumes = ResumeRepository(session)
        self.evaluations = JDEvaluationRepository(session)
        self.runtime = runtime or get_model_runtime()

    async def analyze(
        self,
        *,
        resume_document_id: str,
        jd_text: str,
        user_id: str,
    ) -> dict:
        document = self.resumes.get_owned_ready(resume_document_id, user_id)
        if not document:
            raise ResourceNotFoundError("Resume document not found")

        with paid_operation(self.session, user_id, amount=2, reason="tailor"):
            extraction = await extract_jd_requirements(jd_text, user_id=user_id, runtime=self.runtime)
            resume = ResumeDocumentJSON.model_validate(document.parsed_json)
            try:
                plan = await tailor_resume_to_jd(resume, extraction, user_id=user_id, runtime=self.runtime)
            except HallucinationError as exc:
                raise OperationRejectedError(f"Tailor rejected: {exc}") from exc
            row = JDEvaluation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                resume_document_id=resume_document_id,
                jd_text=jd_text,
                extracted_requirements=extraction.model_dump(),
                diff_plan=plan.model_dump(),
                match_score=plan.match_score,
            )
            self.evaluations.add(row)
            payload = {
                "jd_evaluation_id": row.id,
                "extracted_requirements": extraction.model_dump(),
                "diff_plan": plan.model_dump(),
            }
            self.session.commit()
        return payload

    def apply(
        self,
        evaluation_id: str,
        request: ApplyTailorRequest,
        user_id: str,
    ) -> ApplyTailorResponse:
        evaluation = self._owned_evaluation(evaluation_id, user_id)
        document = self.resumes.get_owned_ready(evaluation.resume_document_id, user_id)
        if not document:
            raise ResourceNotFoundError("Resume document not found")

        base = ResumeDocumentJSON.model_validate(document.parsed_json)
        tailored = apply_changes(base, request.accepted_changes)
        requirements = evaluation.extracted_requirements or {}
        country_hint = requirements.get("country_hint", "US")
        role_category = requirements.get("primary_role_category", "SWE")
        suggested_template = resolve_template(country_hint, role_category)
        template_id = request.template_id or suggested_template
        company_name = requirements.get("company_name")
        target_role_title = requirements.get("job_title") or role_category
        country_code, role_code = suggested_template.split("-")

        version = ResumeVersion(
            id=str(uuid.uuid4()),
            resume_document_id=document.id,
            parent_version_id=None,
            change_set=[change.model_dump() for change in request.accepted_changes],
            parsed_json=tailored.model_dump(),
            jd_evaluation_id=evaluation_id,
            accepted_at=datetime.now(timezone.utc),
            template_id=template_id,
            company_name=company_name,
            target_role_title=target_role_title,
            role_category=role_category,
            seniority=requirements.get("seniority"),
            country_hint=country_hint,
            match_score=evaluation.match_score,
            source_jd_text=evaluation.jd_text,
        )
        self.resumes.add_version(version)
        self.session.commit()

        preview_html, warning = _render_preview(
            tailored,
            country=country_code.upper(),
            role=role_code.lower(),
        )
        filename_parts = []
        if tailored.contact.name:
            filename_parts.append(slugify_filename_part(tailored.contact.name))
        if company_name:
            filename_parts.append(slugify_filename_part(company_name))
        filename_parts.append(role_code)
        return ApplyTailorResponse(
            version_id=version.id,
            preview_html=preview_html,
            company_name=company_name,
            target_role_title=target_role_title,
            suggested_template=suggested_template,
            filename_hint="-".join(filename_parts) + ".pdf",
            warning=warning,
        )

    async def regenerate_options(
        self,
        *,
        evaluation_id: str,
        bullet_id: str,
        user_id: str,
    ) -> BulletDiff:
        evaluation = self._owned_evaluation(evaluation_id, user_id)
        document = self.resumes.get_owned_ready(evaluation.resume_document_id, user_id)
        if not document:
            raise ResourceNotFoundError("Resume document not found")
        resume = ResumeDocumentJSON.model_validate(document.parsed_json)
        original = find_bullet_text(resume, bullet_id)
        if original is None:
            raise ResourceNotFoundError("Bullet not found")
        try:
            requirements = JDExtraction.model_validate(evaluation.extracted_requirements)
            return await generate_bullet_options(
                doc=resume,
                jd=requirements,
                bullet_id=bullet_id,
                original=original,
                user_id=user_id,
                runtime=self.runtime,
            )
        except HallucinationError as exc:
            raise OperationRejectedError(f"Rewrite rejected: {exc}") from exc

    def _owned_evaluation(self, evaluation_id: str, user_id: str) -> JDEvaluation:
        evaluation = self.evaluations.get_owned(evaluation_id, user_id)
        if not evaluation:
            raise ResourceNotFoundError("JD evaluation not found")
        return evaluation


def resolve_template(country_hint: str, role_category: str) -> str:
    country = _COUNTRY_MAP.get(country_hint, "us")
    role = _ROLE_MAP.get(role_category, "swe")
    return f"{country}-{role}"


def _render_preview(
    resume: ResumeDocumentJSON,
    *,
    country: str,
    role: str,
) -> tuple[str, str | None]:
    try:
        if country not in _VALID_COUNTRIES or role not in _VALID_ROLES:
            country, role = "US", "swe"
        return render_html_only(resume, country=country, role=role), None
    except Exception as exc:
        return "", f"Preview render failed: {exc}"
