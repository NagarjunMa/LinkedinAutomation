"""Exercise retries, restart recovery and ownership on migrated PostgreSQL."""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from queue import Queue
from threading import Barrier
from time import monotonic, sleep
from uuid import uuid4

import pytest
from alembic import command
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.application.career_service import CareerApplicationService
from app.application.errors import ExternalServiceError, ResourceConflictError, ResourceNotFoundError
from app.application.interview_service import InterviewService
from app.core import auth
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.schemas.career.interview_persistence import MessageInput, SessionInput
from app.schemas.career.persistence import CareerTargetInput
from app.models.user import User

pytestmark = pytest.mark.postgres


@pytest.fixture(autouse=True)
def transcript_key(monkeypatch):
    key = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv("CAREER_TRANSCRIPT_KEY", key)
    monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", SecretStr(key))
    return key


def test_transcript_key_is_required_for_writes_and_for_reading_prior_messages(
    migrated_database, monkeypatch, transcript_key,
):
    engine, config = migrated_database
    command.upgrade(config, "head")
    owner = str(uuid4())
    # Exercise the longest allowed message at four UTF-8 bytes per character.
    payload = MessageInput(key="first", content="🚀" * 4000)
    with Session(engine) as db:
        db.add(User(user_id=owner))
        db.commit()
        interview = InterviewService(db, owner)
        state = interview.create(SessionInput(mode="foundation"))
        for bad_key in (None, SecretStr("invalid")):
            monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", bad_key)
            with pytest.raises(ExternalServiceError, match="storage is unavailable"):
                interview.append(state.session_id, payload)
            db.rollback()
            assert interview.get(state.session_id).state_version == 1
            assert interview.messages(state.session_id) == []

        monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", SecretStr(transcript_key))
        saved = interview.append(state.session_id, payload)
        stored = db.scalar(text("SELECT content_ciphertext FROM career_interview_messages"))
        assert Fernet(transcript_key).decrypt(stored).decode("utf-8") == payload.content

        monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", SecretStr(Fernet.generate_key().decode("ascii")))
        with pytest.raises(ExternalServiceError, match="could not be opened"):
            interview.messages(state.session_id)
        with pytest.raises(ExternalServiceError, match="could not be opened"):
            interview.append(state.session_id, payload)
        db.rollback()
        with pytest.raises(ExternalServiceError, match="could not be opened"):
            interview.append(state.session_id, MessageInput(key="new-key", content="Synthetic follow-up"))
        db.rollback()
        monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", SecretStr(transcript_key))
        assert interview.messages(state.session_id) == [saved]
        assert interview.get(state.session_id).state_version == 2


def test_concurrent_retry_and_restart(migrated_database):
    engine, config = migrated_database
    command.upgrade(config, "head")
    owner, other = str(uuid4()), str(uuid4())
    with Session(engine) as db:
        db.add_all([User(user_id=owner), User(user_id=other)])
        db.commit()
        state = InterviewService(db, owner).create(SessionInput(mode="foundation"))
    barrier = Barrier(2)
    payload = MessageInput(key="submission-1", content="I built a synthetic API.")

    def append():
        with Session(engine) as db:
            barrier.wait(timeout=5)
            return InterviewService(db, owner).append(state.session_id, payload)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = [future.result(timeout=10) for future in [pool.submit(append), pool.submit(append)]]
    assert first == second
    engine.dispose()
    restarted = subprocess.run(
        [sys.executable, "-c", '''
import json
import sys
from sqlalchemy.orm import Session
from app.application.interview_service import InterviewService
from app.db.session import engine

with Session(engine) as db:
    service = InterviewService(db, sys.argv[1])
    print(json.dumps([service.get(sys.argv[2]).state_version,
                      [message.model_dump(mode="json") for message in service.messages(sys.argv[2])]]))
''', owner, state.session_id],
        env={**os.environ, "SQLALCHEMY_DATABASE_URI": engine.url.render_as_string(hide_password=False)},
        capture_output=True, text=True, check=True, timeout=10,
    )
    assert json.loads(restarted.stdout) == [2, [first.model_dump(mode="json")]]
    with Session(engine) as db:
        interview = InterviewService(db, owner)
        assert interview.get(state.session_id).state_version == 2
        assert interview.messages(state.session_id) == [first]
        with pytest.raises(ResourceConflictError):
            interview.append(state.session_id, MessageInput(key=payload.key, content="Different input"))
        db.rollback()
        third = interview.append(state.session_id, MessageInput(key="submission-2", content="I wrote tests."))
        assert (first.position, third.position) == (1, 2)
        assert InterviewService(db, other).list_sessions() == []
        with pytest.raises(ResourceNotFoundError):
            InterviewService(db, other).messages(state.session_id)
        with pytest.raises(ResourceNotFoundError):
            InterviewService(db, other).append(state.session_id, payload)


