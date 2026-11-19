"""Owner-scoped LinkedIn PDF snapshots and retryable Storage lifecycle."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
from threading import BoundedSemaphore
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.application.career_encryption import career_cipher
from app.application.errors import ExternalServiceError, ResourceConflictError, ResourceNotFoundError
from app.application.evidence_service import EvidenceService
from app.models.career import CareerSourceRow, LinkedInPdfUploadRow
from app.repositories.career_repository import CareerRepository, open_linkedin_document
from app.schemas.career.common import SourceRef
from app.schemas.career.evidence import EvidenceProposal
from app.schemas.career.sources import LINKEDIN_PDF_EXTRACTION_VERSION, LinkedInDocument, LinkedInUpload, LinkedInUploadSummary
from app.services.linkedin_pdf import CLAIM, parse_profile_pages
from app.services.storage.exceptions import StorageError
from app.services.storage.supabase_storage import StorageClient


# Leave shared database connections available while synchronous Storage mutations run.
_STORAGE_MUTATIONS = BoundedSemaphore(4)


@contextmanager
def _storage_mutation_slot():
    if not _STORAGE_MUTATIONS.acquire(blocking=False):
        raise ExternalServiceError("LinkedIn PDF Storage is busy")
    try:
        yield
    finally:
        _STORAGE_MUTATIONS.release()


class LinkedInPdfService:
    def __init__(self, db: Session, owner: str, storage: StorageClient):
        self.db = db
        self.owner = owner
        self.storage = storage
        self.sources = CareerRepository(db, owner)

    def list(self, offset: int, limit: int) -> list[LinkedInUploadSummary]:
        return [_summary(source, upload) for source, upload in self.db.execute(
            self._uploads().order_by(CareerSourceRow.created_at.desc(), LinkedInPdfUploadRow.source_id,
                                     LinkedInPdfUploadRow.version.desc()).offset(offset).limit(limit)
        )]

    def get(self, ref: SourceRef) -> LinkedInUpload:
        source, upload = self._ready(ref)
        return LinkedInUpload(**_summary(source, upload).model_dump(), document=open_linkedin_document(upload))

    def download(self, ref: SourceRef) -> bytes:
        with self.db.begin():
            _, upload = self._ready(ref)
            path, expected_digest = self._object_path(upload), upload.pdf_sha256
        try:
            content = self.storage.download(path)
        except StorageError:
            raise ExternalServiceError("LinkedIn PDF could not be retrieved") from None
        if sha256(content).hexdigest() != expected_digest:
            raise ExternalServiceError("Stored PDF could not be verified")
        return content

    def check_append(self, previous: SourceRef) -> None:
        with self.db.begin():
            self._require_current_version(previous)

    def _require_current_version(self, previous: SourceRef) -> None:
        self._ready(previous)
        latest = self.sources.latest_source(previous.source_id)
        if latest is None or latest.version != previous.source_version:
            raise ResourceConflictError("LinkedIn PDF version is no longer current")

    def add(self, content: bytes, pages: list[str], previous: SourceRef | None = None,
            *, sidebar_lines: list[int | None] | None = None) -> LinkedInUpload:
        with _storage_mutation_slot():
            return self._add(content, pages, previous, sidebar_lines=sidebar_lines)

    def _add(self, content: bytes, pages: list[str], previous: SourceRef | None, *, sidebar_lines: list[int | None] | None) -> LinkedInUpload:
        self._lock_owner()
        ref = SourceRef(source_id=str(uuid4()), source_version=1)
        if previous is not None:
            self._lock(previous.source_id)
            self._require_current_version(previous)
            ref = SourceRef(source_id=previous.source_id, source_version=previous.source_version + 1)

        document = parse_profile_pages(pages, ref, sidebar_lines=sidebar_lines)
        cipher = career_cipher(scope="LinkedIn PDF")
        source = CareerSourceRow(
            user_id=self.owner, id=ref.source_id, version=ref.source_version, kind="linkedin_profile_pdf",
            content="", content_sha256=sha256(document.raw_text.encode()).hexdigest(),
            extraction_version=LINKEDIN_PDF_EXTRACTION_VERSION, created_at=datetime.now(timezone.utc),
        )
        upload = LinkedInPdfUploadRow(
            user_id=self.owner, source_id=ref.source_id, version=ref.source_version, object_id=str(uuid4()),
            pdf_sha256=sha256(content).hexdigest(), state="pending",
            document_ciphertext=cipher.encrypt(document.model_dump_json().encode()).decode("ascii"),
        )
        self.db.add(source)
        self.db.flush()
        self.db.add(upload)
        self.db.commit()
        self._lock_owner()
        self._lock(ref.source_id, nowait=False)
        source, upload = self._version(ref)
        if upload.state != "pending":
            raise ResourceConflictError("LinkedIn PDF upload is no longer pending")
        try:
            path = self.storage.upload(self.owner, f"linkedin-{upload.object_id}", content, "profile.pdf")
        except StorageError:
            # An ambiguous result keeps the object reservation available for owner cleanup.
            raise ExternalServiceError("LinkedIn PDF could not be uploaded") from None
        if path != self._object_path(upload):
            raise ExternalServiceError("LinkedIn PDF Storage path could not be verified")
        upload.state = "ready"
        self.db.flush()
        self._propose(document)
        result = LinkedInUpload(**_summary(source, upload).model_dump(), document=document)
        self.db.commit()
        return result

    def delete(self, source_id: str) -> None:
        with _storage_mutation_slot():
            self._delete(source_id)

    def _delete(self, source_id: str) -> None:
        self._lock_owner()
        self._lock(source_id)
        for _, upload in self._history(source_id):
            if upload.state == "pending":
                upload.state = "canceling"
            elif upload.state == "ready":
                upload.state = "deleting"
        self.db.commit()

        self._lock_owner()
        self._lock(source_id, nowait=False)
        rows = self._history(source_id)
        # A timed-out upload may finish after a remove call finds no object.
        for _, upload in sorted(rows, key=lambda row: row[1].state == "canceling"):
            try:
                removed = self.storage.delete(self._object_path(upload))
            except StorageError:
                raise ExternalServiceError("LinkedIn PDF deletion can be retried") from None
            if upload.state == "canceling" and not removed:
                raise ExternalServiceError("LinkedIn PDF cleanup is pending; deletion can be retried")
        for _, upload in rows:
            self.db.delete(upload)
        self.db.flush()
        self.db.execute(delete(CareerSourceRow).where(
            CareerSourceRow.user_id == self.owner, CareerSourceRow.id == source_id,
            CareerSourceRow.extraction_version == LINKEDIN_PDF_EXTRACTION_VERSION,
        ))
        self.db.commit()

    def _uploads(self):
        return select(CareerSourceRow, LinkedInPdfUploadRow).join(LinkedInPdfUploadRow).where(
            LinkedInPdfUploadRow.user_id == self.owner,
        )

    def _history(self, source_id: str):
        return self.db.execute(self._uploads().where(LinkedInPdfUploadRow.source_id == source_id)).all()

    def _version(self, ref: SourceRef):
        row = self.db.execute(self._uploads().where(
            LinkedInPdfUploadRow.source_id == ref.source_id, LinkedInPdfUploadRow.version == ref.source_version,
        )).one_or_none()
        if row is None:
            raise ResourceNotFoundError("LinkedIn PDF not found")
        return row

    def _ready(self, ref: SourceRef):
        source, upload = self._version(ref)
        if upload.state != "ready" or self.sources.get_source(ref) is None:
            raise ResourceNotFoundError("LinkedIn PDF not found")
        return source, upload

    def _lock_owner(self) -> None:
        if not self.sources.lock_owner_for_insert():
            raise ResourceNotFoundError("LinkedIn PDF not found")

    def _lock(self, source_id: str, *, nowait: bool = True) -> None:
        # New mutations fail fast. An admitted mutation can finish its durable continuation
        # under the Storage slot limit after the reservation or delete intent is committed.
        anchor = self._uploads().where(
            LinkedInPdfUploadRow.source_id == source_id, LinkedInPdfUploadRow.version == 1,
            CareerSourceRow.extraction_version == LINKEDIN_PDF_EXTRACTION_VERSION,
        ).with_for_update(nowait=nowait, key_share=True, of=LinkedInPdfUploadRow)
        try:
            row = self.db.execute(anchor).one_or_none()
        except DBAPIError as exc:
            if getattr(exc.orig, "pgcode", None) != "55P03":  # PostgreSQL lock_not_available
                raise
            raise ResourceConflictError("LinkedIn PDF history is busy") from None
        if row is None:
            raise ResourceNotFoundError("LinkedIn PDF not found")

    def _object_path(self, upload: LinkedInPdfUploadRow) -> str:
        return f"{self.owner}/linkedin-{upload.object_id}.pdf"

    def _propose(self, document: LinkedInDocument) -> None:
        ledger = EvidenceService(self.db, self.owner)
        proposed = 0
        for section in document.sections:
            if section.name not in {"experience", "projects"} or not CLAIM.match(section.text):
                continue
            first = document.raw_text.find(section.text)
            if first < 0 or document.raw_text.find(section.text, first + 1) >= 0:
                continue
            ledger.stage_proposal(EvidenceProposal(
                claim=section.text, category="action", ownership="unknown", sources=[{
                    **document.source.model_dump(), "relationship": "supports", "locator": section.locator,
                    "excerpt": section.text, "extraction": "parser",
                }],
            ))
            proposed += 1
            if proposed == 12:
                break


def _summary(source: CareerSourceRow, upload: LinkedInPdfUploadRow) -> LinkedInUploadSummary:
    return LinkedInUploadSummary(
        source=SourceRef(source_id=source.id, source_version=source.version),
        pdf_sha256=upload.pdf_sha256, created_at=source.created_at, state=upload.state,
    )
