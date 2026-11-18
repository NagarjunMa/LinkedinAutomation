"""Owner-scoped ledger and the eligibility boundary for downstream claims."""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from cryptography.fernet import Fernet
from pydantic import ValidationError
from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import Session

from app.application.career_encryption import career_cipher, open_private_text
from app.application.errors import ExternalServiceError, InvalidOperationError, ResourceConflictError, ResourceNotFoundError
from app.models.career import CareerSourceRow
from app.models.career_evidence import EvidenceDecisionRow as Decision, EvidenceRow as Item, EvidenceSourceRow as Link
from app.models.resume_document import ResumeDocument
from app.repositories.career_repository import CareerRepository
from app.schemas.career.common import SourceRef
from app.schemas.career.evidence import (
    CareerEvidenceDecision, CareerEvidenceItem, EvidenceDecisionInput, EvidenceHistory, EvidenceLifecycle, EvidenceMeasurement,
    EvidenceProposal, EvidenceRevisionRef, EvidenceSourceLink,
)


class EvidenceService:
    def __init__(self, db: Session, owner: str):
        self.db = db
        self.owner = owner
        self.career = CareerRepository(db, owner)

    def propose(self, proposal: EvidenceProposal) -> CareerEvidenceItem:
        self._lock_owner()
        self._lock_sources(proposal.sources)
        sources = []
        seen_spans = set()
        for link in proposal.sources:
            excerpt = link.excerpt
            if excerpt is None:
                raise InvalidOperationError("Evidence proposal requires a verifiable excerpt")
            source = self.career.get_source(link, include_content=True)
            start = source.content.find(excerpt) if source is not None else -1
            if start < 0 or source.content.find(excerpt, start + 1) >= 0:
                raise InvalidOperationError("Excerpt must occur exactly once in the source")
            locator = f"chars:{start}-{start + len(excerpt)}"
            span = (link.source_id, link.source_version, locator)
            if span in seen_spans:
                raise InvalidOperationError("Evidence requires distinct source spans")
            seen_spans.add(span)
            sources.append(link.model_copy(update={
                "locator": locator,
                "excerpt": None,
                "excerpt_sha256": sha256(excerpt.encode()).hexdigest(),
            }))
        item = CareerEvidenceItem(
            **proposal.model_dump(exclude={"sources"}), schema_version=1, owner_id=self.owner,
            evidence_id=str(uuid4()), revision=1, support="candidate_statement", sources=sources,
            lifecycle="contradicted" if any(link.relationship == "contradicts" for link in sources) else "proposed",
        )
        self._insert(item, career_cipher(scope="Career evidence"))
        self.db.commit()
        return item

    def list(self, *, offset: int = 0, limit: int = 50) -> list[CareerEvidenceItem]:
        rows = self.db.scalars(self._current().where(self._has_sources()).order_by(Item.evidence_id)
                               .offset(offset).limit(limit)).all()
        if not rows:
            return []
        cipher = career_cipher(scope="Career evidence")
        return [self._view(row, cipher) for row in rows]

    def get(self, evidence_id: str) -> CareerEvidenceItem:
        return self._view(self._latest(evidence_id), career_cipher(scope="Career evidence"))

    def history(self, evidence_id: str, *, offset: int = 0, limit: int = 50) -> EvidenceHistory:
        self._latest(evidence_id)
        cipher = career_cipher(scope="Career evidence")
        rows = self.db.execute(select(Item, Decision).outerjoin(Decision, (
            (Decision.user_id == Item.user_id) & (Decision.evidence_id == Item.evidence_id)
            & (Decision.resulting_revision == Item.revision)
        )).where(
            Item.user_id == self.owner, Item.evidence_id == evidence_id, self._has_sources(),
        ).order_by(Item.revision).offset(offset).limit(limit)).all()
        return EvidenceHistory(
            revisions=[self._view(item, cipher) for item, _ in rows],
            decisions=[CareerEvidenceDecision(
                schema_version=1, evidence=EvidenceRevisionRef(evidence_id=evidence_id, revision=d.resulting_revision - 1),
                actor_id=self.owner, action=d.action, decided_at=d.decided_at, resulting_revision=d.resulting_revision,
                reason=open_private_text(cipher, d.reason_ciphertext) if d.reason_ciphertext else None,
            ) for _, d in rows if d is not None],
        )

    def eligible(self, reference: EvidenceRevisionRef) -> CareerEvidenceItem | None:
        row = self.db.scalar(self._eligible_rows().where(
            Item.evidence_id == reference.evidence_id, Item.revision == reference.revision,
        ))
        return self._view(row, career_cipher(scope="Career evidence")) if row else None

    def eligible_keys(self, evidence_ids):
        return self._eligible_rows().where(Item.evidence_id.in_(evidence_ids)).with_only_columns(
            Item.evidence_id, Item.revision,
        )

    def lock_eligible_revisions(self, keys: set[tuple[str, int]], *, extra_sources: Sequence[SourceRef] = ()) -> None:
        # The caller locks the owner first. Preserve the ledger's source-before-anchor order.
        source_rows = self.db.execute(select(Link.source_id, Link.source_version).where(
            Link.user_id == self.owner, tuple_(Link.evidence_id, Link.revision).in_(keys),
        ).distinct())
        try:
            self._lock_sources([SourceRef(source_id=id_, source_version=version) for id_, version in source_rows]
                               + list(extra_sources))
        except ResourceNotFoundError:
            raise InvalidOperationError("Artifact evidence or source is unavailable") from None
        ids = {id_ for id_, _ in keys}
        self.db.execute(select(Item.evidence_id).where(
            Item.user_id == self.owner, Item.revision == 1, Item.evidence_id.in_(ids),
        ).order_by(Item.evidence_id).with_for_update(read=True)).all()
        eligible = set(self.db.execute(self.eligible_keys(ids)).tuples())
        if not keys.issubset(eligible):
            raise InvalidOperationError("Artifact evidence is not eligible")

    def decide(self, evidence_id: str, data: EvidenceDecisionInput) -> CareerEvidenceItem:
        self._lock_owner()
        cipher = career_cipher(scope="Career evidence")
        old = self._view(self._latest(evidence_id), cipher)
        if old.revision != data.revision:
            raise ResourceConflictError("Evidence revision is no longer current")
        self._lock_sources(old.sources)
        anchor = self.db.scalar(select(Item.revision).where(
            Item.user_id == self.owner, Item.evidence_id == evidence_id, Item.revision == 1,
        ).with_for_update())
        if anchor is None:
            raise ResourceNotFoundError("Evidence not found")
        row = self._latest(evidence_id)
        if row.revision != data.revision:
            raise ResourceConflictError("Evidence revision is no longer current")
        lifecycle, sources = _decision_state(old, data)
        changes = data.edit_values() if data.action == "edit" else {}
        if "claim" in changes and changes["claim"] != old.claim:
            changes.setdefault("measurement", None)
        item = CareerEvidenceItem.model_validate({
            **old.model_dump(), **changes, "revision": old.revision + 1, "supersedes_revision": old.revision,
            "lifecycle": lifecycle, "sources": sources,
            "is_private": old.is_private or lifecycle == "private",
        })
        self._insert(item, cipher)
        self.db.add(Decision(
            user_id=self.owner, evidence_id=evidence_id, resulting_revision=item.revision,
            action=data.action, decided_at=datetime.now(timezone.utc),
            reason_ciphertext=cipher.encrypt(data.reason.encode()).decode("ascii") if data.reason else None,
        ))
        self.db.commit()
        return item

    def _lock_owner(self) -> None:
        if not self.career.lock_owner_for_insert():
            raise ResourceNotFoundError("Evidence not found")

    def _lock_sources(self, links: Sequence[SourceRef]) -> None:
        refs = {(link.source_id, link.source_version) for link in links}
        cols = CareerSourceRow.id, CareerSourceRow.version
        resumes = select(CareerSourceRow.resume_document_id).where(
            CareerSourceRow.user_id == self.owner, tuple_(*cols).in_(refs),
            CareerSourceRow.resume_document_id.is_not(None),
        )
        # Résumé deletion marks the document unavailable before it removes source rows.
        self.db.execute(select(ResumeDocument.id).where(
            ResumeDocument.user_id == self.owner, ResumeDocument.id.in_(resumes),
        ).order_by(ResumeDocument.id).with_for_update(read=True)).all()
        sources = self._candidate_sources().where(tuple_(*cols).in_(refs))
        locked = self.db.execute(sources.order_by(*cols).with_for_update(read=True)).all()
        # A source can expire while the transaction waits for its row lock.
        if len(locked) != len(refs) or len(self.db.execute(sources).all()) != len(refs):
            raise ResourceNotFoundError("Evidence source not found")

    def _current(self):
        latest = select(Item.evidence_id, func.max(Item.revision)).where(Item.user_id == self.owner).group_by(Item.evidence_id)
        return select(Item).where(Item.user_id == self.owner, tuple_(Item.evidence_id, Item.revision).in_(latest))

    def _eligible_rows(self):
        return self._current().where(Item.lifecycle == "confirmed", Item.is_private.is_(False), self._has_sources())

    def _has_sources(self):
        return Item.source_count == select(func.count()).select_from(Link).where(
            Link.user_id == Item.user_id, Link.evidence_id == Item.evidence_id, Link.revision == Item.revision,
            tuple_(Link.source_id, Link.source_version).in_(self._candidate_sources()),
        ).correlate(Item).scalar_subquery()

    def _candidate_sources(self):
        return self.career.visible_sources().with_only_columns(
            CareerSourceRow.id, CareerSourceRow.version,
        ).where(CareerSourceRow.kind != "job_description")

    def _latest(self, evidence_id: str) -> Item:
        row = self.db.scalar(self._current().where(Item.evidence_id == evidence_id, self._has_sources()))
        if row is None:
            raise ResourceNotFoundError("Evidence not found")
        return row

    def _view(self, row: Item, cipher: Fernet) -> CareerEvidenceItem:
        try:
            item = CareerEvidenceItem.model_validate_json(open_private_text(cipher, row.ciphertext))
            if row.measurement_ciphertext is None:
                return item
            measurement = EvidenceMeasurement.model_validate_json(open_private_text(cipher, row.measurement_ciphertext))
            return item.model_copy(update={"measurement": measurement})
        except ValidationError:
            raise ExternalServiceError("Career evidence could not be opened") from None

    def _insert(self, item: CareerEvidenceItem, cipher: Fernet) -> None:
        measurement = item.measurement
        self.db.add(Item(
            user_id=self.owner, evidence_id=item.evidence_id, revision=item.revision,
            lifecycle=item.lifecycle, is_private=item.is_private, source_count=len(item.sources),
            # Keep the measurement separate from the existing encrypted payload format.
            ciphertext=cipher.encrypt(item.model_dump_json(exclude={"measurement"}).encode()).decode("ascii"),
            measurement_ciphertext=cipher.encrypt(measurement.model_dump_json().encode()).decode("ascii") if measurement else None,
        ))
        self.db.flush()
        self.db.add_all(Link(
            user_id=self.owner, evidence_id=item.evidence_id, revision=item.revision, position=pos,
            source_id=link.source_id, source_version=link.source_version,
        ) for pos, link in enumerate(item.sources, start=1))


def _decision_state(old: CareerEvidenceItem, data: EvidenceDecisionInput) -> tuple[EvidenceLifecycle, list[EvidenceSourceLink]]:
    action = data.action
    sources = old.sources
    if action == "confirm":
        if old.is_private or old.lifecycle not in ("proposed", "confirmed"):
            raise InvalidOperationError("Evidence cannot be confirmed in its current state")
        return "confirmed", sources
    if action == "resolve_contradiction":
        supported = [link for link in sources if link.relationship == "supports"]
        if old.is_private or old.lifecycle != "contradicted" or not supported:
            raise InvalidOperationError("Evidence has no supported resolution")
        return "proposed", supported
    if action == "edit":
        if old.lifecycle in ("rejected", "unavailable"):
            raise InvalidOperationError("Evidence cannot be edited in its current state")
        return (old.lifecycle if old.lifecycle in ("private", "contradicted") else "proposed"), sources
    return {"reject": "rejected", "mark_private": "private", "mark_unavailable": "unavailable"}[action], sources
