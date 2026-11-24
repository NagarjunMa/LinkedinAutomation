"""Internal use cases scoped to a verified application user ID."""
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.application.errors import InvalidOperationError, ResourceConflictError, ResourceNotFoundError
from app.application.evidence_service import EvidenceService
from app.application.target_coverage import project_target_coverage, project_target_resume_coverage
from app.application.target_jd_mapping import project_target_jd_mapping
from app.models.career import CareerSourceRow, CareerTargetRow
from app.repositories.career_repository import CareerRepository
from app.repositories.jd_repository import JDEvaluationRepository
from app.schemas.career.common import SourceRef
from app.schemas.career.evidence import CareerEvidenceItem
from app.schemas.career.jd_mapping import TargetJDMapping
from app.schemas.career.persistence import CareerSourceCreate, CareerTargetInput
from app.schemas.career.sources import CareerSource, CareerTarget
from app.schemas.career.target_coverage import CoverageScope, TargetResumeCoverage, TargetRoleCoverage
from app.schemas.jd import JDExtraction
from app.schemas.resume_v2 import ResumeDocumentJSON


class CareerApplicationService:
    """Call with the authenticated subject and a request-scoped session."""
    def __init__(self, session: Session, user_id: str):
        self.session = session
        self.repo = CareerRepository(session, user_id)

    def add_source(self, data: CareerSourceCreate, previous: SourceRef | None = None) -> CareerSource:
        self._require_owner_for_insert()
        source_id, version = str(uuid4()), 1
        content = data.content
        if data.resume_document_id:
            document = self.repo.ready_resume(data.resume_document_id)
            if document is None:
                raise ResourceNotFoundError("Résumé not found")
            content = document.raw_text

        expiry = data.retention_expires_at
        if previous:
            self._lock_history(previous.source_id)
            snapshot = self._source(previous)
            latest = self.repo.latest_source(previous.source_id)
            if latest.version != previous.source_version:
                raise ResourceConflictError("Source version is no longer current")
            if (snapshot.kind, snapshot.resume_document_id) != (data.kind, data.resume_document_id):
                raise InvalidOperationError("A new version must preserve its source kind and résumé")
            if snapshot.retention_expires_at:
                expiry = min(expiry, snapshot.retention_expires_at) if expiry else snapshot.retention_expires_at
            source_id, version = snapshot.id, snapshot.version + 1

        if not content or not content.strip() or len(content) > 100_000 or "\x00" in content:
            raise InvalidOperationError("Source content is invalid")

        now = datetime.now(timezone.utc)
        if expiry and expiry <= now:
            raise InvalidOperationError("Source retention has already expired")
        row = CareerSourceRow(
            user_id=self.repo.user_id, id=source_id, version=version, kind=data.kind, content=content,
            content_sha256=sha256(content.encode()).hexdigest(), resume_document_id=data.resume_document_id,
            extraction_version=data.extraction_version, created_at=now,
            retention_expires_at=expiry,
        )
        result = _source_view(row)
        self.session.add(row)
        self.session.commit()
        return result

    def get_source(self, source: SourceRef) -> CareerSource:
        return _source_view(self._source(source))

    def read_source_content(self, source: SourceRef) -> str:
        return self.repo.source_content(self._source(source, include_content=True))

    def list_sources(self, *, offset: int = 0, limit: int = 50) -> list[CareerSource]:
        _validate_page(offset, limit)
        return [_source_view(row) for row in self.repo.list_sources(offset, limit)]

    def delete_source(self, source_id: str) -> None:
        self._lock_history(source_id)
        self.repo.delete_source_history(source_id)
        self.session.commit()

    def create_target(self, data: CareerTargetInput) -> CareerTarget:
        self._require_owner_for_insert()
        self._check_jd(data.job_description)
        row = CareerTargetRow(user_id=self.repo.user_id, id=str(uuid4()), status="active")
        _apply_target(row, data)
        self.session.add(row)
        return self._save_target(row)

    def get_target(self, target_id: str) -> CareerTarget:
        return _target_view(self._target(target_id))

    def target_coverage(
        self, target_id: str, *, explain: bool = False, required_scope: CoverageScope | None = None,
    ) -> TargetRoleCoverage:
        target = self._coverage_target(target_id)
        return project_target_coverage(
            target, self._coverage_evidence(target), explain=explain, required_scope=required_scope,
        )

    def target_resume_coverage(
        self, target_id: str, resume_document_id: str, *,
        explain: bool = False, required_scope: CoverageScope | None = None,
    ) -> TargetResumeCoverage:
        target = self._coverage_target(target_id)
        document = self.repo.ready_resume(resume_document_id)
        if document is None:
            raise ResourceNotFoundError("Résumé not found")
        resume = _parsed_resume(document.parsed_json)
        return project_target_resume_coverage(
            target, self._coverage_evidence(target), resume_document_id, resume,
            explain=explain, required_scope=required_scope,
        )

    def target_jd_mapping(self, target_id: str, evaluation_id: str) -> TargetJDMapping:
        target = self._coverage_target(target_id)
        evaluation = JDEvaluationRepository(self.session).get_owned(evaluation_id, self.repo.user_id)
        if evaluation is None:
            raise ResourceNotFoundError("Job analysis not found")
        document = self.repo.ready_resume(evaluation.resume_document_id)
        if document is None:
            raise ResourceNotFoundError("Résumé not found")
        jd_digest = sha256(evaluation.jd_text.encode()).hexdigest()
        if target.job_description and self.get_source(target.job_description).content_sha256 != jd_digest:
            raise ResourceConflictError("Job analysis does not match the target's saved description")
        try:
            extraction = JDExtraction.model_validate(evaluation.extracted_requirements)
        except ValidationError:
            raise InvalidOperationError("Saved job analysis requirements are invalid") from None
        resume = _parsed_resume(document.parsed_json)
        return project_target_jd_mapping(
            target, EvidenceService(self.session, self.repo.user_id).list_eligible(),
            evaluation_id=evaluation.id, jd_text=evaluation.jd_text, jd_text_sha256=jd_digest,
            extraction=extraction, resume_document_id=document.id, resume=resume,
        )

    def _coverage_target(self, target_id: str) -> CareerTarget:
        target = self.get_target(target_id)
        if target.status != "active":
            raise ResourceNotFoundError("Active target not found")
        return target

    def _coverage_evidence(self, target: CareerTarget) -> list[CareerEvidenceItem]:
        return EvidenceService(self.session, self.repo.user_id).list_eligible() if target.desired_work else []

    def list_targets(self, *, offset: int = 0, limit: int = 50, active_only: bool = False) -> list[CareerTarget]:
        _validate_page(offset, limit)
        return [_target_view(row) for row in self.repo.list_targets(offset, limit, active_only=active_only)]

    def update_target(self, target_id: str, data: CareerTargetInput) -> CareerTarget:
        self._target(target_id)
        # Lock the source before the target, matching the order of deletion cascades.
        self._check_jd(data.job_description)
        row = self._target(target_id, lock=True)
        if row.status == "archived":
            raise ResourceConflictError("Archived targets cannot be edited")
        _apply_target(row, data)
        return self._save_target(row)

    def archive_target(self, target_id: str) -> CareerTarget:
        row = self._target(target_id, lock=True)
        row.status = "archived"
        return self._save_target(row)

    def delete_target(self, target_id: str) -> None:
        self.session.delete(self._target(target_id, lock=True))
        self.session.commit()

    def _require_owner_for_insert(self) -> None:
        if not self.repo.lock_owner_for_insert():
            raise ResourceNotFoundError("Account not found")

    def _save_target(self, row: CareerTargetRow) -> CareerTarget:
        result = _target_view(row)
        self.session.commit()
        return result

    def _source(self, source: SourceRef, *, lock=False, include_content=False) -> CareerSourceRow:
        row = self.repo.get_source(source, lock=lock, include_content=include_content)
        if row is None:
            raise ResourceNotFoundError("Source not found")
        return row

    def _lock_history(self, source_id: str) -> None:
        if self.repo.lock_source_history(source_id) is None:
            raise ResourceNotFoundError("Source not found")

    def _target(self, target_id: str, *, lock=False) -> CareerTargetRow:
        row = self.repo.get_target(target_id, lock=lock)
        if row is None:
            raise ResourceNotFoundError("Target not found")
        return row

    def _check_jd(self, source: SourceRef | None) -> None:
        if source and self._source(source, lock=True).kind != "job_description":
            raise ResourceNotFoundError("Job description not found")


