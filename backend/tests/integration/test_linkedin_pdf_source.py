"""Authenticated LinkedIn PDF workflows and PostgreSQL invariants."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import os
from pathlib import Path
from threading import BoundedSemaphore, Event
from uuid import uuid4

import pytest
from alembic import command
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pydantic import SecretStr
import fitz
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints import linkedin_pdf
from app.application import linkedin_pdf_service
from app.application.career_service import CareerApplicationService
from app.application.errors import ResourceNotFoundError
from app.application.evidence_service import EvidenceService
from app.application.linkedin_review import LinkedInReviewService
from app.core import auth
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.career import CareerSourceRow, LinkedInPdfUploadRow
from app.models.career_evidence import EvidenceRow, EvidenceSourceRow
from app.models.resume_document import ResumeDocument
from app.models.user import User
from app.schemas.career.common import SourceRef
from app.schemas.career.evidence import EvidenceDecisionInput, EvidenceProposal, EvidenceRevisionRef
from app.schemas.career.persistence import CareerSourceCreate, CareerTargetInput
from app.services.storage.exceptions import StorageDeleteError, StorageUploadError
from app.services.storage.supabase_storage import get_storage

PREFIX = "/api/v1/career/linkedin-profiles"
TARGETS = "/api/v1/career/targets"
FIXTURES = Path(__file__).parents[1] / "fixtures" / "anydoc"
PDF = (FIXTURES / "linkedin-style.pdf").read_bytes()


class Storage:
    def __init__(self):
        self.objects = {}

    def upload(self, user_id, file_id, content, filename):
        path = f"{user_id}/{file_id}.pdf"
        assert path not in self.objects
        self.objects[path] = content
        return path

    def delete(self, path):
        return self.objects.pop(path, None) is not None

    def download(self, path):
        return self.objects[path]


@pytest.fixture
def sqlite_database():
    # CI's fast coverage run exercises the same API without PostgreSQL lock and RLS assertions.
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def functions(connection, _):
        connection.create_function("char_length", 1, len)
        connection.create_function("statement_timestamp", 0, lambda: datetime.now(timezone.utc).isoformat())

    with engine.begin() as connection:
        connection.exec_driver_sql("""
            CREATE TABLE resume_documents (
                user_id TEXT, id TEXT, storage_status TEXT, PRIMARY KEY (user_id, id)
            )
        """)
        for model in (User, CareerSourceRow, LinkedInPdfUploadRow, EvidenceRow, EvidenceSourceRow):
            model.__table__.create(connection)

    @event.listens_for(Session, "loaded_as_persistent")
    def restore_utc(session, row):
        if session.bind is engine and isinstance(row, CareerSourceRow) and row.created_at.tzinfo is None:
            row.created_at = row.created_at.replace(tzinfo=timezone.utc)

    try:
        yield engine
    finally:
        event.remove(Session, "loaded_as_persistent", restore_utc)
        engine.dispose()


@pytest.fixture
def setup(request, monkeypatch):
    if make_url(os.environ["DATABASE_URL"]).get_backend_name() == "postgresql":
        engine, config = request.getfixturevalue("migrated_database")
        command.upgrade(config, "head")
    elif request.node.get_closest_marker("postgres"):
        pytest.skip("requires a disposable PostgreSQL server")
    else:
        engine = request.getfixturevalue("sqlite_database")
    monkeypatch.setattr(settings, "LINKEDIN_PDF_UPLOADS_ENABLED", True)
    with Session(engine) as db:
        owners = [str(uuid4()), str(uuid4())]
        db.add_all(User(user_id=user_id) for user_id in owners)
        db.commit()
    storage = Storage()
    monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", SecretStr(Fernet.generate_key().decode()))
    monkeypatch.setattr(auth, "decode_supabase_jwt", lambda token: {"sub": owners[int(token)]})

    def session():
        with Session(engine, expire_on_commit=engine.dialect.name != "sqlite") as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, session)
    monkeypatch.setitem(app.dependency_overrides, get_storage, lambda: storage)
    with TestClient(app) as client:
        yield client, engine, storage, owners


def upload(client, owner=0, path=PREFIX, content=PDF, filename="profile.pdf", media_type="application/pdf"):
    return client.post(path, headers=identity(owner), files={"file": (filename, content, media_type)})


def identity(owner):
    return {"Authorization": f"Bearer {owner}"}


def test_two_accounts_and_immutable_proposed_evidence(setup):
    client, engine, storage, owners = setup
    assert client.get(PREFIX).status_code == 401
    first = upload(client)
    assert first.status_code == 201
    document = first.json()["document"]
    source_id = document["source"]["source_id"]
    base = f"{PREFIX}/{source_id}"
    v1 = f"{base}/versions/1"
    assert first.headers["cache-control"] == "no-store"
    assert document["coverage"] == "uploaded_export_only"
    assert document["name"] == "Alex Example"
    assert {s["name"] for s in document["sections"]} >= {"headline", "experience", "education", "skills"}
    assert all(s["page"] >= 1 and s["locator"] for s in document["sections"])
    evidence = client.get("/api/v1/career/evidence", headers=identity(0)).json()
    assert evidence and {item["lifecycle"] for item in evidence} == {"proposed"}
    assert all(item["sources"][0]["source_id"] == source_id for item in evidence)
    with Session(engine) as db:
        assert EvidenceService(db, owners[0]).eligible(EvidenceRevisionRef(
            evidence_id=evidence[0]["evidence_id"], revision=1,
        )) is None
    assert client.get(PREFIX, headers=identity(1)).json() == []
    assert upload(client, owner=1).status_code == 201
    for path in (v1, v1 + "/pdf"):
        assert client.get(path, headers=identity(1)).status_code == 404
    assert upload(client, owner=1, path=v1).status_code == 404
    assert client.delete(base, headers=identity(1)).status_code == 404

    second = upload(client, path=v1, content=(FIXTURES / "simple.pdf").read_bytes())
    assert second.status_code == 201 and second.json()["document"]["source"]["source_version"] == 2
    assert second.json()["document"]["raw_text"] != document["raw_text"]
    assert client.get(v1, headers=identity(0)).json()["document"] == document
    assert upload(client, path=v1).status_code == 409
    download = client.get(v1 + "/pdf", headers=identity(0))
    assert download.content == PDF and "attachment" in download.headers["content-disposition"]
    assert len({key for key in storage.objects if key.startswith(owners[0] + "/")}) == 2
    assert client.delete(base, headers=identity(0)).status_code == 204
    assert client.get(v1, headers=identity(0)).status_code == 404
    assert client.get("/api/v1/career/evidence", headers=identity(0)).json() == []
    assert len(storage.objects) == 1 and next(iter(storage.objects)).startswith(owners[1] + "/")


@pytest.mark.parametrize(("content", "filename", "media_type", "status"), [
    (b"plain text", "profile.pdf", "application/pdf", 400),
    (PDF, "profile.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 400),
    (PDF, "profile.pdf", "text/plain", 400),
    (b"%PDF-1.7\nbroken content", "profile.pdf", "application/pdf", 400),
])
def test_rejects_invalid_uploads_without_writing_storage(setup, content, filename, media_type, status):
    client, _, storage, _ = setup
    assert upload(client, content=content, filename=filename, media_type=media_type).status_code == status
    assert storage.objects == {}
    assert client.get(PREFIX, headers=identity(0)).json() == []


def test_scanned_export_records_limits_without_proposing_claims(setup):
    client, _, storage, _ = setup
    response = upload(client, content=(FIXTURES / "scanned.pdf").read_bytes())
    assert response.status_code == 201
    document = response.json()["document"]
    assert document["parse_status"] == "unreadable" and document["coverage"] == "uploaded_export_only"
    assert document["raw_text"] == "" and "experience" in document["not_found_in_export"]
    assert client.get("/api/v1/career/evidence", headers=identity(0)).json() == []
    assert upload(client, content=(FIXTURES / "over-page-limit.pdf").read_bytes()).status_code == 422
    assert len(storage.objects) == 1


def test_failed_storage_operations_keep_owner_cleanup_paths(setup, monkeypatch):
    client, engine, storage, owners = setup
    put, remove = storage.upload, storage.delete

    def interrupted_upload(*args):
        put(*args)
        raise StorageUploadError("Synthetic private provider body")

    monkeypatch.setattr(storage, "upload", interrupted_upload)
    response = upload(client)
    assert response.status_code == 503 and "provider body" not in response.text
    assert len(storage.objects) == 1
    [pending] = client.get(PREFIX, headers=identity(0)).json()
    base = f"{PREFIX}/{pending['source']['source_id']}"
    assert pending["state"] == "pending"
    assert client.get(base + "/versions/1/pdf", headers=identity(0)).status_code == 404
    assert client.get("/api/v1/career/evidence", headers=identity(0)).json() == []

    def interrupted_delete(_path):
        raise StorageDeleteError("Synthetic delete outage")

    monkeypatch.setattr(storage, "delete", interrupted_delete)
    assert client.delete(base, headers=identity(0)).status_code == 503
    assert client.get(PREFIX, headers=identity(0)).json()[0]["state"] == "canceling"
    if engine.dialect.name == "postgresql":
        with pytest.raises(DBAPIError), engine.begin() as db:
            db.execute(text("DELETE FROM users WHERE user_id = :id"), {"id": owners[0]})
    monkeypatch.setattr(storage, "delete", remove)
    assert client.delete(base, headers=identity(0)).status_code == 204
    assert storage.objects == {}
    assert client.get(PREFIX, headers=identity(0)).json() == []


@pytest.mark.postgres
def test_concurrent_appends_publish_one_version(setup):
    client, _, storage, _ = setup
    response = upload(client)
    assert response.status_code == 201
    source_id = response.json()["source"]["source_id"]
    path = f"{PREFIX}/{source_id}/versions/1"
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: upload(client, path=path).status_code, range(2)))
    assert sorted(outcomes) == [201, 409]
    assert len(storage.objects) == 2
    assert sorted(row["source"]["source_version"] for row in client.get(PREFIX, headers=identity(0)).json()) == [1, 2]


def test_busy_storage_capacity_leaves_other_histories_available(setup, monkeypatch):
    client, _, storage, _ = setup
    first = upload(client)
    assert first.status_code == 201
    base = f"{PREFIX}/{first.json()['source']['source_id']}"
    slots = BoundedSemaphore(1)
    monkeypatch.setattr(linkedin_pdf_service, "_STORAGE_MUTATIONS", slots, raising=False)
    assert slots.acquire(blocking=False)
    try:
        assert upload(client, owner=1).status_code == 503
        assert client.delete(base, headers=identity(0)).status_code == 503
        assert client.get(PREFIX, headers=identity(1)).json() == []
        assert client.get(base + "/versions/1/pdf", headers=identity(0)).content == PDF
        assert len(storage.objects) == 1
    finally:
        slots.release()
    assert client.delete(base, headers=identity(0)).status_code == 204


@pytest.mark.postgres
@pytest.mark.parametrize("operation", ["upload", "delete"])
def test_busy_history_reports_conflict_without_waiting_on_storage(setup, monkeypatch, operation):
    client, engine, storage, _ = setup
    first = upload(client)
    assert first.status_code == 201
    base = f"{PREFIX}/{first.json()['source']['source_id']}"
    started, finish = Event(), Event()
    real_operation = getattr(storage, operation)

    def slow_operation(*args):
        started.set()
        assert finish.wait(10)
        return real_operation(*args)

    def remove():
        return client.delete(base, headers=identity(0))

    monkeypatch.setattr(storage, operation, slow_operation)
    with ThreadPoolExecutor(max_workers=2) as pool:
        active = pool.submit(upload, client, path=base + "/versions/1") if operation == "upload" else pool.submit(remove)
        try:
            assert started.wait(5)
            assert pool.submit(remove).result(timeout=3).status_code == 409
            assert engine.pool.checkedout() == 1
            assert client.get(PREFIX, headers=identity(1)).json() == []
        finally:
            finish.set()
        assert active.result().status_code == (201 if operation == "upload" else 204)


@pytest.mark.postgres
def test_append_and_download_release_reads_before_external_work(setup, monkeypatch):
    client, engine, storage, _ = setup
    first = upload(client)
    assert first.status_code == 201
    path = f"{PREFIX}/{first.json()['source']['source_id']}/versions/1"
    parse, download = linkedin_pdf.read_profile_pages, storage.download
    checked_out = {}

    async def parse_without_connection(content):
        checked_out["parse"] = engine.pool.checkedout()
        return await parse(content)

    def download_without_connection(key):
        checked_out["download"] = engine.pool.checkedout()
        return download(key)

    monkeypatch.setattr(linkedin_pdf, "read_profile_pages", parse_without_connection)
    monkeypatch.setattr(storage, "download", download_without_connection)
    assert upload(client, path=path).status_code == 201
    assert client.get(path + "/pdf", headers=identity(0)).content == PDF
    assert checked_out == {"parse": 0, "download": 0}


@pytest.mark.postgres
def test_snapshot_ciphertext_and_api_role_grants(setup):
    client, engine, _, _ = setup
    assert upload(client).status_code == 201
    with engine.connect() as db:
        assert db.scalar(text("SELECT content FROM career_sources WHERE kind='linkedin_profile_pdf'")) == ""
        assert "Alex Example" not in db.scalar(text("SELECT document_ciphertext FROM linkedin_pdf_uploads"))
        assert db.scalar(text("SELECT relrowsecurity FROM pg_class WHERE oid='linkedin_pdf_uploads'::regclass"))
        assert db.scalar(text("""
            SELECT count(*) FROM pg_roles WHERE rolname IN ('authenticated','anon','service_role')
            AND has_table_privilege(oid, 'linkedin_pdf_uploads', 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE')
        """)) == 0
    with pytest.raises(DBAPIError, match="immutable"), engine.begin() as db:
        db.execute(text("UPDATE linkedin_pdf_uploads SET document_ciphertext = 'changed'"))
    # Rehearse the documented grants and RLS policy for a restricted web login.
    with engine.connect() as db, db.begin() as tx:
        db.exec_driver_sql("""
            CREATE ROLE pri46_test_runtime NOLOGIN NOBYPASSRLS;
            GRANT USAGE ON SCHEMA public TO pri46_test_runtime;
            GRANT SELECT, INSERT, UPDATE, DELETE ON linkedin_pdf_uploads TO pri46_test_runtime;
            CREATE POLICY prismpro_linkedin_pdf_runtime ON linkedin_pdf_uploads
                FOR ALL TO pri46_test_runtime USING (true) WITH CHECK (true);
            SET LOCAL ROLE pri46_test_runtime;
        """)
        assert db.scalar(text("SELECT count(*) FROM linkedin_pdf_uploads")) == 1
        assert db.execute(text("UPDATE linkedin_pdf_uploads SET state = 'deleting'")).rowcount == 1
        assert db.execute(text("DELETE FROM linkedin_pdf_uploads")).rowcount == 1
        tx.rollback()


@pytest.mark.postgres
def test_existing_storage_policy_and_empty_schema_rollback(migrated_database):
    engine, config = migrated_database
    previous = "2026_11_18_evidence_measurement"
    command.upgrade(config, previous)
    with engine.begin() as db:
        db.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN CREATE ROLE anon; END IF;
            END $$;
            CREATE SCHEMA storage;
            CREATE TABLE storage.buckets (id text PRIMARY KEY, public boolean);
            CREATE TABLE storage.objects (bucket_id text, name text);
            INSERT INTO storage.buckets VALUES ('resume', false);
            INSERT INTO storage.objects VALUES ('resume', 'owner/resume.pdf'), ('resume', 'owner/linkedin-test.pdf');
            ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;
            CREATE POLICY test_owner_grant ON storage.objects FOR SELECT TO authenticated USING (true);
            GRANT USAGE ON SCHEMA storage TO authenticated;
            GRANT SELECT ON storage.objects TO authenticated;
        """))
    command.upgrade(config, "head")
    with engine.begin() as db:
        db.execute(text("SET LOCAL ROLE authenticated"))
        assert db.execute(text("SELECT name FROM storage.objects")).scalars().all() == ["owner/resume.pdf"]
    command.downgrade(config, previous)
    with engine.connect() as db:
        assert db.scalar(text("SELECT to_regclass('public.linkedin_pdf_uploads')")) is None
    command.upgrade(config, "head")



