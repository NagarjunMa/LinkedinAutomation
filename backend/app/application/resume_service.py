"""Application orchestration for resume upload, evaluation, and versioning."""

from __future__ import annotations

import uuid
from zipfile import BadZipFile

from docx.opc.exceptions import PackageNotFoundError
from fastapi import UploadFile
from lxml.etree import XMLSyntaxError
from pdfplumber.utils.exceptions import PdfminerException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.application.career_encryption import career_cipher, open_private_text
from app.application.career_service import CareerApplicationService
from app.application.errors import (
    ExternalServiceError,
    InvalidOperationError,
    OperationRejectedError,
    ResourceNotFoundError,
)
from app.application.credits import paid_operation
from app.application.evidence_service import EvidenceService
from app.application.resume_review import project_resume_review
from app.core.openai_client import ModelRuntime, get_model_runtime
from app.models.resume_document import ResumeVersion
from app.models.resume_evaluation_v2 import ResumeEvaluationV2
from app.repositories.resume_repository import ResumeRepository
from app.schemas.career.resume import GroundedResumeReview
from app.schemas.resume_v2 import BulletFlag, ChangeItem, ResumeDocumentJSON
from app.services.resume.ats_simulator import ATSResult, simulate_ats
from app.services.resume.changes import apply_changes, find_bullet_text
from app.services.resume.evaluator import evaluate_resume
from app.services.resume.file_security import parse_resume_with_timeout, read_resume_upload
from app.services.resume.hallucination_guard import HallucinationError
from app.services.resume.rewriter import rewrite_bullet
from app.services.resume.upload_workflow import (
    ResumeStorageWorkflowError,
    create_resume_document,
    delete_resume_document,
)
from app.services.storage.supabase_storage import get_storage


