"""Exercise artifact freshness and private metadata on disposable PostgreSQL."""

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4

import pytest
from alembic import command
from cryptography.fernet import Fernet
from pydantic import SecretStr, ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.application.career_service import CareerApplicationService
from app.application.errors import InvalidOperationError, ResourceConflictError, ResourceNotFoundError
from app.application.evidence_service import EvidenceService
from app.application.lineage_service import LineageService
from app.core.config import settings
from app.core.openai_client import DEFAULT_MANIFESTS
from app.db.session import engine_options
from app.models.resume_document import ResumeDocument
from app.models.user import User
from app.schemas.career.evidence import EvidenceDecisionInput, EvidenceProposal
from app.schemas.career.lineage import ArtifactInput, CareerRunManifest, ProofMetadata, RunMetadata
from app.schemas.career.persistence import CareerSourceCreate

pytestmark = pytest.mark.postgres
TABLES = ("career_interview_runs", "career_generated_artifacts", "career_artifact_runs",
          "career_artifact_claims", "career_proof_artifacts")


@pytest.fixture
def lineage(migrated_database, monkeypatch):
    engine, config = migrated_database
    command.upgrade(config, "2026_11_14_career_evidence")
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN
                    CREATE ROLE anon;
                END IF;
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'service_role') THEN
                    CREATE ROLE service_role BYPASSRLS;
                END IF;
            END $$;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public
                GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO PUBLIC, anon, authenticated, service_role;
        """)
    command.upgrade(config, "head")
    owners = (str(uuid4()), str(uuid4()))
    monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", SecretStr(Fernet.generate_key().decode()))
    with Session(engine) as db:
        db.add_all(User(user_id=owner) for owner in owners)
        db.commit()
        refs = []
        for owner in owners:
            source = CareerApplicationService(db, owner).add_source(CareerSourceCreate(
                kind="candidate_introduction", content="Built a synthetic integration.",
            )).source
            service = EvidenceService(db, owner)
            draft = service.propose(EvidenceProposal(
                claim="Built a synthetic integration", category="action", ownership="individual",
                sources=[{**source.model_dump(), "locator": "line-1", "relationship": "supports",
                          "excerpt": "Built a synthetic integration", "extraction": "candidate"}],
            ))
            confirmed = service.decide(draft.evidence_id, EvidenceDecisionInput(revision=1, action="confirm"))
            refs.append((source, confirmed))
    return engine, config, owners, refs


def artifact(*refs, **kwargs):
    return ArtifactInput(
        schema_version=1, kind="resume",
        generator={"schema_version": 1, "application_commit": "abc123",
                   "generator_version": "renderer-1", "policy_version": "policy-1"},
        claims=[{"claim_id": f"claim-{i}", "evidence_revisions": [
            {"evidence_id": ref.evidence_id, "revision": ref.revision},
        ]} for i, ref in enumerate(refs)], **kwargs,
    )


def test_exact_lineage_versions_and_privacy(lineage):
    engine, _, (owner, foreign), ((_, confirmed), (_, other)) = lineage
    with Session(engine) as db:
        service = LineageService(db, owner)
        initial = service.record_artifact(artifact(confirmed))
        assert initial.version == 1 and initial.status == "eligible"
        assert initial.claims[0].evidence_revisions[0].revision == confirmed.revision
        revision = service.record_artifact(artifact(confirmed), previous=initial)
        assert revision.artifact_id == initial.artifact_id and revision.version == 2
        assert service.get_artifact(initial) == initial
        with pytest.raises(ResourceConflictError):
            service.record_artifact(artifact(confirmed), previous=initial)
        db.rollback()
        with pytest.raises(ResourceNotFoundError):
            LineageService(db, foreign).get_artifact(initial)
        with pytest.raises(InvalidOperationError):
            service.record_artifact(artifact(confirmed, other))
        db.rollback()
        EvidenceService(db, owner).decide(confirmed.evidence_id, EvidenceDecisionInput(
            revision=confirmed.revision, action="mark_private",
        ))
        for ref in (initial, revision):
            invalidated = service.get_artifact(ref)
            assert invalidated.status == "invalidated" and invalidated.claims == []
        with pytest.raises(InvalidOperationError):
            service.record_artifact(artifact(confirmed))


def test_source_deletion_and_proof_cleanup(lineage):
    engine, _, (owner, other), ((source, confirmed), (_, foreign)) = lineage
    with Session(engine) as db:
        service = LineageService(db, owner)
        owned = service.record_artifact(artifact(confirmed))
        separate = LineageService(db, other).record_artifact(artifact(foreign))
        career = CareerApplicationService(db, owner)
        proof_source = career.add_source(CareerSourceCreate(
            kind="public_proof_link", content="https://example.invalid/synthetic",
        )).source
        proof = ProofMetadata(
            schema_version=1, source=proof_source, evidence={"evidence_id": confirmed.evidence_id,
                                                            "revision": confirmed.revision},
            access="public", confidentiality="public", ownership="individual",
        )
        proof_id = service.record_proof(proof)
        assert service.get_proof(proof_id) == proof
        with pytest.raises(ResourceNotFoundError):
            LineageService(db, other).get_proof(proof_id)
        career.delete_source(proof_source.source_id)
        assert db.scalar(text("SELECT count(*) FROM career_proof_artifacts")) == 0
        with pytest.raises(ResourceNotFoundError):
            service.get_proof(proof_id)
        career.delete_source(source.source_id)
        assert service.get_artifact(owned).status == "invalidated"
        assert LineageService(db, other).get_artifact(separate).status == "eligible"


def test_run_accepts_structured_metadata_and_rejects_private_content(lineage):
    engine, _, (owner, foreign), ((_, confirmed), (_, other)) = lineage
    for field in ("raw_prompt", "raw_transcript", "raw_response"):
        with pytest.raises(ValidationError):
            RunMetadata.model_validate({"schema_version": 1, "application_commit": "abc", "latency_ms": 4,
                                        field: "private synthetic words"})
    with Session(engine) as db:
        run_id = LineageService(db, owner).record_run(DEFAULT_MANIFESTS["tailor"], RunMetadata(
            schema_version=1, application_commit="abc", latency_ms=5, reason_codes=["safe_render_used"],
            provider_request_id="private-synthetic-marker",
        ))
        stored = db.scalar(text("SELECT ciphertext FROM career_interview_runs WHERE id = :id"), {"id": run_id})
        assert "private-synthetic-marker" not in stored and "safe_render_used" not in stored
        assert LineageService(db, owner).get_run(run_id).metadata.reason_codes == ["safe_render_used"]
        with pytest.raises(ResourceNotFoundError):
            LineageService(db, foreign).get_run(run_id)
        assert LineageService(db, owner).record_artifact(artifact(confirmed, run_id=run_id)).run_id == run_id
        with pytest.raises(ResourceNotFoundError):
            LineageService(db, foreign).record_artifact(artifact(other, run_id=run_id))


def test_career_release_manifest_round_trips_through_owner_scoped_encrypted_storage(lineage):
    engine, _, (owner, foreign), _ = lineage
    manifest = CareerRunManifest(
        schema_version=1, provider="synthetic", transport="memory", model_snapshot="synthetic-v1",
        prompt_name="career-turn", prompt_version="1", prompt_hash="a" * 64,
        response_schema_version="CareerTurnProposal.v1", schema_hash="b" * 64,
        policy_version="career-interview.v1", max_output_tokens=500, timeout_ms=5000,
    )
    metadata = RunMetadata(schema_version=1, application_commit="c" * 40, latency_ms=3)
    with Session(engine) as db:
        service = LineageService(db, owner)
        run_id = service.record_run(manifest, metadata)
        stored = service.get_run(run_id)
        assert stored.manifest == manifest and stored.metadata == metadata
        ciphertext = db.scalar(text("SELECT ciphertext FROM career_interview_runs WHERE id = :id"), {"id": run_id})
        assert manifest.prompt_hash not in ciphertext and manifest.policy_version not in ciphertext
        with pytest.raises(ResourceNotFoundError):
            LineageService(db, foreign).get_run(run_id)


def test_database_ownership_and_recovery(lineage):
    engine, config, owners, refs = lineage
    with Session(engine) as db:
        for owner, (_, evidence) in zip(owners, refs):
            service = LineageService(db, owner)
            run_id = service.record_run(DEFAULT_MANIFESTS["tailor"], RunMetadata(
                schema_version=1, application_commit="abc", latency_ms=5,
            ))
            generated = service.record_artifact(artifact(evidence, run_id=run_id))
            source = CareerApplicationService(db, owner).add_source(CareerSourceCreate(
                kind="public_proof_link", content="https://example.invalid/synthetic",
            )).source
            service.record_proof(ProofMetadata(
                schema_version=1, source=source,
                evidence={"evidence_id": evidence.evidence_id, "revision": evidence.revision},
                access="public", confidentiality="public", ownership="individual",
            ))
        with pytest.raises(DBAPIError) as denied:
            db.execute(text("""
                INSERT INTO career_artifact_claims
                    (user_id, artifact_id, artifact_version, claim_id, evidence_id, evidence_revision)
                VALUES (:owner, :artifact, 1, 'wrong-owner', :evidence, :revision)
            """), {"owner": owners[1], "artifact": generated.artifact_id,
                   "evidence": refs[0][1].evidence_id, "revision": refs[0][1].revision})
        assert denied.value.orig.pgcode == "23503"
        db.rollback()
        with pytest.raises(DBAPIError) as immutable:
            db.execute(text("UPDATE career_generated_artifacts SET link_count = 2"))
        assert immutable.value.orig.pgcode == "23514"
        db.rollback()
    with engine.begin() as conn:
        for table in TABLES:
            assert conn.scalar(text("SELECT relrowsecurity FROM pg_class WHERE oid=to_regclass(:table)"), {"table": table})
            for role in ("anon", "authenticated", "service_role"):
                assert not conn.scalar(text("""
                    SELECT has_table_privilege(:role, :table, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
                """), {"role": role, "table": table})
        conn.exec_driver_sql("""
            CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE
                AS 'SELECT nullif(current_setting(''request.jwt.claim.sub'', true), '''')::uuid';
            GRANT USAGE ON SCHEMA auth TO authenticated;
        """)
        for table in TABLES:
            conn.exec_driver_sql(f"GRANT SELECT ON {table} TO authenticated")
    for owner in owners:
        with engine.begin() as conn:
            conn.exec_driver_sql("SET LOCAL ROLE authenticated")
            conn.execute(text("SELECT set_config('request.jwt.claim.sub', :owner, true)"), {"owner": owner})
            for table in TABLES:
                assert conn.exec_driver_sql(f"SELECT DISTINCT user_id FROM {table}").scalars().all() == [owner]
    with pytest.raises(DBAPIError, match="preserved"):
        command.downgrade(config, "2026_11_14_career_evidence")
    with engine.begin() as conn:
        for owner in owners:
            conn.execute(text("DELETE FROM users WHERE user_id = :owner"), {"owner": owner})
        for table in TABLES:
            assert conn.exec_driver_sql(f"SELECT count(*) FROM {table}").scalar_one() == 0
    command.downgrade(config, "2026_11_14_career_evidence")
    command.upgrade(config, "head")


def test_concurrent_versions_get_one_winner(lineage):
    engine, _, (owner, _), ((_, confirmed), _) = lineage
    with Session(engine) as db:
        initial = LineageService(db, owner).record_artifact(artifact(confirmed))

    def append():
        with Session(engine) as db:
            try:
                return LineageService(db, owner).record_artifact(artifact(confirmed), previous=initial)
            except ResourceConflictError:
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.submit(append), pool.submit(append)
        winners = [result for result in (first.result(), second.result()) if result is not None]
    assert [result.version for result in winners] == [2]


@pytest.mark.parametrize("changes", [
    {"claim": "Built a synthetic integration and its tests"},
    {"ownership": "shared", "scope": "Owned the integration tests"},
])
def test_reconfirmation_keeps_old_claims_invalidated(lineage, changes):
    engine, _, (owner, _), ((_, confirmed), _) = lineage
    with Session(engine) as db:
        service = LineageService(db, owner)
        original = service.record_artifact(artifact(confirmed))
        ledger = EvidenceService(db, owner)
        edited = ledger.decide(confirmed.evidence_id, EvidenceDecisionInput(
            revision=confirmed.revision, action="edit", **changes,
        ))
        assert ledger.eligible(edited) is None
        assert service.get_artifact(original).status == "invalidated"
        current = ledger.decide(edited.evidence_id, EvidenceDecisionInput(revision=edited.revision, action="confirm"))
        regenerated = service.record_artifact(artifact(current), previous=original)
        assert service.get_artifact(original).status == "invalidated"
        assert regenerated.status == "eligible"
        assert regenerated.claims[0].evidence_revisions[0].revision == current.revision


def test_run_deletion_invalidates_only_linked_version(lineage):
    engine, _, (owner, _), ((_, confirmed), _) = lineage
    with Session(engine) as db:
        service = LineageService(db, owner)
        run = service.record_run(DEFAULT_MANIFESTS["tailor"], RunMetadata(
            schema_version=1, application_commit="abc", latency_ms=5,
        ))
        initial = service.record_artifact(artifact(confirmed, run_id=run))
        latest = service.record_artifact(artifact(confirmed), previous=initial)
        db.execute(text("DELETE FROM career_interview_runs WHERE id = :id"), {"id": run})
        db.commit()
        invalidated = service.get_artifact(initial)
        assert invalidated.status == "invalidated" and invalidated.claims == [] and invalidated.run_id is None
        assert service.get_artifact(latest).status == "eligible"
        assert service.record_artifact(artifact(confirmed), previous=latest).version == 3


def test_artifact_write_serializes_with_resume_unavailability(lineage, monkeypatch):
    engine, _, (owner, _), _ = lineage
    with Session(engine) as db:
        db.add(ResumeDocument(
            id="synthetic-resume", user_id=owner, original_filename="resume.pdf",
            file_path="synthetic-path", file_type="pdf", parsed_json={}, raw_text="Built a synthetic API",
        ))
        db.commit()
        source = CareerApplicationService(db, owner).add_source(CareerSourceCreate(
            kind="resume", resume_document_id="synthetic-resume",
        )).source
        evidence = EvidenceService(db, owner)
        draft = evidence.propose(EvidenceProposal(
            claim="Built a synthetic API", category="action", ownership="individual",
            sources=[{**source.model_dump(), "locator": "line-1", "relationship": "supports",
                      "excerpt": "Built a synthetic API", "extraction": "candidate"}],
        ))
        confirmed = evidence.decide(draft.evidence_id, EvidenceDecisionInput(revision=1, action="confirm"))
        service = LineageService(db, owner)
        get_artifact = service.get_artifact

        def verify_locked_after_read(ref):
            result = get_artifact(ref)
            with pytest.raises(DBAPIError) as blocked, engine.begin() as conn:
                conn.exec_driver_sql("SET LOCAL lock_timeout = '200ms'")
                conn.exec_driver_sql("UPDATE resume_documents SET storage_status = 'deleting'")
            assert blocked.value.orig.pgcode == "55P03"
            return result

        monkeypatch.setattr(service, "get_artifact", verify_locked_after_read)
        view = service.record_artifact(artifact(confirmed))
        assert view.status == "eligible"
        with engine.begin() as conn:
            conn.exec_driver_sql("UPDATE resume_documents SET storage_status = 'deleting'")
        assert get_artifact(view).status == "invalidated"


def test_run_metadata_stays_out_of_database_and_application_logs(lineage, caplog):
    log_file = os.getenv("PRI33_TEST_POSTGRES_LOG_FILE")
    container = os.getenv("PRI33_TEST_POSTGRES_CONTAINER")
    if not log_file and not container:
        pytest.skip("requires access to the disposable PostgreSQL server log")
    engine, _, (owner, _), _ = lineage
    logged_engine = create_engine(engine.url, hide_parameters=engine_options["hide_parameters"])
    marker = f"synthetic-private-{uuid4()}"
    caplog.set_level("INFO", logger="sqlalchemy.engine")
    metadata = RunMetadata(schema_version=1, application_commit="test", latency_ms=1, provider_request_id=marker)
    try:
        with Session(logged_engine) as db:
            db.execute(text("SET LOCAL log_statement = 'all'"))
            service = LineageService(db, owner)
            service.record_run(DEFAULT_MANIFESTS["tailor"], metadata)
            db.execute(text("ALTER TABLE career_interview_runs ADD CHECK (length(ciphertext) = 1) NOT VALID"))
            db.commit()
            db.execute(text("SET LOCAL log_min_error_statement = 'error'"))
            with pytest.raises(DBAPIError) as rejected:
                service.record_run(DEFAULT_MANIFESTS["tailor"], metadata)
            assert rejected.value.orig.pgcode == "23514"
            assert marker not in str(rejected.value)
            db.rollback()
            assert db.scalar(text("SELECT count(*) FROM career_interview_runs")) == 1
    finally:
        logged_engine.dispose()
    assert "INSERT INTO career_interview_runs" in caplog.text and marker not in caplog.text
    deadline = monotonic() + 5
    while True:
        if log_file:
            pg_log = Path(log_file).read_text()
        else:
            log = subprocess.run(["docker", "logs", container], capture_output=True, text=True, timeout=10, check=True)
            pg_log = log.stdout + log.stderr
        writes = [line for line in pg_log.splitlines() if owner in line]
        if (any("statement: INSERT INTO career_interview_runs" in line for line in writes)
                and any("STATEMENT:  INSERT INTO career_interview_runs" in line for line in writes)):
            break
        assert monotonic() < deadline, "PostgreSQL did not log both run writes"
        sleep(0.05)
    assert marker not in pg_log