@pytest.mark.parametrize(("employment", "header"), [
    (None, ["Boston, Massachusetts"]),
    ("Full-time", ["Boston, Massachusetts"]),
    ("Full-time", ["São Paulo, Brazil"]),
    ("Full-time", ["West Java"]),
    ("Full-time", ["Boston, Massachusetts", "github.com/candidate"]),
])
def test_realistic_experience_and_invalid_optional_profile_link(setup, employment, header):
    client, _, _, _ = setup
    pdf = fitz.open()
    page = pdf.new_page()
    lines = [
        "Contact", "https://linkedin.com:99999/in/alex", "Top Skills", "Python",
        "Alex Example", "Platform Engineer", *header,
        "Experience", "Senior Engineer", f"Example Labs · {employment}" if employment else "Example Labs",
        "January 2022 - Present (2 years 3 months)", "Boston, Massachusetts",
        "Built a data validation tool.", "Documented the rollout with the team.",
        "Education", "Example University",
    ]
    for index, line in enumerate(lines[:4]):
        page.insert_text((25, 30 + index * 22), line, fontsize=8)
    for index, line in enumerate(lines[4:]):
        page.insert_text((212, 30 + index * 22), line)
    response = upload(client, content=pdf.tobytes())
    assert response.status_code == 201
    document = response.json()["document"]
    assert document["profile_url"] is None
    assert document["name"] == "Alex Example"
    assert [section["text"] for section in document["sections"] if section["name"] == "headline"] == ["Platform Engineer"]
    assert [section["text"] for section in document["sections"] if section["name"] == "skills"] == ["Python"]
    [role] = document["experience"]
    assert role["title"] == "Senior Engineer" and role["company"] == "Example Labs"
    assert role["employment_type"] == employment
    assert role["start_date"] == "January 2022" and role["end_date"] == "Present"
    assert role["location"] == "Boston, Massachusetts"
    assert role["description"] == "Built a data validation tool.\nDocumented the rollout with the team."
    assert all(item["lifecycle"] == "proposed"
               for item in client.get("/api/v1/career/evidence", headers=identity(0)).json())