def test_auth_routes_resume_only_owned_interview(migrated_database, monkeypatch, caplog):
    engine, config = migrated_database
    command.upgrade(config, "head")
    owner, other = str(uuid4()), str(uuid4())
    with Session(engine) as db:
        db.add_all([User(user_id=owner), User(user_id=other)])
        db.commit()
        target = CareerApplicationService(db, owner).create_target(CareerTargetInput(
            role_family="Platform", seniority="Senior",
        ))
    identities = {"first": owner, "second": other}
    monkeypatch.setattr(auth, "decode_supabase_jwt", lambda token: {"sub": identities[token]})

    def sessions():
        with Session(engine, autoflush=False) as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, sessions)
    first = {"Authorization": "Bearer first"}
    second = {"Authorization": "Bearer second"}
    path = "/api/v1/career/sessions"
    with TestClient(app) as client:
        assert client.get(path).status_code == 401
        assert client.post(path, headers=second, json={
            "mode": "target_calibration", "target_id": target.target_id,
        }).status_code == 404
        invalid = client.post(path, headers=first, json={"mode": "foundation", "owner_id": "synthetic-private-sentinel"})
        assert invalid.status_code == 422 and "synthetic-private-sentinel" not in invalid.text
        assert "synthetic-private-sentinel" not in caplog.text
        assert client.post(path, headers=first, content=b"x" * 8193).status_code == 413
        created = client.post(path, headers=first, json={"mode": "target_calibration", "target_id": target.target_id})
        assert created.status_code == 201, created.text
        assert created.headers["cache-control"] == "no-store"
        state = created.json()
        detail = f"{path}/{state['session_id']}"
        assert state["owner_id"] == owner
        with Session(engine) as db:
            InterviewService(db, owner).append(state["session_id"], MessageInput(key="first", content="Synthetic answer"))
        with engine.begin() as conn:
            conn.execute(text("UPDATE career_interview_sessions SET status = 'paused' WHERE user_id = :owner"),
                         {"owner": owner})
        assert client.get(path, headers=second).json() == []
        assert client.get(detail, headers=second).status_code == 404
        assert client.get(f"{detail}/messages", headers=second).status_code == 404
        assert client.post(f"{detail}/resume", headers=second).status_code == 404
        resumed = client.post(f"{detail}/resume", headers=first)
        assert resumed.status_code == 200
        assert resumed.json()["status"] == "active"
        assert resumed.json()["state_version"] == 3
        assert client.post(f"{detail}/resume", headers=first).json() == resumed.json()
        assert client.get(f"{detail}/messages", headers=first).json()[0]["content"] == "Synthetic answer"
        with Session(engine) as db:
            CareerApplicationService(db, owner).delete_target(target.target_id)
        detached = client.get(detail, headers=first).json()
        assert detached["target_id"] is None
        assert detached["state_version"] == resumed.json()["state_version"] + 1
        assert datetime.fromisoformat(detached["updated_at"]) >= datetime.fromisoformat(resumed.json()["updated_at"])