class ResumeApplicationService:
    def __init__(self, session: Session, *, runtime: ModelRuntime | None = None):
        self.session = session
        self.resumes = ResumeRepository(session)
        self.runtime = runtime or get_model_runtime()

    async def upload(self, file: UploadFile, user_id: str) -> dict:
        uploaded = await read_resume_upload(file)
        document = await parse_resume_with_timeout(uploaded.content, uploaded.filename)
        try:
            row = create_resume_document(
                db=self.session,
                storage=get_storage(),
                user_id=user_id,
                filename=uploaded.filename,
                extension=uploaded.extension,
                content=uploaded.content,
                document=document,
            )
        except ResumeStorageWorkflowError as exc:
            raise ExternalServiceError(str(exc)) from exc
        return {"resume_document_id": row.id, **document.model_dump()}

    def list(self, user_id: str) -> dict:
        documents = self.resumes.list_ready(user_id)
        evaluations = self.resumes.latest_evaluations(
            user_id,
            [document.id for document in documents],
        )
        rows = [
            _resume_list_item(
                document,
                evaluation=evaluations.get(document.id),
                is_primary=index == 0,
            )
            for index, document in enumerate(documents)
        ]
        return {"resumes": rows, "total_count": len(rows), "totalCount": len(rows)}

    def get(self, resume_document_id: str, user_id: str, *, grounded_evaluation_id: str | None = None) -> dict:
        document = self._owned_ready(resume_document_id, user_id)
        evaluation = self.resumes.latest_evaluation(resume_document_id, user_id)
        payload = {
            "resume": _resume_list_item(document, evaluation=evaluation),
            "evaluation": _evaluation_payload(evaluation),
        }
        grounded = self.resumes.latest_evaluation(
            resume_document_id, user_id, grounded_only=True, evaluation_id=grounded_evaluation_id,
        )
        if grounded_evaluation_id and not grounded:
            raise ResourceNotFoundError("Saved résumé review not found")
        if grounded and (review := self._saved_review(grounded, user_id)):
            payload["grounded_review"] = review.model_dump()
            payload["grounded_evaluation_id"] = grounded.id
        return payload

    def _saved_review(self, evaluation: ResumeEvaluationV2 | None, user_id: str) -> GroundedResumeReview | None:
        if not evaluation or not evaluation.grounded_review_ciphertext:
            return None
        try:
            cipher = career_cipher(scope="Résumé review")
            review = GroundedResumeReview.model_validate_json(
                open_private_text(cipher, evaluation.grounded_review_ciphertext),
            )
        except (ExternalServiceError, ValidationError):
            return None
        evidence_ids = {ref.evidence_id for finding in review.findings for ref in finding.evidence_revisions}
        if not evidence_ids:
            return review
        eligible = set(self.session.execute(EvidenceService(self.session, user_id).eligible_keys(evidence_ids)).tuples())
        findings = [
            finding for finding in review.findings
            if all((ref.evidence_id, ref.revision) in eligible for ref in finding.evidence_revisions)
        ]
        if len(findings) == len(review.findings):
            return review
        mode = "evidence_grounded" if any(finding.evidence_revisions for finding in findings) else "document_only"
        return review.model_copy(update={"findings": findings, "mode": mode, "needs_refresh": True})

    def delete(self, resume_document_id: str, user_id: str) -> None:
        document = self.resumes.get_owned(resume_document_id, user_id)
        if not document:
            raise ResourceNotFoundError("Not found")
        try:
            delete_resume_document(
                db=self.session,
                storage=get_storage(),
                row=document,
                user_id=user_id,
            )
        except ResumeStorageWorkflowError as exc:
            raise ExternalServiceError(str(exc)) from exc

    async def evaluate(
        self, resume_document_id: str, target_role: str | None, user_id: str, version_id: str | None = None,
        *, target_id: str | None = None, grounded_review: bool = False,
    ) -> dict:
        document = self._owned_ready(resume_document_id, user_id)
        resume = self._version_content(document, version_id)
        target = CareerApplicationService(self.session, user_id).get_target(target_id) if target_id else None
        if target and target.status != "active":
            raise ResourceNotFoundError("Active target not found")
        role = target.role_family if target else target_role
        if role is None:
            raise InvalidOperationError("A target role is required")
        cipher = career_cipher(scope="Résumé review") if grounded_review or target else None
        with paid_operation(self.session, user_id, amount=1, reason="evaluate"):
            report = await evaluate_resume(
                resume, target_role=role, user_id=user_id, runtime=self.runtime,
            )
            storage = get_storage()
            content = storage.download(document.storage_path or document.file_path)
            try:
                ats = simulate_ats(content, filename=document.original_filename)
            except (BadZipFile, PackageNotFoundError, PdfminerException, XMLSyntaxError, ValueError):
                if cipher is None:
                    raise
                ats = ATSResult(parseability_score=0, raw_text="", format_issues=[])
            review = None
            if cipher is not None:
                evidence = EvidenceService(self.session, user_id).list_eligible() if target and target.desired_work else []
                review = project_resume_review(document.id, resume, version_id, ats, target, evidence, target_role=role)
            # Version feedback describes edited text. Document checks still describe the uploaded file.
            document_issues = ats.format_issues if version_id else report.format_issues + ats.format_issues
            format_issues = [item.model_dump() for item in document_issues]
            row = ResumeEvaluationV2(
                id=str(uuid.uuid4()),
                resume_document_id=resume_document_id,
                user_id=user_id,
                overall_score=report.overall_score,
                bullet_flags=[flag.model_dump() for flag in report.bullet_flags],
                format_issues=format_issues,
                readiness_label=report.readiness_label,
                score_breakdown=report.score_breakdown.model_dump(),
                score_explanation=[item.model_dump() for item in report.score_explanation],
                top_actions_before_applying=report.top_actions_before_applying,
                parser_confidence=report.parser_confidence,
                summary_critique=report.summary_critique,
                grounded_review_ciphertext=cipher.encrypt(review.model_dump_json().encode()).decode()
                if cipher and review else None,
                ats_parseability=ats.parseability_score,
                ats_raw_text=ats.raw_text,
                model_version=self.runtime.manifests["evaluator"].model_snapshot,
            )
            self.resumes.add_evaluation(row)
            payload = {
                "evaluation_id": row.id,
                "overall_score": report.overall_score,
                "readiness_label": report.readiness_label,
                "score_breakdown": report.score_breakdown.model_dump(),
                "score_explanation": [item.model_dump() for item in report.score_explanation],
                "top_actions_before_applying": report.top_actions_before_applying,
                "parser_confidence": report.parser_confidence,
                "bullet_flags": [flag.model_dump() for flag in report.bullet_flags],
                "format_issues": format_issues,
                "summary_critique": report.summary_critique,
                "ats_parseability": ats.parseability_score,
                "ats_raw_text": ats.raw_text,
            }
            if review:
                payload["grounded_review"] = review.model_dump()
            self.session.commit()
        return payload

    async def rewrite(
        self,
        *,
        resume_document_id: str,
        bullet_id: str,
        target_role: str,
        country: str,
        jd_context: str | None,
        user_id: str,
        version_id: str | None = None,
        findings: list[BulletFlag] | None = None,
    ) -> dict:
        document = self._owned_ready(resume_document_id, user_id)
        resume = self._version_content(document, version_id)
        original = find_bullet_text(resume, bullet_id)
        if original is None:
            raise ResourceNotFoundError("Bullet not found")
        if any(finding.bullet_id != bullet_id for finding in findings or []):
            raise OperationRejectedError("Findings must refer to the selected bullet")
        try:
            result = await rewrite_bullet(
                original=original,
                target_role=target_role,
                country=country,
                jd_context=jd_context,
                user_id=user_id,
                runtime=self.runtime,
                findings=findings,
            )
        except HallucinationError as exc:
            raise OperationRejectedError(f"Rewrite rejected: {exc}") from exc
        return result.model_dump()

    def create_version(
        self,
        *,
        resume_document_id: str,
        parent_version_id: str | None,
        change_set: list[ChangeItem],
        user_id: str,
    ) -> dict:
        document = self._owned_ready(resume_document_id, user_id)
        base = self._version_content(document, parent_version_id)

        new_document = apply_changes(base, change_set)
        version = ResumeVersion(
            id=str(uuid.uuid4()),
            resume_document_id=resume_document_id,
            parent_version_id=parent_version_id,
            change_set=[change.model_dump() for change in change_set],
            parsed_json=new_document.model_dump(),
        )
        self.resumes.add_version(version)
        self.session.commit()
        return {"version_id": version.id}

    def _version_content(self, document, version_id: str | None) -> ResumeDocumentJSON:
        if not version_id:
            return ResumeDocumentJSON.model_validate(document.parsed_json)
        version = self.resumes.get_version(version_id)
        if not version or version.resume_document_id != document.id:
            raise ResourceNotFoundError("Version not found")
        resume = ResumeDocumentJSON.model_validate(version.parsed_json)
        # Original PDF text must not override edits in a saved version's model input.
        resume.raw_text = ""
        for entry in [*resume.experience, *resume.projects]:
            for bullet in entry.bullets:
                bullet.raw_text = bullet.text
        return resume

    def _owned_ready(self, resume_document_id: str, user_id: str):
        document = self.resumes.get_owned_ready(resume_document_id, user_id)
        if not document:
            raise ResourceNotFoundError("Not found")
        return document