def test_upload_pause_preserves_existing_history_and_cleanup(setup, monkeypatch):
    client, _, storage, _ = setup
    first = upload(client)
    assert first.status_code == 201
    source_id = first.json()["source"]["source_id"]
    base = f"{PREFIX}/{source_id}"
    monkeypatch.setattr(settings, "LINKEDIN_PDF_UPLOADS_ENABLED", False)
    assert upload(client).status_code == 503
    assert upload(client, path=base + "/versions/1").status_code == 503
    assert client.get(base + "/versions/1/pdf", headers=identity(0)).content == PDF
    assert client.delete(base, headers=identity(0)).status_code == 204
    assert not storage.objects



def test_delete_keeps_cleanup_path_when_upload_completes_late(setup, monkeypatch):
    client, _, storage, _ = setup
    upload_late = []

    def timeout(user, file_id, content, filename):
        upload_late.append((f"{user}/{file_id}.pdf", content))
        raise StorageUploadError("Synthetic timeout before provider commit")

    monkeypatch.setattr(storage, "upload", timeout)
    assert upload(client).status_code == 503
    [pending] = client.get(PREFIX, headers=identity(0)).json()
    base = f"{PREFIX}/{pending['source']['source_id']}"
    assert client.delete(base, headers=identity(0)).status_code == 503
    assert client.get(base + "/versions/1/pdf", headers=identity(0)).status_code == 404
    storage.objects.update(upload_late)
    assert client.delete(base, headers=identity(0)).status_code == 204
    assert not storage.objects



