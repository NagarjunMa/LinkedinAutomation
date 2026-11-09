"""Exercise the profile API against PostgreSQL created by release migrations."""

from uuid import uuid4

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.core import auth
from app.db.session import get_db
from app.main import app
from app.models.resume_document import ResumeDocument


pytestmark = pytest.mark.postgres
PREVIOUS_HEAD = "2026_11_09_monthly_credits"


@pytest.fixture
def owned_profile(migrated_database, monkeypatch):
    engine, _ = migrated_database
    owner = str(uuid4())
    headers = {"Authorization": "Bearer synthetic-test-token"}
    monkeypatch.setattr(auth, "decode_supabase_jwt", lambda _: {"sub": owner})

    def database_session():
        with Session(engine, autoflush=False) as session:
            yield session

    monkeypatch.setitem(app.dependency_overrides, get_db, database_session)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, owner, headers


def test_clean_migration_supports_owned_profile_api(migrated_database, owned_profile):
    _, config = migrated_database
    command.upgrade(config, "head")
    client, owner, headers = owned_profile
    path = f"/api/v1/user-profiles/{owner}"
    assert client.get(path).status_code == 401
    assert client.get(f"/api/v1/user-profiles/{uuid4()}", headers=headers).status_code == 403
    assert client.post("/api/v1/auth/bootstrap", headers=headers).status_code == 204
    empty = client.get(path, headers=headers)
    assert empty.status_code == 200, empty.text
    assert empty.json()["exists"] is False
    payload = {
        "full_name": "Synthetic Candidate",
        "email": "candidate@example.com",
        "programming_languages": ["Python"],
    }
    created = client.post(path, headers=headers, json=payload)
    assert created.status_code == 200, created.text
    updated = client.put(path, headers=headers, json={"location": "Remote"})
    assert updated.status_code == 200, updated.text
    profile = client.get(path, headers=headers)
    assert profile.status_code == 200, profile.text
    assert profile.json()["full_name"] == payload["full_name"]
    assert profile.json()["programming_languages"] == ["Python"]
    assert profile.json()["location"] == "Remote"


def _access_rules(conn):
    return conn.execute(text("""
        SELECT relrowsecurity, relforcerowsecurity, relacl, roles, cmd, qual, with_check
        FROM pg_class JOIN pg_policies ON schemaname = 'public' AND tablename = relname
        WHERE oid = 'public.user_profiles'::regclass
        ORDER BY policyname
    """)).all()


@pytest.mark.parametrize("partial_schema", [False, True])
def test_existing_schema_preserves_profile_and_access_rules(migrated_database, owned_profile, partial_schema):
    engine, config = migrated_database
    client, owner, headers = owned_profile
    path = f"/api/v1/user-profiles/{owner}"
    command.upgrade(config, PREVIOUS_HEAD)
    with engine.begin() as conn:
        conn.exec_driver_sql("GRANT SELECT ON public.user_profiles TO authenticated")
        access_before = _access_rules(conn)
        assert len(access_before) == 1 and access_before[0].relrowsecurity
        conn.execute(text("INSERT INTO public.user_profiles (user_id) VALUES (:owner)"), {"owner": owner})
        if partial_schema:
            conn.exec_driver_sql("ALTER TABLE public.user_profiles ADD COLUMN full_name varchar(255)")
            conn.exec_driver_sql("UPDATE public.user_profiles SET full_name = 'Saved profile'")
            conn.exec_driver_sql(
                "CREATE UNIQUE INDEX preexisting_profile_owner ON public.user_profiles (user_id)"
            )

    command.upgrade(config, "head")
    command.downgrade(config, PREVIOUS_HEAD)
    command.upgrade(config, "head")
    with engine.connect() as conn:
        row = conn.exec_driver_sql("SELECT user_id, full_name FROM public.user_profiles").one()
        assert row == (owner, "Saved profile" if partial_schema else None)
        assert _access_rules(conn) == access_before
        unique_indexes = [i["name"] for i in inspect(conn).get_indexes("user_profiles") if i["unique"]]
        assert len(unique_indexes) == 1
        if partial_schema:
            assert unique_indexes == ["preexisting_profile_owner"]
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("INSERT INTO public.user_profiles (user_id) VALUES (:owner)"), {"owner": owner})

    assert client.post("/api/v1/auth/bootstrap", headers=headers).status_code == 204
    before = client.get(path, headers=headers)
    assert before.status_code == 200, before.text
    assert before.json()["full_name"] == ("Saved profile" if partial_schema else "")
    parsed_email = "owner@example.invalid" if partial_schema else ""
    if partial_schema:
        with Session(engine) as session:
            session.add(ResumeDocument(
                id=str(uuid4()), user_id=owner, original_filename="synthetic.pdf",
                file_path="unused", file_type="pdf", raw_text="Synthetic resume",
                parsed_json={"contact": {"email": parsed_email}},
            ))
            session.commit()
    preferences = client.put(path, headers=headers, json={"desired_roles": ["Engineer"]})
    assert preferences.status_code == 200, preferences.text
    assert preferences.json()["email"] == parsed_email
    assert preferences.json()["full_name"] == ("Saved profile" if partial_schema else "")
    assert preferences.json()["desired_roles"] == ["Engineer"]
    assert preferences.json()["created_at"]
    saved = client.post(path, headers=headers, json={"full_name": "Completed Profile", "email": "owner@example.com"})
    assert saved.status_code == 200, saved.text
    assert saved.json()["created_at"] == preferences.json()["created_at"]
    updated = client.put(path, headers=headers, json={"location": "Remote"})
    assert updated.status_code == 200, updated.text
    assert updated.json()["created_at"] == saved.json()["created_at"]


def test_duplicate_owners_abort_without_partial_schema_changes(migrated_database):
    engine, config = migrated_database
    command.upgrade(config, PREVIOUS_HEAD)
    with engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO public.user_profiles (user_id) VALUES ('test'), ('test')")
    with pytest.raises(DBAPIError, match="duplicate owners"):
        command.upgrade(config, "head")
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT count(*) FROM public.user_profiles").scalar_one() == 2
        assert conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one() == PREVIOUS_HEAD
        assert {col["name"] for col in inspect(conn).get_columns("user_profiles")} == {"id", "user_id"}


def test_incompatible_existing_column_aborts_without_coercion(migrated_database):
    engine, config = migrated_database
    command.upgrade(config, PREVIOUS_HEAD)
    with engine.begin() as conn:
        conn.exec_driver_sql("ALTER TABLE public.user_profiles ADD COLUMN full_name integer")
        conn.exec_driver_sql("INSERT INTO public.user_profiles (user_id, full_name) VALUES ('test', 42)")
    with pytest.raises(RuntimeError, match="Incompatible existing user_profiles column: full_name"):
        command.upgrade(config, "head")
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT full_name FROM public.user_profiles").scalar_one() == 42
        assert conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one() == PREVIOUS_HEAD