def _parsed_resume(value: object) -> ResumeDocumentJSON | None:
    try:
        return ResumeDocumentJSON.model_validate(value)
    except ValidationError:
        return None


def _apply_target(row: CareerTargetRow, data: CareerTargetInput) -> None:
    for key, value in data.model_dump(exclude={"job_description"}).items():
        setattr(row, key, value)
    jd = data.job_description
    row.jd_user_id = row.user_id if jd else None
    row.jd_source_id = jd.source_id if jd else None
    row.jd_source_version = jd.source_version if jd else None
    row.jd_source_kind = "job_description" if jd else None


def _validate_page(offset: int, limit: int) -> None:
    if offset < 0 or not 1 <= limit <= 100:
        raise InvalidOperationError("Invalid page")


def _source_view(row: CareerSourceRow) -> CareerSource:
    return CareerSource(
        schema_version=1, source=SourceRef(source_id=row.id, source_version=row.version), owner_id=row.user_id,
        kind=row.kind, content_sha256=row.content_sha256, resume_document_id=row.resume_document_id,
        extraction_version=row.extraction_version, created_at=row.created_at, retention_expires_at=row.retention_expires_at,
    )


def _target_view(row: CareerTargetRow) -> CareerTarget:
    jd = SourceRef(source_id=row.jd_source_id, source_version=row.jd_source_version) if row.jd_source_id else None
    return CareerTarget(
        schema_version=1, target_id=row.id, owner_id=row.user_id, role_family=row.role_family,
        seniority=row.seniority, location=row.location, desired_work=row.desired_work,
        exclusions=row.exclusions, status=row.status, job_description=jd,
    )