@pytest.mark.postgres
def test_review_reads_owned_sources_and_rechecks_the_live_evidence_revision(setup):
    client, engine, _, (owner, other) = setup
    uploaded = upload(client)
    assert uploaded.status_code == 201
    source = SourceRef.model_validate(uploaded.json()["source"])
    with Session(engine) as db:
        target_fields = CareerTargetInput(role_family="Platform Engineer", seniority="Senior")
        target = CareerApplicationService(db, owner).create_target(target_fields)
        other_target = CareerApplicationService(db, other).create_target(target_fields)
        review = LinkedInReviewService(db, owner)
        foreign = LinkedInReviewService(db, other)
        with pytest.raises(ResourceNotFoundError):
            foreign.review(source, target.target_id, evidence_snapshot_version=1)
        with pytest.raises(ResourceNotFoundError):
            foreign.review(source, other_target.target_id, evidence_snapshot_version=1)

        ledger = EvidenceService(db, owner)
        [extracted, *_] = ledger.list()
        draft = ledger.propose(EvidenceProposal(
            claim=extracted.claim, category="action", ownership="individual",
            sources=[{**source.model_dump(), "relationship": "supports", "locator": "placeholder",
                      "excerpt": extracted.claim, "extraction": "candidate"}],
        ))
        assert review.recommendation_blocker(draft, draft.claim) == "evidence_not_confirmed"
        assert any(f.kind == "unsupported_claim" for f in review.review(
            source, target.target_id, evidence_snapshot_version=1,
        ).findings)
        confirmed = ledger.decide(draft.evidence_id, EvidenceDecisionInput(revision=1, action="confirm"))
        ref = EvidenceRevisionRef(evidence_id=confirmed.evidence_id, revision=confirmed.revision)
        assert review.recommendation_blocker(ref, confirmed.claim) is None
        assert foreign.recommendation_blocker(ref, confirmed.claim) == "evidence_not_confirmed"
        ledger.decide(draft.evidence_id, EvidenceDecisionInput(revision=2, action="mark_private"))
        assert review.recommendation_blocker(ref, confirmed.claim) == "evidence_not_confirmed"


