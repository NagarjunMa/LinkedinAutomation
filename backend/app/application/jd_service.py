"""Application orchestration for JD analysis and evidence-safe tailoring."""

import json
import uuid
from datetime import datetime, timezone
from os import getenv

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.career_encryption import career_cipher, open_private_text
from app.application.career_service import CareerApplicationService
from app.application.credits import paid_operation
from app.application.errors import ExternalServiceError, OperationRejectedError, ResourceConflictError, ResourceNotFoundError
from app.application.evidence_service import EvidenceService
from app.application.grounded_tailor import GroundedTailorPreview, plan_grounded_bullets, wording_options
from app.application.lineage_service import LineageService
from app.application.resume_service import ResumeApplicationService
from app.core.openai_client import ModelRuntime, get_model_runtime
from app.models.jd_evaluation import JDEvaluation
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.user import User
from app.repositories.career_repository import CareerRepository
from app.repositories.jd_repository import JDEvaluationRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.career.common import SourceRef
from app.schemas.career.lineage import ArtifactInput, ClaimInput, GeneratorManifest
from app.schemas.career.resume import ResumeRenderValidationResult
from app.schemas.jd import BulletDiff, JDExtraction
from app.schemas.resume_v2 import (
    ApplyTailorRequest, ApplyTailorResponse, Bullet, ProjectEntry, ResumeDocumentJSON,
)
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

    def resolve_grounded_evaluation(self, document_id: str, target_id: str, user_id: str) -> str:
        career = CareerApplicationService(self.session, user_id)
        target = career.get_target(target_id)
        if target.status != "active" or target.job_description is None:
            raise ResourceConflictError("Choose an active target with a saved job description.")
        if not self.resumes.get_owned_ready(document_id, user_id):
            raise ResourceNotFoundError("Résumé not found")
        jd_text = career.read_source_content(target.job_description)
        evaluation_id = self.session.scalar(select(JDEvaluation.id).where(
            JDEvaluation.user_id == user_id, JDEvaluation.resume_document_id == document_id,
            JDEvaluation.jd_text == jd_text,
        ).order_by(JDEvaluation.created_at.desc(), JDEvaluation.id.desc()).limit(1))
        if evaluation_id is None:
            raise ResourceNotFoundError("Save a job analysis for this résumé and target first.")
        return evaluation_id

    def preview_grounded(
        self,
        *,
        evaluation_id: str,
        target_id: str,
        resume_version_id: str | None,
        review_id: str,
        user_id: str,
        document_id: str | None = None,
    ) -> GroundedTailorPreview:
        if document_id is not None and self._owned_evaluation(evaluation_id, user_id).resume_document_id != document_id:
            raise ResourceNotFoundError("Job analysis not found")
        mapping, eligible = CareerApplicationService(self.session, user_id).target_jd_context(
            target_id, evaluation_id, resume_version_id=resume_version_id, grounded=True,
        )
        review = ResumeApplicationService(self.session, runtime=self.runtime).get_grounded_review(
            mapping.resume_document_id, review_id, user_id,
        )
        if review.target_id != target_id or review.resume_version_id != resume_version_id:
            raise ResourceConflictError("Saved résumé review does not match the selected target and version")
        if mapping.jd_source is None:
            raise ResourceConflictError("The target requires a saved job description")
        career = CareerApplicationService(self.session, user_id)
        target = career.get_target(target_id)
        bullets, decisions = plan_grounded_bullets(
            mapping, eligible, review.policy, resume_version_id=resume_version_id, seniority=target.seniority,
            recency=EvidenceService(self.session, user_id).decision_times(eligible),
        )
        revisions = {(ref.evidence_id, ref.revision) for bullet in bullets for ref in bullet.plan.evidence_revisions}
        if revisions:
            evidence_ids = {evidence_id for evidence_id, _ in revisions}
            current = set(self.session.execute(EvidenceService(self.session, user_id).eligible_keys(evidence_ids)).tuples())
            if not revisions.issubset(current):
                raise ResourceConflictError("Evidence changed during preview. Refresh and try again.")
        return GroundedTailorPreview(
            resume_version_id=resume_version_id, jd_source=mapping.jd_source, page_limit=review.policy.page_limit,
            bullets=bullets, decisions=decisions,
        )

    def apply_grounded(
        self, *, evaluation_id: str, target_id: str, resume_version_id: str | None, review_id: str,
        selections: dict[str, str], user_id: str, document_id: str | None = None,
        wording_receipt: str | None = None,
    ) -> ApplyTailorResponse:
        evaluation = self._owned_evaluation(evaluation_id, user_id)
        if document_id is not None and evaluation.resume_document_id != document_id:
            raise ResourceNotFoundError("Job analysis not found")
        repo = CareerRepository(self.session, user_id)
        if self.session.scalar(select(User.user_id).where(User.user_id == user_id).with_for_update()) is None:
            raise ResourceNotFoundError("Account not found")
        document = self.session.scalar(select(ResumeDocument).where(
            ResumeDocument.user_id == user_id, ResumeDocument.id == evaluation.resume_document_id,
            ResumeDocument.storage_status == "ready",
        ).with_for_update())
        if document is None:
            raise ResourceNotFoundError("Résumé not found")
        preview = self.preview_grounded(
            evaluation_id=evaluation_id, target_id=target_id, resume_version_id=resume_version_id,
            review_id=review_id, user_id=user_id,
        )
        available = {bullet.plan.plan_id: bullet for bullet in preview.bullets}
        if not selections or selections.keys() - available.keys():
            raise ResourceConflictError("Tailor choices changed. Refresh the preview.")
        validation = None
        if wording_receipt:
            context = [user_id, evaluation_id, target_id, document_id, resume_version_id, review_id]
            try:
                stored_context, validation_data = json.loads(
                    open_private_text(career_cipher(scope="Tailor wording"), wording_receipt),
                )
                validation = ResumeRenderValidationResult.model_validate(validation_data)
            except (ExternalServiceError, ValueError, ValidationError):
                raise ResourceConflictError("Tailor wording receipt is unavailable. Refresh the preview.") from None
            if stored_context != context or validation.plan_hash not in available:
                raise ResourceConflictError("Tailor wording changed. Refresh the preview.")
        selected = []
        for plan_id, bullet in available.items():
            if plan_id not in selections:
                continue
            text = wording_options(bullet).get(selections[plan_id])
            if text is None:
                raise ResourceConflictError("Tailor wording changed. Refresh the preview.")
            selected.append((bullet, text))

        target = self._lock_grounded_target(repo, target_id, preview.jd_source)
        version_id = str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps([
            user_id, target_id, evaluation_id, resume_version_id, review_id, sorted(selections.items()),
        ], separators=(",", ":"))))
        lineage = LineageService(self.session, user_id)
        if prior := self.resumes.get_version(version_id):
            lineage.require_grounded_resume(prior, lock=True)
            response = self._apply_response(prior, ResumeDocumentJSON.model_validate(prior.parsed_json))
            self.session.commit()
            return response

        parent = self.resumes.get_version(resume_version_id) if resume_version_id else document
        tailored = ResumeDocumentJSON.model_validate(parent.parsed_json)
        tailored.projects.append(ProjectEntry(
            name="Selected contributions", bullets=[
                Bullet(id=bullet.plan.plan_id, text=text, raw_text=text) for bullet, text in selected
            ],
        ))
        plan = selected[0][0].plan
        lineage.stage_artifact(ArtifactInput(
            schema_version=1, kind="resume", target_id=target_id,
            generator=GeneratorManifest(
                schema_version=1, application_commit=getenv("RAILWAY_GIT_COMMIT_SHA") or "local",
                generator_version=plan.renderer_version, policy_version=plan.policy_version,
            ),
            claims=[ClaimInput(claim_id=bullet.plan.plan_id, evidence_revisions=bullet.plan.evidence_revisions)
                    for bullet, _ in selected],
        ), artifact_id=version_id)
        requirements = evaluation.extracted_requirements
        version = ResumeVersion(
            id=version_id, resume_document_id=document.id, parent_version_id=resume_version_id,
            change_set={"grounded": {
                "jd_source": preview.jd_source.model_dump(), "page_limit": preview.page_limit,
                "requirements": {bullet.plan.plan_id: [ref.model_dump() for ref in bullet.requirements]
                                 for bullet, _ in selected},
                "decisions": [decision.model_copy(update={"artifact_id": version_id}).model_dump(mode="json")
                              for decision in preview.decisions],
                "plans": [bullet.plan.model_dump(mode="json", exclude_none=True) for bullet, _ in selected],
                "wording": selections,
                "wording_validation": validation.model_dump(mode="json") if validation else None,
            }},
            parsed_json=tailored.model_dump(), jd_evaluation_id=evaluation_id, accepted_at=datetime.now(timezone.utc),
            template_id=resolve_template(requirements.get("country_hint"), requirements.get("primary_role_category")),
            company_name=requirements.get("company_name"), target_role_title=target.role_family,
            seniority=target.seniority, country_hint=requirements.get("country_hint"),
            role_category=requirements.get("primary_role_category"), source_jd_text=evaluation.jd_text,
        )
        self.resumes.add_version(version)
        response = self._apply_response(version, tailored)
        self.session.commit()
        return response

    @staticmethod
    def grounded_wording_receipt(args: dict, user_id: str, validation: ResumeRenderValidationResult) -> str:
        context = [user_id, *(args[key] for key in (
            "evaluation_id", "target_id", "document_id", "resume_version_id", "review_id",
        ))]
        payload = json.dumps([context, validation.model_dump(mode="json")]).encode()
        return career_cipher(scope="Tailor wording").encrypt(payload).decode("ascii")

    @staticmethod
    def _lock_grounded_target(repo: CareerRepository, target_id: str, source: SourceRef):
        # Source before target locks match target update and source deletion.
        if repo.get_source(source, lock=True) is None:
            raise ResourceConflictError("The saved job description is unavailable")
        target = repo.get_target(target_id, lock=True)
        if (target is None or target.status != "active" or
            (target.jd_source_id, target.jd_source_version) != (source.source_id, source.source_version)):
            raise ResourceConflictError("The target changed. Refresh the preview.")
        return target

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
        return self._apply_response(version, tailored)

    def _apply_response(self, version: ResumeVersion, tailored: ResumeDocumentJSON) -> ApplyTailorResponse:
        suggested_template = resolve_template(version.country_hint, version.role_category)
        country_code, role_code = suggested_template.split("-")
        preview_html, warning = _render_preview(
            tailored,
            country=country_code.upper(),
            role=role_code.lower(),
        )
        filename_parts = []
        if tailored.contact.name:
            filename_parts.append(slugify_filename_part(tailored.contact.name))
        if version.company_name:
            filename_parts.append(slugify_filename_part(version.company_name))
        filename_parts.append(role_code)
        return ApplyTailorResponse(
            version_id=version.id,
            preview_html=preview_html,
            company_name=version.company_name,
            target_role_title=version.target_role_title,
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
