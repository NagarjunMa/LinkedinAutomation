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
from app.application.evidence_service import EvidenceService
from app.core import auth
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.career import CareerSourceRow, LinkedInPdfUploadRow
from app.models.career_evidence import EvidenceRow, EvidenceSourceRow
from app.models.user import User
from app.schemas.career.evidence import EvidenceRevisionRef
from app.services.storage.exceptions import StorageDeleteError, StorageUploadError
from app.services.storage.supabase_storage import get_storage

PREFIX = "/api/v1/career/linkedin-profiles"
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



@pytest.mark.parametrize("employment", [None, "Full-time"])
def test_realistic_experience_and_invalid_optional_profile_link(setup, employment):
    client, _, _, _ = setup
    pdf = fitz.open()
    page = pdf.new_page()
    lines = [
        "Contact", "https://linkedin.com:99999/in/alex", "Top Skills", "Python",
        "Alex Example", "Platform Engineer", "Boston, Massachusetts",
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
    assert document["location"] == "Boston, Massachusetts"
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