@pytest.mark.postgres
def test_review_preview_is_private_and_uses_owned_ready_revisions(setup):
    client, engine, _, (owner, other) = setup
    uploaded = upload(client)
    assert uploaded.status_code == 201
    source = uploaded.json()["source"]
    base = f"{PREFIX}/{source['source_id']}"
    path = base + "/versions/1/review"
    with Session(engine) as db:
        fields = CareerTargetInput(role_family="Platform Engineer", seniority="Senior")
        career = CareerApplicationService(db, owner)
        target = career.create_target(fields)
        archived = career.create_target(fields)
        career.archive_target(archived.target_id)
        foreign_target = CareerApplicationService(db, other).create_target(fields)

    body = {"target_id": target.target_id}
    assert client.post(path, json=body).status_code == 401
    preview = client.post(path, headers=identity(0), json=body)
    assert preview.status_code == 200
    assert preview.headers["cache-control"] == "no-store"
    data = preview.json()
    assert set(data) == {"schema_version", "document", "target_id", "parser_version", "findings"}
    assert data["document"] == source and data["target_id"] == target.target_id
    assert {finding["kind"] for finding in data["findings"]} >= {"document_limit", "unsupported_claim"}
    assert all(finding["document_locator"] for finding in data["findings"])
    assert "Alex Example" not in preview.text

    for account, target_id in (
        (1, target.target_id), (1, foreign_target.target_id),
        (0, foreign_target.target_id), (0, archived.target_id),
    ):
        assert client.post(path, headers=identity(account), json={"target_id": target_id}).status_code == 404
    assert client.post(path, headers=identity(0), json=body | {"resume_source": source}).status_code == 404
    assert client.post(path, headers=identity(0), json=body | {"evidence_snapshot_version": 5}).status_code == 422
    assert client.delete(base, headers=identity(0)).status_code == 204
    assert client.post(path, headers=identity(0), json=body).status_code == 404