def _resume_list_item(document, evaluation=None, is_primary: bool = False) -> dict:
    created = document.created_at.isoformat() if document.created_at else None
    return {
        "id": document.id,
        "resume_document_id": document.id,
        "filename": document.original_filename,
        "original_filename": document.original_filename,
        "file_size": 0,
        "file_type": document.file_type,
        "uploaded_at": created,
        "evaluation_status": "completed" if evaluation else "pending",
        "is_primary": is_primary,
        "evaluation_result": _evaluation_payload(evaluation),
    }


def _evaluation_payload(evaluation) -> dict | None:
    if not evaluation:
        return None
    score_breakdown = evaluation.score_breakdown or {
        "content_quality": evaluation.overall_score,
        "role_fit": evaluation.overall_score,
        "evidence_strength": evaluation.overall_score,
        "recruiter_readability": evaluation.overall_score,
    }
    score_explanation = evaluation.score_explanation or []
    top_actions = evaluation.top_actions_before_applying or []
    return {
        "id": evaluation.id,
        "resume_id": evaluation.resume_document_id,
        "resume_document_id": evaluation.resume_document_id,
        "overall_score": evaluation.overall_score,
        "readiness_label": evaluation.readiness_label or "needs_work",
        "score_breakdown": score_breakdown,
        "score_explanation": score_explanation,
        "top_actions_before_applying": top_actions,
        "parser_confidence": evaluation.parser_confidence or "medium",
        "bullet_flags": evaluation.bullet_flags or [],
        "format_issues": evaluation.format_issues or [],
        "ats_score": evaluation.ats_parseability,
        "ats_compliance_score": evaluation.ats_parseability,
        "content_quality_score": score_breakdown.get("content_quality", evaluation.overall_score),
        "experience_points_score": score_breakdown.get("evidence_strength", evaluation.overall_score),
        "job_relevance_score": score_breakdown.get("role_fit", evaluation.overall_score),
        "quality_checks_score": score_breakdown.get("recruiter_readability", evaluation.overall_score),
        "strengths": [
            item.get("reason", "")
            for item in score_explanation
            if item.get("score", 0) >= 80 and item.get("reason")
        ][:3],
        "improvements": top_actions,
        "ats_compatibility": "good" if evaluation.ats_parseability >= 80 else "fair",
        "detailed_feedback": evaluation.summary_critique,
        "keyword_analysis": {
            "relevant": [],
            "missing": [],
            "score": score_breakdown.get("role_fit", 0),
        },
        "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
    }
