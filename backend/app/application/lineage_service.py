"""Internal, owner-scoped persistence for Career metadata."""

from uuid import uuid4

from sqlalchemy import and_, or_, select, tuple_
from sqlalchemy.orm import Session

from app.application.career_encryption import career_cipher, open_private_text
from app.application.errors import InvalidOperationError, ResourceConflictError, ResourceNotFoundError
from app.application.evidence_service import EvidenceService
from app.models.career import CareerSourceRow, CareerTargetRow
from app.models.career_lineage import ArtifactClaimRow as Claim
from app.models.career_lineage import CareerRunRow as Run
from app.models.career_lineage import GeneratedArtifactRow as Artifact
from app.models.career_lineage import ArtifactRunRow, ProofArtifactRow
from app.models.interview import InterviewSessionRow
from app.models.resume_document import ResumeVersion
from app.repositories.career_repository import CareerRepository
from app.repositories.interview_repository import InterviewRepository
from app.schemas.career.common import SourceRef
from app.schemas.career.evidence import EvidenceRevisionRef
from app.schemas.career.lineage import ArtifactInput, ArtifactRef, ArtifactView, ProofMetadata, RunManifest, RunMetadata, StoredRun
from app.schemas.career.resume import GeneratedClaimLineage


class LineageService:
    """Use with an authenticated subject and a request-scoped database session."""

    def __init__(self, db: Session, owner: str):
        self.db = db
        self.owner = owner
        self.career = CareerRepository(db, owner)
        self.evidence = EvidenceService(db, owner)
        self.interviews = InterviewRepository(db, owner)

    def record_run(self, manifest: RunManifest, metadata: RunMetadata) -> str:
        self._lock_owner()
        if metadata.session_id and self.interviews.get(metadata.session_id, lock=True) is None:
            raise ResourceNotFoundError("Interview not found")
        run_id = self.stage_run(StoredRun(schema_version=1, manifest=manifest, metadata=metadata))
        self.db.commit()
        return run_id

    def stage_run(self, run: StoredRun) -> str:
        """Stage an encrypted run inside a transaction whose caller owns the session lock."""
        ciphertext = career_cipher(scope="Career run").encrypt(run.model_dump_json().encode()).decode("ascii")
        run_id = str(uuid4())
        self.db.add(Run(user_id=self.owner, id=run_id, session_id=run.metadata.session_id, ciphertext=ciphertext))
        return run_id

    def get_run(self, run_id: str) -> StoredRun:
        row = self.db.scalar(self._active_runs().where(Run.id == run_id))
        if row is None:
            raise ResourceNotFoundError("Career run not found")
        return StoredRun.model_validate_json(open_private_text(career_cipher(scope="Career run"), row.ciphertext))

    def record_artifact(self, data: ArtifactInput, previous: ArtifactRef | None = None) -> ArtifactView:
        result = self.stage_artifact(data, previous=previous)
        self.db.commit()
        return result

    def stage_artifact(
        self, data: ArtifactInput, *, artifact_id: str | None = None, previous: ArtifactRef | None = None,
    ) -> ArtifactView:
        self._lock_owner()
        if data.target_id:
            target = select(CareerTargetRow.id).where(
                CareerTargetRow.user_id == self.owner, CareerTargetRow.id == data.target_id,
                CareerTargetRow.status == "active",
            ).with_for_update(read=True)
            if self.db.scalar(target) is None:
                raise ResourceNotFoundError("Career target not found")
        if data.run_id and self.db.scalar(self._active_runs().where(Run.id == data.run_id)
                                              .with_for_update(read=True, key_share=True)) is None:
            raise ResourceNotFoundError("Career run not found")
        keys = {(ref.evidence_id, ref.revision) for claim in data.claims for ref in claim.evidence_revisions}
        self.evidence.lock_eligible_revisions(keys)

        artifact_id, version = artifact_id or str(uuid4()), 1
        if previous is not None:
            artifact_id, version = previous.artifact_id, previous.version + 1
            artifacts = self._artifacts(artifact_id)
            anchor = self.db.scalar(artifacts.where(Artifact.version == 1).with_for_update())
            if anchor is None:
                raise ResourceNotFoundError("Career artifact not found")
            latest = self.db.scalar(artifacts.order_by(Artifact.version.desc()).limit(1))
            if latest.version != previous.version:
                raise ResourceConflictError("Career artifact version is no longer current")
            if (latest.kind, latest.target_id) != (data.kind, data.target_id):
                raise InvalidOperationError("A new version must keep its artifact kind and target")

        links = [Claim(
            user_id=self.owner, artifact_id=artifact_id, artifact_version=version, claim_id=claim.claim_id,
            evidence_id=ref.evidence_id, evidence_revision=ref.revision,
        ) for claim in data.claims for ref in claim.evidence_revisions]
        with self.db.begin_nested():
            self.db.add(Artifact(
                user_id=self.owner, id=artifact_id, version=version, kind=data.kind, target_id=data.target_id,
                requires_run=data.run_id is not None, generator=data.generator.model_dump(mode="json"), link_count=len(links),
            ))
            self.db.flush()
            if data.run_id:
                self.db.add(ArtifactRunRow(
                    user_id=self.owner, artifact_id=artifact_id, artifact_version=version, run_id=data.run_id,
                ))
            self.db.add_all(links)
            self.db.flush()
            result = self.get_artifact(ArtifactRef(schema_version=1, artifact_id=artifact_id, version=version))
            if result.status != "eligible":
                raise InvalidOperationError("Career artifact is no longer eligible")
        return result

    def get_artifact(self, reference: ArtifactRef) -> ArtifactView:
        same_version = and_(
            Claim.user_id == self.owner, Claim.artifact_id == reference.artifact_id,
            Claim.artifact_version == reference.version,
        )
        evidence_ids = select(Claim.evidence_id).where(same_version).correlate(None)
        eligible = tuple_(Claim.evidence_id, Claim.evidence_revision).in_(self.evidence.eligible_keys(evidence_ids))
        same_run_version = and_(
            ArtifactRunRow.user_id == self.owner, ArtifactRunRow.artifact_id == reference.artifact_id,
            ArtifactRunRow.artifact_version == reference.version,
        )
        run_is_live = or_(Artifact.requires_run.is_(False), ArtifactRunRow.run_id.in_(
            self._active_runs().with_only_columns(Run.id),
        ))
        query = (
            select(Artifact, Claim, eligible, run_is_live, ArtifactRunRow.run_id)
            .outerjoin_from(Artifact, Claim, same_version)
            .outerjoin_from(Artifact, ArtifactRunRow, same_run_version)
            .where(Artifact.user_id == self.owner, Artifact.id == reference.artifact_id,
                   Artifact.version == reference.version)
            .order_by(Claim.claim_id, Claim.evidence_id)
        )
        rows = self.db.execute(query).all()
        if not rows:
            raise ResourceNotFoundError("Career artifact not found")
        item = rows[0][0]
        usable = len(rows) == item.link_count and all(ok and live_run for _, _, ok, live_run, _ in rows)
        claim_refs: dict[str, list[EvidenceRevisionRef]] = {}
        if usable:
            for _, link, _, _, _ in rows:
                claim_refs.setdefault(link.claim_id, []).append(EvidenceRevisionRef(
                    evidence_id=link.evidence_id, revision=link.evidence_revision,
                ))
        return ArtifactView(
            schema_version=1, artifact_id=item.id, version=item.version, kind=item.kind, generator=item.generator,
            target_id=item.target_id, run_id=rows[0][4], created_at=item.created_at,
            status="eligible" if usable else "invalidated",
            claims=[GeneratedClaimLineage(
                schema_version=1, artifact_id=item.id, artifact_version=item.version,
                claim_id=claim_id, evidence_revisions=refs,
            ) for claim_id, refs in claim_refs.items()],
        )

    def require_grounded_resume(self, version: ResumeVersion, *, lock: bool = False) -> ArtifactView | None:
        receipt = version.change_set
        if not isinstance(receipt, dict) or "grounded" not in receipt:
            return None
        jd = SourceRef.model_validate(receipt["grounded"]["jd_source"])
        if lock:
            self._lock_owner()
            if self.career.ready_resume(version.resume_document_id) is None or self.career.get_source(jd, lock=True) is None:
                raise ResourceConflictError("The saved Tailor résumé or job description is unavailable.")
        artifact = self.get_artifact(ArtifactRef(schema_version=1, artifact_id=version.id, version=1))
        if artifact.status != "eligible":
            raise ResourceConflictError("Tailor evidence changed. Generate a new draft.")
        target = self.career.get_target(artifact.target_id, lock=lock)
        if (target is None or target.status != "active" or
            (target.jd_source_id, target.jd_source_version) != (jd.source_id, jd.source_version) or
            self.career.get_source(jd) is None):
            raise ResourceConflictError("The saved Tailor target changed. Generate a new draft.")
        if lock:
            try:
                self.evidence.lock_eligible_revisions({
                    (ref.evidence_id, ref.revision) for claim in artifact.claims for ref in claim.evidence_revisions
                })
            except InvalidOperationError:
                raise ResourceConflictError("Tailor evidence changed. Generate a new draft.") from None
        return artifact

    def record_proof(self, metadata: ProofMetadata) -> str:
        self._lock_owner()
        self.evidence.lock_eligible_revisions(
            {(metadata.evidence.evidence_id, metadata.evidence.revision)}, extra_sources=[metadata.source],
        )
        source = self.career.get_source(metadata.source)
        if source is None or source.kind != "public_proof_link":
            raise ResourceNotFoundError("Proof source not found")
        proof_id = str(uuid4())
        with self.db.begin_nested():
            self.db.add(ProofArtifactRow(
                user_id=self.owner, id=proof_id, source_id=metadata.source.source_id,
                source_version=metadata.source.source_version, evidence_id=metadata.evidence.evidence_id,
                evidence_revision=metadata.evidence.revision,
                attributes=metadata.model_dump(mode="json", exclude={"source", "evidence"}),
            ))
            self.db.flush()
            self.get_proof(proof_id)
        self.db.commit()
        return proof_id

    def get_proof(self, proof_id: str) -> ProofMetadata:
        proof = ProofArtifactRow
        key = tuple_(proof.evidence_id, proof.evidence_revision)
        sources = self.career.visible_sources().with_only_columns(CareerSourceRow.id, CareerSourceRow.version)
        row = self.db.scalar(select(proof).where(
            proof.user_id == self.owner, proof.id == proof_id,
            key.in_(self.evidence.eligible_keys(select(proof.evidence_id).where(
                proof.user_id == self.owner, proof.id == proof_id,
            ).correlate(None))),
            tuple_(proof.source_id, proof.source_version).in_(sources),
        ))
        if row is None:
            raise ResourceNotFoundError("Proof metadata not found")
        return ProofMetadata(
            **row.attributes,
            source=SourceRef(source_id=row.source_id, source_version=row.source_version),
            evidence=EvidenceRevisionRef(evidence_id=row.evidence_id, revision=row.evidence_revision),
        )

    def _active_runs(self):
        sessions = self.interviews.sessions().with_only_columns(InterviewSessionRow.id)
        return select(Run).where(Run.user_id == self.owner, or_(Run.session_id.is_(None), Run.session_id.in_(sessions)))

    def _artifacts(self, artifact_id: str):
        return select(Artifact).where(Artifact.user_id == self.owner, Artifact.id == artifact_id)

    def _lock_owner(self) -> None:
        if not self.career.lock_owner_for_insert():
            raise ResourceNotFoundError("Account not found")