@pytest.mark.postgres
def test_review_preview_cites_owned_resume_and_exact_pdf_version(setup):
    client, engine, _, (owner, _) = setup
    uploaded = upload(client)
    assert uploaded.status_code == 201
    document = uploaded.json()["document"]
    [role, *_] = document["experience"]
    base = f"{PREFIX}/{document['source']['source_id']}/versions"
    assert upload(client, path=f"{base}/1", content=(FIXTURES / "simple.pdf").read_bytes()).status_code == 201

    resume_id = str(uuid4())
    with Session(engine) as db:
        db.add(ResumeDocument(
            id=resume_id, user_id=owner, original_filename="synthetic.pdf", file_path="synthetic",
            file_type="pdf", raw_text="Synthetic résumé specimen",
            parsed_json={
                "contact": {"name": "Synthetic résumé specimen"},
                "raw_text": "Synthetic résumé specimen",
                "experience": [{"company": role["company"], "role": "Different title", "dates": "2018 - 2021"}],
            },
        ))
        db.commit()
        career = CareerApplicationService(db, owner)
        target = career.create_target(CareerTargetInput(role_family="Platform Engineer", seniority="Senior"))
        resume = career.add_source(CareerSourceCreate(kind="resume", resume_document_id=resume_id)).source

    body = {"target_id": target.target_id, "resume_source": resume.model_dump()}
    first = client.post(f"{base}/1/review", headers=identity(0), json=body)
    second = client.post(f"{base}/2/review", headers=identity(0), json=body)
    assert first.status_code == second.status_code == 200
    assert first.json()["document"] == document["source"]
    assert second.json()["document"] == document["source"] | {"source_version": 2}
    [question] = [finding for finding in first.json()["findings"] if finding["kind"] == "consistency_question"]
    assert question["resume_source"] == resume.model_dump()
    assert question["resume_locator"] == "experience:0"
    assert not any(finding["kind"] == "consistency_question" for finding in second.json()["findings"])


@pytest.mark.postgres
def test_target_picker_is_authenticated_bounded_and_owner_scoped(setup):
    client, engine, _, (owner, _) = setup
    fields = {"role_family": "Platform Engineer", "seniority": "Senior", "desired_work": ["Python"]}
    assert client.get(TARGETS).status_code == 401
    assert client.post(TARGETS, json=fields).status_code == 401
    assert client.post(TARGETS, headers=identity(1), json=fields | {"owner_id": owner}).status_code == 422
    foreign = client.post(TARGETS, headers=identity(1), json=fields)
    assert foreign.status_code == 201
    with Session(engine) as db:
        career = CareerApplicationService(db, owner)
        archived = career.create_target(CareerTargetInput(**fields))
        career.archive_target(archived.target_id)
    owned = client.post(TARGETS, headers=identity(0), json=fields)
    assert owned.status_code == 201 and owned.json()["owner_id"] == owner
    assert owned.headers["cache-control"] == "no-store"
    page = client.get(TARGETS, headers=identity(0), params={"limit": 1})
    assert page.headers["cache-control"] == "no-store" and page.json() == [owned.json()]
    assert client.get(TARGETS, headers=identity(0), params={"offset": 1}).json() == []
    assert client.get(TARGETS, headers=identity(0), params={"limit": 101}).status_code == 422


