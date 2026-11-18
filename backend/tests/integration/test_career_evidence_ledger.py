"""Check evidence decisions, provenance and isolation on migrated PostgreSQL."""
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4

import pytest
from alembic import command
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.application.career_service import CareerApplicationService
from app.application.evidence_service import EvidenceService
from app.application.errors import ExternalServiceError, InvalidOperationError, ResourceConflictError, ResourceNotFoundError
from app.core import auth
from app.core.config import settings
from app.db.session import engine_options, get_db
from app.main import app
from app.models.resume_document import ResumeDocument
from app.models.user import User
from app.schemas.career.evidence import EvidenceDecisionInput, EvidenceProposal
from app.schemas.career.persistence import CareerSourceCreate

pytestmark = pytest.mark.postgres


@pytest.fixture
def ledger(migrated_database, monkeypatch):
    engine, config = migrated_database
    command.upgrade(config, "2026_11_14_career_interviews")
    with engine.begin() as c:
        c.exec_driver_sql("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN
                    CREATE ROLE anon;
                END IF;
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'service_role') THEN
                    CREATE ROLE service_role BYPASSRLS;
                END IF;
            END $$;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public
                GRANT SELECT ON TABLES TO PUBLIC, anon, authenticated, service_role;
        """)
    command.upgrade(config, "head")
    owners = [str(uuid4()), str(uuid4())]
    monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", SecretStr(Fernet.generate_key().decode()))
    with Session(engine) as db:
        db.add_all(User(user_id=owner) for owner in owners)
        db.commit()
        sources = [
            CareerApplicationService(db, owner).add_source(CareerSourceCreate(
                kind="candidate_introduction", content="Built the synthetic API and wrote its tests.",
            )).source
            for owner in owners
        ]
    return engine, config, owners, sources


def proposal(source, relationship="supports"):
    return EvidenceProposal(claim="Built the synthetic API", category="action", ownership="individual", sources=[
        {**source.model_dump(), "relationship": relationship, "locator": "line 1",
         "excerpt": "Built the synthetic API", "extraction": "model"},
    ])


def test_authenticated_decisions_are_owned_versioned_and_cache_private(ledger, monkeypatch):
    engine, _, (owner, other), (source, _) = ledger
    with Session(engine) as db:
        first = EvidenceService(db, owner).propose(proposal(source))
    path = f"/api/v1/career/evidence/{first.evidence_id}"
    monkeypatch.setattr(auth, "decode_supabase_jwt", lambda token: {"sub": {"a": owner, "b": other}[token]})
    def db_session():
        with Session(engine) as db:
            yield db
    monkeypatch.setitem(app.dependency_overrides, get_db, db_session)
    a = {"Authorization": "Bearer a"}
    b = {"Authorization": "Bearer b"}
    with TestClient(app) as client:
        assert client.get(path).status_code == 401
        assert client.get("/api/v1/career/evidence", headers=b).json() == []
        assert client.get(path, headers=b).status_code == 404
        assert client.get(path + "/history", headers=b).status_code == 404
        assert client.patch(path + "/decision", headers=b, json={"revision": 1, "action": "confirm"}).status_code == 404
        invalid = client.patch(path + "/decision", headers=a, json={"revision": 1, "action": "confirm", "actor_id": other})
        assert invalid.status_code == 422 and other not in invalid.text
        confirmed = client.patch(path + "/decision", headers=a, json={"revision": 1, "action": "confirm"})
        assert confirmed.status_code == 200 and confirmed.headers["cache-control"] == "no-store"
        assert confirmed.json()["lifecycle"] == "confirmed"
        assert confirmed.json()["support"] == "candidate_statement"
        stale = client.patch(path + "/decision", headers=a, json={"revision": 1, "action": "reject"})
        assert stale.status_code == 409
        edited = client.patch(path + "/decision", headers=a, json={"revision": 2, "action": "edit", "claim": "Built the API tests"})
        assert edited.status_code == 200 and edited.json()["lifecycle"] == "proposed"
        history = client.get(path + "/history", headers=a).json()
        assert [x["claim"] for x in history["revisions"]] == [first.claim, first.claim, "Built the API tests"]
        assert [d["actor_id"] for d in history["decisions"]] == [owner, owner]
        assert [d["action"] for d in history["decisions"]] == ["confirm", "edit"]

        measurement = {
            "method": "Compared median synthetic test runs",
            "scope": "Local benchmark fixture",
            "estimated": True,
        }
        metadata = {
            "ownership": "shared", "scope": "Owned the regression tests", "measurement": measurement,
        }
        decision = {"revision": 3, "action": "edit", **metadata}
        corrected = client.patch(path + "/decision", headers=a, json=decision)
        assert corrected.status_code == 200
        current = corrected.json()
        assert {field: current[field] for field in metadata} == metadata
        assert current["revision"] == 4 and current["lifecycle"] == "proposed"
        assert current["claim"] == edited.json()["claim"]
        assert current["support"] == "candidate_statement"
        assert client.patch(path + "/decision", headers=b, json=decision).status_code == 404
        assert client.patch(path + "/decision", headers=a, json=decision | {"revision": 2}).status_code == 409
        assert client.patch(path + "/decision", headers=a, json=decision | {"action": "confirm"}).status_code == 422
        assert client.patch(path + "/decision", headers=a, json=decision | {
            "measurement": measurement | {"estimated": "yes"},
        }).status_code == 422
        approved = client.patch(path + "/decision", headers=a, json={"revision": 4, "action": "confirm"})
        assert approved.status_code == 200 and approved.json()["measurement"] == measurement
        replacement = measurement | {"method": "Compared recorded synthetic runs", "estimated": False}
        revised = client.patch(path + "/decision", headers=a, json={
            "revision": 5, "action": "edit", "claim": "Maintained the API tests", "scope": None,
            "measurement": replacement,
        })
        assert revised.status_code == 200
        assert client.get(path, headers=a).json()["measurement"] == replacement
        changed = client.patch(path + "/decision", headers=a, json={
            "revision": 6, "action": "edit", "claim": "Maintained and ran the API tests",
        })
        assert changed.status_code == 200
        assert changed.json()["ownership"] == "shared" and changed.json()["scope"] is None
        assert changed.json()["measurement"] is None
        history = client.get(path + "/history", headers=a).json()
        assert [entry["revision"] for entry in history["revisions"]] == list(range(1, 8))
        assert history["revisions"][3]["measurement"] == measurement
        assert history["revisions"][4]["measurement"] == measurement
        assert history["revisions"][5]["measurement"] == replacement
        assert history["revisions"][2]["ownership"] == "individual"
        assert [entry["action"] for entry in history["decisions"]][-4:] == ["edit", "confirm", "edit", "edit"]


def test_foreign_sources_contradictions_and_deleted_sources_fail_closed(ledger):
    engine, _, (owner, _), (source, foreign) = ledger
    with Session(engine) as db:
        service = EvidenceService(db, owner)
        with pytest.raises(ResourceNotFoundError):
            service.propose(proposal(foreign))
        db.rollback()
        fabricated = proposal(source)
        fabricated.sources[0] = fabricated.sources[0].model_copy(
            update={"excerpt": None, "excerpt_sha256": "f" * 64},
        )
        with pytest.raises(InvalidOperationError, match="verifiable"):
            service.propose(fabricated)
        db.rollback()
        repeated = CareerApplicationService(db, owner).add_source(CareerSourceCreate(
            kind="candidate_introduction", content="Built the synthetic API. Built the synthetic API.",
        ))
        with pytest.raises(InvalidOperationError, match="exactly once"):
            service.propose(proposal(repeated.source))
        db.rollback()
        job = CareerApplicationService(db, owner).add_source(CareerSourceCreate(
            kind="job_description", content="Built the synthetic API",
        ))
        with pytest.raises(ResourceNotFoundError):
            service.propose(proposal(job.source))
        db.rollback()
        opposing = service.propose(proposal(source, "contradicts"))
        assert opposing.lifecycle == "contradicted"
        with pytest.raises(InvalidOperationError):
            service.decide(opposing.evidence_id, EvidenceDecisionInput(revision=1, action="confirm"))
        db.rollback()
        mixed = proposal(source)
        mixed.sources += proposal(source, "contradicts").sources
        with pytest.raises(InvalidOperationError, match="distinct"):
            service.propose(mixed)
        db.rollback()
        mixed.sources[-1] = mixed.sources[-1].model_copy(update={"excerpt": "wrote its tests"})
        disputed = service.propose(mixed)
        resolved = service.decide(disputed.evidence_id, EvidenceDecisionInput(revision=1, action="resolve_contradiction"))
        assert resolved.lifecycle == "proposed"
        assert service.eligible(resolved) is None
        assert service.history(disputed.evidence_id).revisions[0].lifecycle == "contradicted"
        supported = service.propose(proposal(source))
        assert supported.sources[0].locator == "chars:0-23"
        confirmed = service.decide(supported.evidence_id, EvidenceDecisionInput(revision=1, action="confirm"))
        assert service.eligible(confirmed) == confirmed
        private = service.decide(supported.evidence_id, EvidenceDecisionInput(revision=2, action="mark_private"))
        assert private.is_private and service.eligible(confirmed) is None and service.eligible(private) is None
        with pytest.raises(InvalidOperationError):
            service.decide(private.evidence_id, EvidenceDecisionInput(revision=3, action="confirm"))
        db.rollback()
        for action in ("reject", "mark_unavailable"):
            initial = service.propose(proposal(source))
            confirmed = service.decide(initial.evidence_id, EvidenceDecisionInput(revision=1, action="confirm"))
            suppressed = service.decide(initial.evidence_id, EvidenceDecisionInput(revision=2, action=action))
            assert service.eligible(confirmed) is None and service.eligible(suppressed) is None
            with pytest.raises(InvalidOperationError):
                service.decide(initial.evidence_id, EvidenceDecisionInput(revision=3, action="confirm"))
            db.rollback()
        keep = service.propose(proposal(source))
        keep = service.decide(keep.evidence_id, EvidenceDecisionInput(revision=1, action="confirm"))
        CareerApplicationService(db, owner).delete_source(source.source_id)
        assert service.eligible(keep) is None
        assert service.list() == []
        assert db.scalar(text("SELECT count(*) FROM career_evidence_items WHERE user_id=:owner"), {"owner": owner}) == 0
        assert db.scalar(text("SELECT count(*) FROM career_evidence_decisions WHERE user_id=:owner"), {"owner": owner}) == 0


def test_measurement_upgrade_preserves_legacy_payload_and_guards_recorded_data(ledger):
    engine, config, (owner, _), (source, _) = ledger
    with Session(engine) as db:
        prior = EvidenceService(db, owner).propose(proposal(source))
    command.downgrade(config, "2026_11_16_career_recovery")
    with engine.connect() as conn:
        legacy_ciphertext = conn.scalar(text("SELECT ciphertext FROM career_evidence_items"))
        assert "measurement_ciphertext" not in conn.execute(text("SELECT * FROM career_evidence_items LIMIT 0")).keys()
    command.upgrade(config, "head")

    measurement = {"method": "Compared synthetic test runs", "scope": "Local suite", "estimated": False}
    with Session(engine) as db:
        ledger_service = EvidenceService(db, owner)
        assert ledger_service.get(prior.evidence_id) == prior
        with pytest.raises(ValidationError):
            EvidenceProposal.model_validate(proposal(source).model_dump() | {"measurement": measurement})
        edited = ledger_service.decide(prior.evidence_id, EvidenceDecisionInput(
            revision=1, action="edit", measurement=measurement,
        ))
        assert ledger_service.get(prior.evidence_id) == edited
        cleared = ledger_service.decide(prior.evidence_id, EvidenceDecisionInput(
            revision=2, action="edit", measurement=None,
        ))
        assert cleared.measurement is None

    cipher = Fernet(settings.CAREER_TRANSCRIPT_KEY.get_secret_value().encode())
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT ciphertext, measurement_ciphertext FROM career_evidence_items ORDER BY revision"
        )).all()
        assert rows[0] == (legacy_ciphertext, None)
        assert "measurement" not in json.loads(cipher.decrypt(rows[1].ciphertext.encode()))
        token = rows[1].measurement_ciphertext
        assert measurement["method"] not in token
        assert json.loads(cipher.decrypt(token.encode())) == measurement
        assert rows[2].measurement_ciphertext is None
    with pytest.raises(DBAPIError, match="preserved"):
        command.downgrade(config, "2026_11_16_career_recovery")
    with Session(engine) as db:
        assert EvidenceService(db, owner).history(prior.evidence_id).revisions[1] == edited


def test_resume_cascade_purges_only_linked_history(ledger):
    engine, _, (owner, other), (source, other_source) = ledger
    with Session(engine) as db:
        db.add(ResumeDocument(
            id="synthetic-resume", user_id=owner, original_filename="resume.pdf",
            file_path="synthetic-path", file_type="pdf", parsed_json={},
            raw_text="Résumé\nBuilt the synthetic API",
        ))
        db.commit()
        snapshot = CareerApplicationService(db, owner).add_source(CareerSourceCreate(
            kind="resume", resume_document_id="synthetic-resume",
        )).source
        service = EvidenceService(db, owner)
        linked = proposal(source)
        linked.sources += proposal(snapshot).sources
        item = service.propose(linked)
        assert item.sources[1].locator == "chars:7-30"
        service.decide(item.evidence_id, EvidenceDecisionInput(revision=1, action="confirm"))
        owner_keep = service.propose(proposal(source))
        other_service = EvidenceService(db, other)
        other_keep = other_service.propose(proposal(other_source))
        with engine.begin() as c:
            c.exec_driver_sql("""
                DO $$ BEGIN
                    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'pri34_test_runtime') THEN
                        CREATE ROLE pri34_test_runtime BYPASSRLS;
                    END IF;
                END $$;
                GRANT USAGE ON SCHEMA public TO pri34_test_runtime;
                GRANT SELECT, DELETE ON resume_documents TO pri34_test_runtime;
                GRANT SELECT ON career_evidence_sources TO pri34_test_runtime;
                GRANT SELECT, UPDATE, DELETE ON career_evidence_items TO pri34_test_runtime;
                SET LOCAL ROLE pri34_test_runtime;
                DELETE FROM resume_documents WHERE id = 'synthetic-resume';
            """)
        assert service.list() == [owner_keep]
        assert other_service.list() == [other_keep]
        assert db.scalar(text("SELECT count(*) FROM career_evidence_items")) == 2
        assert db.scalar(text("SELECT count(*) FROM career_evidence_decisions")) == 0


def test_evidence_encryption_and_database_owner_policies(ledger, monkeypatch):
    engine, _, owners, sources = ledger
    roles = ("anon", "authenticated", "service_role")
    tables = ("career_evidence_items", "career_evidence_sources", "career_evidence_decisions")
    with Session(engine) as db:
        for owner, source in zip(owners, sources):
            service = EvidenceService(db, owner)
            item = service.propose(proposal(source))
            service.decide(item.evidence_id, EvidenceDecisionInput(
                revision=1, action="reject", reason="synthetic private reason",
            ))
        monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", SecretStr(Fernet.generate_key().decode()))
        with pytest.raises(ExternalServiceError, match="could not be opened"):
            service.get(item.evidence_id)
    with engine.begin() as c:
        assert all("Built the synthetic API" not in token for token in c.scalars(
            text("SELECT ciphertext FROM career_evidence_items")
        ))
        assert all("synthetic private reason" not in token for token in c.scalars(
            text("SELECT reason_ciphertext FROM career_evidence_decisions")
        ))
        for table in tables:
            assert c.scalar(text("SELECT relrowsecurity FROM pg_class WHERE oid=to_regclass(:table)"), {"table": table})
            for role in roles:
                assert not c.scalar(text("SELECT has_table_privilege(:role, :table, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE')"),
                                    {"role": role, "table": table})
        c.exec_driver_sql("""
            CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE
                AS 'SELECT nullif(current_setting(''request.jwt.claim.sub'', true), '''')::uuid';
            GRANT USAGE ON SCHEMA auth TO authenticated;
            GRANT SELECT ON career_evidence_items, career_evidence_sources, career_evidence_decisions TO authenticated;
        """)
    for owner in owners:
        with engine.begin() as c:
            c.exec_driver_sql("SET LOCAL ROLE authenticated")
            c.execute(text("SELECT set_config('request.jwt.claim.sub', :owner, true)"), {"owner": owner})
            for table in tables:
                assert c.exec_driver_sql(f"SELECT DISTINCT user_id FROM {table}").scalars().all() == [owner]


def test_concurrent_decisions_choose_one_revision_and_migration_guards_history(ledger):
    engine, config, (owner, _), (source, _) = ledger
    with Session(engine) as db:
        first = EvidenceService(db, owner).propose(proposal(source))
    def decide(action):
        with Session(engine) as db:
            try:
                return EvidenceService(db, owner).decide(first.evidence_id, EvidenceDecisionInput(revision=1, action=action))
            except ResourceConflictError:
                return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(decide, ["confirm", "reject"]))
    assert sum(result is not None for result in outcomes) == 1
    with pytest.raises(DBAPIError), engine.begin() as c:
        c.execute(text("UPDATE career_evidence_items SET is_private = true"))
    with pytest.raises(DBAPIError), engine.begin() as c:
        c.execute(text("UPDATE career_evidence_decisions SET resulting_revision = 1"))
    with pytest.raises(DBAPIError, match="preserved"):
        command.downgrade(config, "2026_11_14_career_interviews")
    with engine.begin() as c:
        c.execute(text("DELETE FROM users WHERE user_id = :owner"), {"owner": owner})
        assert c.scalar(text("SELECT count(*) FROM career_evidence_items")) == 0
        assert c.scalar(text("SELECT count(*) FROM career_evidence_decisions")) == 0
    command.downgrade(config, "2026_11_14_career_interviews")
    command.upgrade(config, "head")


def test_evidence_plaintext_stays_out_of_success_and_failure_logs(ledger, caplog):
    log_file = os.getenv("PRI33_TEST_POSTGRES_LOG_FILE")
    container = os.getenv("PRI33_TEST_POSTGRES_CONTAINER")
    if not log_file and not container:
        pytest.skip("requires access to the disposable PostgreSQL server log")
    engine, _, (owner, _), (source, _) = ledger
    logged_engine = create_engine(engine.url, hide_parameters=engine_options["hide_parameters"])
    private = f"private-evidence-{uuid4()}"
    caplog.set_level("INFO", logger="sqlalchemy.engine")
    try:
        with Session(logged_engine) as db:
            db.execute(text("SET LOCAL log_statement = 'all'"))
            data = proposal(source).model_copy(update={"claim": private})
            service = EvidenceService(db, owner)
            item = service.propose(data)
            db.execute(text("SET LOCAL log_statement = 'all'"))
            service.decide(item.evidence_id, EvidenceDecisionInput(
                revision=1, action="edit", reason=private,
                measurement={"method": private, "scope": "Synthetic scope", "estimated": True},
            ))
            db.execute(text("""
                ALTER TABLE career_evidence_decisions ADD CHECK (action <> 'reject')
            """))
            db.commit()
            db.execute(text("SET LOCAL log_min_error_statement = 'error'"))
            with pytest.raises(DBAPIError) as rejected:
                service.decide(item.evidence_id, EvidenceDecisionInput(revision=2, action="reject", reason=private))
            assert rejected.value.orig.pgcode == "23514"
            assert private not in str(rejected.value)
            db.rollback()
            assert len(service.history(item.evidence_id).revisions) == 2
    finally:
        logged_engine.dispose()
    assert "INSERT INTO career_evidence_decisions" in caplog.text
    assert private not in caplog.text
    deadline = monotonic() + 5
    while True:
        if log_file:
            pg_log = Path(log_file).read_text()
        else:
            result = subprocess.run(["docker", "logs", container], capture_output=True, text=True, timeout=10, check=True)
            pg_log = result.stdout + result.stderr
        writes = [line for line in pg_log.splitlines() if item.evidence_id in line]
        if (any("statement: INSERT INTO career_evidence_decisions" in line for line in writes)
                and any("STATEMENT:  INSERT INTO career_evidence_decisions" in line for line in writes)):
            break
        assert monotonic() < deadline, "PostgreSQL did not log both decision writes"
        sleep(0.05)
    assert private not in pg_log