def test_interview_rls_immutability_retention_and_safe_downgrade(migrated_database):
    engine, config = migrated_database
    previous = "2026_11_13_career_sources"
    command.upgrade(config, previous)
    owners = (str(uuid4()), str(uuid4()))
    with Session(engine) as db:
        db.add_all(User(user_id=owner) for owner in owners)
        db.commit()
    command.upgrade(config, "head")
    command.downgrade(config, previous)
    assert not inspect(engine).has_table("career_interview_messages")
    command.upgrade(config, "head")
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    with Session(engine) as db:
        for owner in owners:
            service = InterviewService(db, owner)
            state = service.create(SessionInput(mode="foundation"), retention_expires_at=expiry)
            service.append(state.session_id, MessageInput(key="answer", content="Synthetic response"))
    tables = ("career_interview_sessions", "career_interview_messages")
    with engine.begin() as conn:
        for table in tables:
            assert conn.scalar(text("SELECT relrowsecurity FROM pg_class WHERE oid = to_regclass(:name)"), {"name": table})
            assert not conn.scalar(text("SELECT has_table_privilege('authenticated', :table, 'SELECT,UPDATE,TRUNCATE')"),
                                   {"table": table})
        conn.exec_driver_sql("""
            CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE
                AS 'SELECT nullif(current_setting(''request.jwt.claim.sub'', true), '''')::uuid';
            GRANT USAGE ON SCHEMA auth TO authenticated;
            GRANT SELECT ON career_interview_sessions, career_interview_messages TO authenticated;
        """)
    for owner in owners:
        with engine.begin() as conn:
            conn.exec_driver_sql("SET LOCAL ROLE authenticated")
            conn.execute(text("SELECT set_config('request.jwt.claim.sub', :owner, true)"), {"owner": owner})
            for table in tables:
                assert conn.exec_driver_sql(f"SELECT user_id FROM {table}").scalars().all() == [owner]
    with pytest.raises(IntegrityError, match="immutable"), engine.begin() as conn:
        conn.exec_driver_sql("UPDATE career_interview_messages SET content_ciphertext = repeat('x', 100)")
    with pytest.raises(DBAPIError, match="must be preserved"):
        command.downgrade(config, previous)
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            UPDATE career_interview_sessions
            SET created_at = now() - interval '2 days', retention_expires_at = now() - interval '1 day'
        """)
    with Session(engine) as db:
        service = InterviewService(db, owners[-1])
        assert service.list_sessions() == []
        with pytest.raises(ResourceNotFoundError):
            service.messages(state.session_id)
    with engine.begin() as conn:
        conn.exec_driver_sql("SET LOCAL ROLE authenticated")
        conn.execute(text("SELECT set_config('request.jwt.claim.sub', :owner, true)"), {"owner": owners[0]})
        assert conn.exec_driver_sql("SELECT count(*) FROM career_interview_messages").scalar_one() == 0
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE user_id = :owner"), {"owner": owners[0]})
        assert conn.exec_driver_sql("SELECT user_id FROM career_interview_messages").scalars().all() == [owners[1]]


@pytest.mark.parametrize("retry", [False, True])
def test_append_rechecks_retention_after_waiting_for_session_lock(migrated_database, retry):
    engine, config = migrated_database
    command.upgrade(config, "head")
    owner = str(uuid4())
    payload = MessageInput(key="first", content="Synthetic response")
    with Session(engine) as db:
        db.add(User(user_id=owner))
        db.commit()
        service = InterviewService(db, owner)
        state = service.create(SessionInput(mode="foundation"))
        if retry:
            service.append(state.session_id, payload)
    with engine.begin() as conn:
        expiry = conn.exec_driver_sql("""
            UPDATE career_interview_sessions
            SET retention_expires_at = statement_timestamp() + interval '2 seconds'
            RETURNING retention_expires_at
        """).scalar_one()
    writer_pid = Queue()

    def append_message():
        with Session(engine) as db:
            db.execute(text("SET LOCAL statement_timeout = '8s'"))
            writer_pid.put(db.scalar(text("SELECT pg_backend_pid()")))
            return InterviewService(db, owner).append(state.session_id, payload)

    with ThreadPoolExecutor(max_workers=1) as pool:
        with engine.begin() as holder:
            holder_pid = holder.exec_driver_sql("SELECT pg_backend_pid()").scalar_one()
            holder.exec_driver_sql("SELECT id FROM career_interview_sessions FOR UPDATE")
            writer = pool.submit(append_message)
            blocked = writer_pid.get(timeout=2)
            deadline = monotonic() + 2
            while not holder.scalar(text("SELECT :holder = ANY(pg_blocking_pids(:blocked))"),
                                    {"holder": holder_pid, "blocked": blocked}):
                assert monotonic() < deadline, "Append never waited for the session lock"
                sleep(.01)
            assert holder.scalar(text("SELECT statement_timestamp() < :expiry"), {"expiry": expiry})
            holder.execute(text("SELECT pg_sleep(GREATEST(0, EXTRACT(EPOCH FROM :expiry - clock_timestamp())) + 0.02)"),
                           {"expiry": expiry})
        with pytest.raises(ResourceNotFoundError):
            writer.result(timeout=8)
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT count(*) FROM career_interview_messages").scalar_one() == int(retry)