@pytest.mark.postgres
def test_target_coverage_reads_current_owned_evidence_without_mutation(setup):
    client, engine, _, (owner, other) = setup
    with Session(engine) as db:
        career = CareerApplicationService(db, owner)
        target = career.create_target(CareerTargetInput(
            role_family="Platform Engineer", seniority="Senior", desired_work=["Python", "Ruby"],
        ))
        alternative = career.create_target(CareerTargetInput(
            role_family="Data Engineer", seniority="Senior", desired_work=["Ruby"],
        ))
        foreign = CareerApplicationService(db, other).create_target(CareerTargetInput(
            role_family="Platform Engineer", seniority="Senior", desired_work=["Python"],
        ))
        claim = "Used Python to build a deployment service."
        source = career.add_source(CareerSourceCreate(kind="candidate_introduction", content=claim))
        ledger = EvidenceService(db, owner)
        proposed = ledger.propose(EvidenceProposal(
            claim=claim, category="action", ownership="individual",
            sources=[{**source.source.model_dump(), "relationship": "supports", "locator": "placeholder",
                      "excerpt": claim, "extraction": "candidate"}],
        ))
        confirmed = ledger.decide(proposed.evidence_id, EvidenceDecisionInput(revision=1, action="confirm"))
        before = ledger.list()

    path = f"{TARGETS}/{target.target_id}/coverage"
    response = client.get(path, headers=identity(0))
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    assert response.json()["target_id"] == target.target_id
    [python, ruby] = response.json()["focus"]
    assert python["state"] == "supported" and python["reason_code"] == "confirmed_application"
    assert python["evidence"] == {"evidence_id": confirmed.evidence_id, "revision": confirmed.revision}
    assert ruby["state"] == "experience_gap" and ruby["evidence"] is None
    assert claim not in response.text
    assert client.get(path).status_code == 401
    assert client.get(path, headers=identity(1)).status_code == 404
    assert client.get(f"{TARGETS}/{foreign.target_id}/coverage", headers=identity(0)).status_code == 404
    assert client.get(f"{TARGETS}/{alternative.target_id}/coverage", headers=identity(0)).json()["focus"] == [ruby]
    assert client.get(path, headers=identity(0)).content == response.content
    with Session(engine) as db:
        ledger = EvidenceService(db, owner)
        assert ledger.list() == before
        edited = ledger.decide(confirmed.evidence_id, EvidenceDecisionInput(
            revision=confirmed.revision, action="edit", claim="I am learning Python.",
        ))
        learned = ledger.decide(edited.evidence_id, EvidenceDecisionInput(revision=edited.revision, action="confirm"))
        assert learned.category == "action"
    learning = client.get(path, headers=identity(0)).json()["focus"][0]
    assert learning["state"] == "knowledge_gap" and learning["reason_code"] == "learning_only"
    assert learning["evidence"] == {"evidence_id": learned.evidence_id, "revision": learned.revision}
    with Session(engine) as db:
        EvidenceService(db, owner).decide(learned.evidence_id, EvidenceDecisionInput(
            revision=learned.revision, action="mark_private",
        ))
    assert client.get(path, headers=identity(0)).json()["focus"][0]["evidence"] is None
    with Session(engine) as db:
        CareerApplicationService(db, owner).archive_target(target.target_id)
    assert client.get(path, headers=identity(0)).status_code == 404


@pytest.mark.postgres
def test_target_resume_comparison_is_read_only_and_owner_scoped(setup):
    client, engine, _, (owner, other) = setup
    claim = "Used Python to build a deployment service."
    parsed = {
        "contact": {"name": "Synthetic candidate"},
        "raw_text": claim,
        "experience": [{"company": claim, "role": "Engineer", "bullets": [
            {"id": "unrelated", "text": "Maintained build scripts.", "raw_text": "Maintained build scripts."},
        ]}],
    }
    with Session(engine) as db:
        career = CareerApplicationService(db, owner)
        target = career.create_target(CareerTargetInput(
            role_family="Platform Engineer", seniority="Senior", desired_work=["Python", "Rust"],
        ))
        source = career.add_source(CareerSourceCreate(kind="candidate_introduction", content=claim))
        ledger = EvidenceService(db, owner)
        proposed = ledger.propose(EvidenceProposal(
            claim=claim, category="action", ownership="individual",
            sources=[{**source.source.model_dump(), "relationship": "supports", "locator": "placeholder",
                      "excerpt": claim, "extraction": "candidate"}],
        ))
        confirmed = ledger.decide(proposed.evidence_id, EvidenceDecisionInput(revision=1, action="confirm"))
        before = ledger.list()
        resume_ids = [str(uuid4()) for _ in range(4)]
        for resume_id, user_id, state, document in zip(
            resume_ids,
            (owner, other, owner, owner),
            ("ready", "ready", "pending", "ready"),
            (parsed, parsed, parsed, parsed | {"experience": []}),
        ):
            db.add(ResumeDocument(
                id=resume_id, user_id=user_id, original_filename="synthetic.pdf", file_path="synthetic",
                file_type="pdf", storage_status=state, raw_text=claim, parsed_json=document,
            ))
        db.commit()

    coverage_path = f"{TARGETS}/{target.target_id}/coverage"
    own, foreign, pending, limited = [f"{coverage_path}/resume/{value}" for value in resume_ids]
    headers = identity(0)
    response = client.get(own, headers=headers)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    assert response.json()["resume_document_id"] == resume_ids[0]
    assert response.json()["coverage"] == client.get(coverage_path, headers=headers).json()
    [finding] = response.json()["findings"]
    assert (finding["kind"], finding["reason_code"], finding["focus_label"]) == (
        "communication_gap", "confirmed_application_not_found_in_resume", "Python",
    )
    assert finding["evidence"] == {"evidence_id": confirmed.evidence_id, "revision": confirmed.revision}
    assert claim not in response.text and "Maintained build scripts." not in response.text
    assert client.get(own, headers=headers).content == response.content
    assert client.get(own).status_code == 401
    assert client.get(own, headers=identity(1)).status_code == 404

    missing = client.get(f"{coverage_path}/resume/{uuid4()}", headers=headers)
    for inaccessible in (foreign, pending):
        result = client.get(inaccessible, headers=headers)
        assert result.status_code == missing.status_code == 404
        assert result.headers["cache-control"] == "no-store"
        assert result.json()["message"] == missing.json()["message"]

    limited_response = client.get(limited, headers=headers)
    assert limited_response.status_code == 200
    [limit] = limited_response.json()["findings"]
    assert (limit["kind"], limit["reason_code"], limit["evidence"]) == (
        "document_limit", "resume_comparable_bullets_unavailable", None,
    )

    with Session(engine) as db:
        ledger = EvidenceService(db, owner)
        assert ledger.list() == before
        ledger.decide(confirmed.evidence_id, EvidenceDecisionInput(revision=confirmed.revision, action="mark_private"))
    assert client.get(own, headers=headers).json()["findings"] == []


