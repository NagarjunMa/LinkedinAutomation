"""Check actual application and PostgreSQL logs with synthetic transcripts."""
import os
import subprocess
import sys
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4

import pytest
from alembic import command
from cryptography.fernet import Fernet

pytestmark = pytest.mark.postgres


def test_transcript_plaintext_stays_out_of_write_logs(migrated_database):
    log_file = os.getenv("PRI33_TEST_POSTGRES_LOG_FILE")
    container = os.getenv("PRI33_TEST_POSTGRES_CONTAINER")
    if not log_file and not container:
        pytest.skip("requires access to the disposable PostgreSQL server log")

    engine, config = migrated_database
    command.upgrade(config, "head")
    marker = uuid4().hex
    succeeded = f"synthetic-success-{marker}"
    failed = f"synthetic-failure-{marker}"
    result = subprocess.run(
        [sys.executable, "-c", _WRITE_PROBE, marker, succeeded, failed],
        env={
            **os.environ,
            "SQLALCHEMY_DATABASE_URI": engine.url.render_as_string(hide_password=False),
            "DEBUG": "true",
            "CAREER_TRANSCRIPT_KEY": Fernet.generate_key().decode("ascii"),
        },
        capture_output=True, text=True, timeout=20,
    )
    app_log = result.stdout + result.stderr
    if succeeded in app_log or failed in app_log:
        pytest.fail("Transcript appeared in application output")
    assert result.returncode == 0, "The application write probe failed"
    assert "INSERT INTO career_interview_messages" in app_log, "Application SQL logging was not exercised"

    deadline = monotonic() + 5
    while True:
        if log_file:
            postgres_log = Path(log_file).read_text()
        else:
            logs = subprocess.run(["docker", "logs", container], capture_output=True, text=True, timeout=10, check=True)
            postgres_log = logs.stdout + logs.stderr
        entries = postgres_log.splitlines()
        logged_success = any(
            "statement: INSERT INTO career_interview_messages" in line and f"write-ok-{marker}" in line
            for line in entries
        )
        logged_failure = any(
            "STATEMENT:  INSERT INTO career_interview_messages" in line and f"write-failed-{marker}" in line
            for line in entries
        )
        if logged_success and logged_failure:
            break
        assert monotonic() < deadline, "PostgreSQL logs did not capture both write statements"
        sleep(0.05)
    if succeeded in postgres_log or failed in postgres_log:
        pytest.fail("Transcript appeared in PostgreSQL logs")


_WRITE_PROBE = """
import sys

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.application.interview_service import InterviewService
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.career.interview_persistence import MessageInput, SessionInput

marker, succeeded, failed = sys.argv[1:]
with SessionLocal() as db:
    db.add(User(user_id=marker))
    db.commit()
    service = InterviewService(db, marker)
    state = service.create(SessionInput(mode="foundation"))
    db.execute(text("SET LOCAL log_statement = 'all'"))
    message = service.append(state.session_id, MessageInput(key=f"write-ok-{marker}", content=succeeded))
    assert message.content == succeeded
    db.execute(text('''
        CREATE FUNCTION force_transcript_failure() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Synthetic transcript storage failure';
        END;
        $$;
        CREATE TRIGGER force_transcript_failure BEFORE INSERT ON career_interview_messages
        FOR EACH ROW EXECUTE FUNCTION force_transcript_failure();
    '''))
    db.commit()
    db.execute(text("SET LOCAL log_min_error_statement = 'error'"))
    try:
        service.append(state.session_id, MessageInput(key=f"write-failed-{marker}", content=failed))
    except DBAPIError as exc:
        assert exc.orig.pgcode == "P0001"
        print(str(exc))
        db.rollback()
    else:
        raise AssertionError("Expected the synthetic storage failure")
    assert service.messages(state.session_id) == [message]
    assert service.get(state.session_id).state_version == 2
"""