@pytest.mark.postgres
def test_recommendations_copy_checks_current_evidence_and_review_scope(setup):
    client, engine, _, (owner, other) = setup
    [own_pdf, other_pdf] = [upload(client, account).json()["source"]["source_id"] for account in (0, 1)]
    fields = {"role_family": "Platform Engineer", "seniority": "Senior", "desired_work": ["Python"]}
    own_target = client.post(TARGETS, headers=identity(0), json=fields)
    other_target = client.post(TARGETS, headers=identity(1), json=fields)
    assert own_target.status_code == other_target.status_code == 201
    target_id = own_target.json()["target_id"]
    foreign_target = other_target.json()["target_id"]
    path = f"{PREFIX}/{own_pdf}/versions/1/recommendations"
    copy = path + "/copy"

    def add_evidence(db, account, claim, category="action", *, confirm=True, ownership="individual"):
        source = CareerApplicationService(db, account).add_source(CareerSourceCreate(
            kind="candidate_introduction", content=claim,
        ))
        ledger = EvidenceService(db, account)
        item = ledger.propose(EvidenceProposal(
            claim=claim, category=category, ownership=ownership,
            sources=[{**source.source.model_dump(), "relationship": "supports", "locator": "placeholder",
                      "excerpt": claim, "extraction": "candidate"}],
        ))
        return ledger.decide(item.evidence_id, EvidenceDecisionInput(revision=1, action="confirm")) if confirm else item

    def reference(item):
        return {"evidence_id": item.evidence_id, "revision": item.revision}

    with Session(engine) as db:
        action = add_evidence(db, owner, "Used Python to build a deployment service.")
        skill = add_evidence(db, owner, "Python", "skill")
        unused = add_evidence(db, owner, "Kubernetes", "skill")
        add_evidence(db, owner, "Led a team of 27 engineers.")
        add_evidence(db, owner, "Built a Rust compiler.", ownership="team")
        proposed = add_evidence(db, owner, "Built an Ada parser.", confirm=False)
        foreign = add_evidence(db, other, "Built a Java deployment service.")

    body = {"target_id": target_id}
    assert client.post(path, json=body).status_code == 401
    assert client.post(path, headers=identity(0), json={"target_id": foreign_target}).status_code == 404
    assert client.post(path, headers=identity(1), json={"target_id": foreign_target}).status_code == 404
    response = client.post(path, headers=identity(0), json=body)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    suggestions = {item["section"]: item for item in response.json()}
    assert set(suggestions) == {"headline", "about", "experience", "skills"}
    for section in ("headline", "about", "experience"):
        assert suggestions[section]["text"] == action.claim
        assert suggestions[section]["evidence_revisions"] == [reference(action)]
    assert suggestions["skills"]["text"] == skill.claim
    assert suggestions["skills"]["evidence_revisions"] == [reference(skill), reference(action)]

    selection = {"section": "skills", "evidence_revisions": [reference(skill), reference(action)]}
    copied = client.post(copy, headers=identity(0), json=body | {"selection": selection})
    assert copied.status_code == 200 and copied.json() == suggestions["skills"]
    assert copied.headers["cache-control"] == "no-store"
    blocked = {"section": "skills", "evidence_revisions": [reference(unused), reference(action)]}
    assert client.post(copy, headers=identity(0), json=body | {"selection": blocked}).status_code == 409
    for item in (proposed, foreign):
        invalid = {"section": "about", "evidence_revisions": [reference(item)]}
        assert client.post(copy, headers=identity(0), json=body | {"selection": invalid}).status_code == 409
    assert client.post(copy, headers=identity(0), json=body | {"selection": selection | {"text": "Injected"}}).status_code == 422
    assert client.post(f"{PREFIX}/{other_pdf}/versions/1/recommendations/copy", headers=identity(0),
                       json=body | {"selection": selection}).status_code == 404

    with Session(engine) as db:
        EvidenceService(db, owner).decide(action.evidence_id, EvidenceDecisionInput(revision=2, action="mark_private"))
    assert client.post(copy, headers=identity(0), json=body | {"selection": selection}).status_code == 409
    assert client.post(path, headers=identity(0), json=body).json() == []
    assert client.delete(f"{PREFIX}/{own_pdf}", headers=identity(0)).status_code == 204
    assert client.post(copy, headers=identity(0), json=body | {"selection": selection}).status_code == 404
