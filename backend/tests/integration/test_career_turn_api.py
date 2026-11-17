"""Exercise browser-facing turns across the real PostgreSQL transaction boundary."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from threading import Event
from time import sleep
from uuid import uuid4

import httpx
import pytest
from alembic import command
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from openai import AsyncOpenAI
from pydantic import SecretStr
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.api.v1.endpoints import career_interviews
from app.application import interview_turn_service
from app.application.career_model import CareerModelQuote, CareerModelResult
from app.application.interview_service import InterviewService
from app.application.lineage_service import LineageService

from app.core import auth
from app.core.config import settings
from app.core.openai_client import ModelRuntime
from app.db.session import get_db
from app.main import app
from app.models.career_lineage import CareerRunRow
from app.models.interview import InterviewMessageRow
from app.models.user import User
from app.schemas.career.interview import CareerTurnProposal
from app.schemas.career.interview_persistence import MessageInput, TurnInput
from app.schemas.career.lineage import CareerRunManifest, RunMetadata, StoredRun


pytestmark = pytest.mark.postgres
SESSIONS = "/api/v1/career/sessions"
A = {"Authorization": "Bearer owner"}
B = {"Authorization": "Bearer other"}


@pytest.fixture
def api(migrated_database, monkeypatch):
    engine, config = migrated_database
    command.upgrade(config, "head")
    identities = {"owner": str(uuid4()), "other": str(uuid4())}
    with Session(engine) as db:
        db.add_all(User(user_id=value) for value in identities.values())
        db.commit()
    monkeypatch.setattr(auth, "decode_supabase_jwt", lambda token: {"sub": identities[token]})
    monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", SecretStr(Fernet.generate_key().decode()))
    monkeypatch.setattr(settings, "CAREER_TURNS_ENABLED", True)
    monkeypatch.setattr(settings, "CAREER_MODEL_SAFETY_KEY", None)

    def sessions():
        with Session(engine, autoflush=False) as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, sessions)
    with TestClient(app) as client:
        yield client, engine, identities


def create_session(client, headers=A):
    result = client.post(SESSIONS, headers=headers, json={"mode": "foundation", "candidate_stage": "experienced_ic"})
    assert result.status_code == 201, result.text
    return f"{SESSIONS}/{result.json()['session_id']}"


def turn(key="project-1", expected_state_version=1, content="I built a synthetic index."):
    return {"key": key, "content": content, "expected_state_version": expected_state_version}


def events(response):
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-store"
    return [
        (event.removeprefix("event: "), json.loads(data.removeprefix("data: ")))
        for event, data in (frame.splitlines() for frame in response.text.strip().split("\n\n"))
    ]


def test_authenticated_turn_stream_and_reconnect(api):
    client, _, _ = api
    path = create_session(client)
    assert client.post(f"{path}/turns", json=turn()).status_code == 401
    assert client.post(f"{path}/turns", headers=B, json=turn()).status_code == 404
    assert client.get(f"{path}/messages", headers=A).json() == []
    result = events(client.post(f"{path}/turns", headers=A, json=turn()))
    assert [name for name, _ in result] == ["turn.started", "analysis.progress", "assistant.message", "turn.completed"]
    messages = client.get(f"{path}/messages", headers=A).json()
    assert [item["processing_status"] for item in messages] == ["complete", "complete"]
    assert messages[0]["content"] == turn()["content"]
    assert result[2][1]["message"] == messages[1]
    saved = client.get(path, headers=A).json()
    assert saved["chapter"] == "work_project_timeline"
    assert result[-1][1]["state"] == saved
    assert client.get(f"{path}/messages", headers=B).status_code == 404


MANIFEST = CareerRunManifest(
    schema_version=1, provider="synthetic", transport="mock", model_snapshot="model-test",
    prompt_name="test", prompt_version="1", prompt_hash="a" * 64, response_schema_version="turn-v1",
    schema_hash="b" * 64, policy_version="career-interview.v1", max_output_tokens=750, timeout_ms=1000,
)
UNVALIDATED = "UNVALIDATED-SYNTHETIC-PROVIDER-TEXT"
UNLINKED = "PRIVATE-SYNTHETIC-HISTORICAL-TEXT"


class SyntheticModel:
    manifest = MANIFEST

    def __init__(self, on_request=lambda: None, *, malformed=True, transient=False, quote=None):
        self.on_request = on_request
        self.malformed = malformed
        self.transient = transient
        self.reservation = quote or CareerModelQuote(1500, 1000)
        self.requests = []

    def quote(self, _request):
        return self.reservation

    async def propose(self, request):
        self.requests.append(json.loads(request.context))
        await asyncio.to_thread(self.on_request)
        plan = self.requests[-1]["plan"]
        proposal = CareerTurnProposal.model_validate({
            "schema_version": 1, **plan,
            "question": UNVALIDATED if self.malformed else plan["question"],
        })
        return CareerModelResult(run=StoredRun(
            schema_version=1, manifest=self.manifest, metadata=RunMetadata(
                schema_version=1, application_commit="b" * 40, latency_ms=1, input_tokens=12, output_tokens=8,
                failure="model_unavailable" if self.transient else None,
            ),
        ), proposal=None if self.transient else proposal, retryable=self.transient)


def test_invalid_model_output_is_repaired_once_and_only_safe_fallback_is_sent(api, monkeypatch, caplog):
    client, engine, identities = api
    path = create_session(client)
    session_id = path.rsplit("/", 1)[1]
    with Session(engine) as db:
        history = InterviewService(db, identities["owner"]).append(session_id, MessageInput(key="legacy", content=UNLINKED))

    def see_durable_input():
        with Session(engine) as db:
            saved = InterviewService(db, identities["owner"]).messages(session_id)
            assert len(saved) == 2
            assert saved[-1].processing_status == "pending"
            assert saved[-1].content == "I built a synthetic index."

    model = SyntheticModel(see_durable_input)
    monkeypatch.setattr(career_interviews, "_turn_model", lambda: model)
    response = client.post(f"{path}/turns", headers=A, json=turn(expected_state_version=history.position + 1))
    stream = events(response)
    assert len(model.requests) == 2
    assert model.requests[0]["recent_messages"] == [{"role": "user", "content": turn()["content"]}]
    assert model.requests[1]["violations"] == [{"code": "question_out_of_scope", "path": "question"}]
    assert stream[-2][1]["message"]["content"] == "Can you share a specific example of the scope of your role?"
    assert not stream[-1][1]["proposal_validated"]
    assert stream[-1][1]["tokens_reserved"] == 2 * interview_turn_service.ATTEMPT_TOKENS
    assert UNVALIDATED not in (response.text + caplog.text) and UNLINKED not in json.dumps(model.requests)
    with Session(engine) as db:
        records = db.scalars(select(CareerRunRow).where(CareerRunRow.session_id == session_id)).all()
        assert len(records) == 2
        lineage = LineageService(db, identities["owner"])
        runs = [lineage.get_run(record.id) for record in records]
        assert sorted(run.metadata.repair_count for run in runs) == [0, 1]
        assert all(run.metadata.failure == "proposal_rejected" for run in runs)
        assert {run.metadata.start_state for run in runs} == {"active:introduction:v3"}
        assert {run.metadata.end_state for run in runs} == {"active:work_project_timeline:v4"}
        assert all(UNVALIDATED not in record.ciphertext for record in records)


def test_model_quote_above_server_budget_is_never_dispatched(api, monkeypatch):
    client, _, _ = api
    model = SyntheticModel(quote=CareerModelQuote(1000, interview_turn_service.ATTEMPT_COST_MICROUSD + 1))
    monkeypatch.setattr(career_interviews, "_turn_model", lambda: model)
    path = create_session(client)
    response = events(client.post(f"{path}/turns", headers=A, json=turn()))
    assert response[-1][0] == "turn.completed" and response[-1][1]["tokens_reserved"] == 0
    assert model.requests == []
    assert response[-1][1]["state"]["tokens_remaining"] == interview_turn_service.SESSION_TOKENS


def test_rate_limit_and_duplicate_keys_apply_across_sessions(api, monkeypatch):
    client, _, _ = api
    monkeypatch.setattr(interview_turn_service, "DAILY_LIMIT", 2)
    monkeypatch.setattr(interview_turn_service, "SHORT_LIMIT", 1)
    first, second = create_session(client), create_session(client)
    other = create_session(client, B)
    saved = events(client.post(f"{first}/turns", headers=A, json=turn()))[-1][1]["state"]
    duplicate = events(client.post(f"{first}/turns", headers=A, json=turn(expected_state_version=saved["state_version"])))
    assert duplicate[0][0] == "turn.replayed"
    assert client.post(f"{second}/turns", headers=A, json=turn()).status_code == 429
    assert client.get(f"{second}/messages", headers=A).json() == []
    monkeypatch.setattr(interview_turn_service, "SHORT_LIMIT", 10)
    events(client.post(f"{second}/turns", headers=A, json=turn()))
    third = create_session(client)
    assert client.post(f"{third}/turns", headers=A, json=turn()).status_code == 429
    events(client.post(f"{other}/turns", headers=B, json=turn()))


def test_active_turn_blocks_another_session_without_blocking_another_owner(api, monkeypatch):
    client, _, _ = api
    first, second = create_session(client), create_session(client)
    entered, release = Event(), Event()

    def provider():
        entered.set()
        assert release.wait(8)

    model = SyntheticModel(provider, malformed=False)
    # The other owner's introduction requires stage confirmation and never dispatches.
    other_created = client.post(SESSIONS, headers=B, json={"mode": "foundation"}).json()
    other = f"{SESSIONS}/{other_created['session_id']}"
    monkeypatch.setattr(career_interviews, "_turn_model", lambda: model)
    with ThreadPoolExecutor(max_workers=1) as pool:
        active = pool.submit(client.post, f"{first}/turns", headers=A, json=turn())
        try:
            assert entered.wait(8)
            assert client.post(f"{second}/turns", headers=A, json=turn()).status_code == 429
            assert client.get(f"{second}/messages", headers=A).json() == []
            assert events(client.post(f"{other}/turns", headers=B, json=turn()))[-1][0] == "turn.completed"
        finally:
            release.set()
        assert events(active.result(timeout=8))[-1][1]["proposal_validated"]


def test_failed_final_write_does_not_publish_or_partially_commit(api, monkeypatch, caplog):
    client, engine, _ = api
    model = SyntheticModel(malformed=False)
    monkeypatch.setattr(career_interviews, "_turn_model", lambda: model)

    def reject_storage(*_args):
        raise RuntimeError(UNVALIDATED)

    monkeypatch.setattr(LineageService, "stage_run", reject_storage)
    path = create_session(client)
    response = client.post(f"{path}/turns", headers=A, json=turn())
    assert events(response)[-1] == ("turn.failed", {"type": "turn.failed", "code": "turn_unavailable"})
    assert UNVALIDATED not in response.text + caplog.text
    assert [message["processing_status"] for message in client.get(f"{path}/messages", headers=A).json()] == ["interrupted"]
    state = client.get(path, headers=A).json()
    assert state["chapter"] == "introduction" and state["state_version"] == 2
    assert state["tokens_remaining"] == interview_turn_service.SESSION_TOKENS - interview_turn_service.ATTEMPT_TOKENS
    with Session(engine) as db:
        assert db.scalars(select(CareerRunRow)).all() == []


@pytest.mark.parametrize(
    ("change", "result"),
    [("version", "valid"), ("version", "repair"), ("version", "retry"),
     ("account_deleted", "retry"), ("retention_expired", "retry")],
)
def test_session_authority_rechecked_before_model_retry_and_commit(api, monkeypatch, change, result):
    client, engine, identities = api
    path = create_session(client)

    def change_session():
        operations = {
            "version": "UPDATE career_interview_sessions SET state_version = state_version + 1",
            "account_deleted": "DELETE FROM users WHERE user_id = :owner",
            "retention_expired": "UPDATE career_interview_sessions SET retention_expires_at = clock_timestamp()",
        }
        with engine.begin() as conn:
            conn.execute(text(operations[change]), {"owner": identities["owner"]})

    model = SyntheticModel(change_session, malformed=result == "repair", transient=result == "retry")
    monkeypatch.setattr(career_interviews, "_turn_model", lambda: model)
    stream = events(client.post(f"{path}/turns", headers=A, json=turn()))
    assert [name for name, _ in stream] == ["turn.started", "analysis.progress", "turn.failed"]
    assert stream[-1][1]["code"] == "state_changed"
    assert len(model.requests) == 1
    messages = client.get(f"{path}/messages", headers=A)
    if change == "version":
        assert [message["processing_status"] for message in messages.json()] == ["interrupted"]
    else:
        assert messages.status_code == 404


def test_closed_by_default_and_bad_inputs_have_no_side_effects(api, monkeypatch):
    client, _, _ = api
    path = create_session(client)
    monkeypatch.setattr(settings, "CAREER_TURNS_ENABLED", False)
    assert client.post(f"{path}/turns", headers=A, json=turn()).status_code == 503
    monkeypatch.setattr(settings, "CAREER_TURNS_ENABLED", True)
    assert client.post(f"{path}/turns", headers=A, json=turn(content="x" * 4001)).status_code == 422
    assert client.post(f"{path}/turns", headers=A, content=b"x" * 8193).status_code == 413
    assert client.post(f"{path}/turns", headers=A, json={**turn(), "owner_id": UNLINKED}).status_code == 422
    assert client.post(f"{path}/turns", headers=A, json=turn(expected_state_version=2)).status_code == 409
    assert client.get(f"{path}/messages", headers=A).json() == []


def test_turn_migration_keeps_existing_records_and_refuses_dropping_live_markers(api, migrated_database):
    client, engine, identities = api
    _, config = migrated_database
    previous = "2026_11_14_career_lineage"
    path = create_session(client)
    session_id = path.rsplit("/", 1)[1]
    with Session(engine) as db:
        InterviewService(db, identities["owner"]).append(session_id, MessageInput(key="legacy", content=UNLINKED))
    command.downgrade(config, previous)
    command.upgrade(config, "head")
    assert client.get(f"{path}/messages", headers=A).json()[0]["content"] == UNLINKED
    events(client.post(f"{path}/turns", headers=A, json=turn(expected_state_version=2)))
    with pytest.raises(DBAPIError, match="Career turn admission records must be preserved"):
        command.downgrade(config, previous)


@pytest.mark.parametrize("content", ["Synthetic project explanation", "😀" * 1500])
def test_provider_configuration_uses_the_real_adapter_with_mock_http(api, monkeypatch, tmp_path, content):
    client, engine, identities = api
    path = create_session(client)
    commit = "c" * 40
    monkeypatch.setattr(settings, "CAREER_MODEL_SAFETY_KEY", SecretStr("synthetic-dedicated-safety-secret-123"))
    revision = tmp_path / "release_revision.txt"
    revision.write_text(commit + "\n")
    monkeypatch.setattr(career_interviews, "_PACKAGED_REVISION", revision)
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "d" * 40)
    monkeypatch.setattr(settings, "CAREER_MODEL_APPLICATION_COMMIT", "e" * 40)
    monkeypatch.setattr(settings, "ENABLE_AI_FEATURES", True)
    requests = []

    def provider(request):
        wire = json.loads(request.content)
        assert str(request.url) == "https://api.openai.com/v1/responses"
        assert wire["store"] is False
        assert identities["owner"] not in json.dumps(wire)
        assert wire["model"] == "gpt-4o-2024-08-06"
        requests.append(wire)
        context = json.loads(wire["input"][0]["content"])
        assert context["recent_messages"] == [{"role": "user", "content": content}]
        plan = context["plan"]
        validated = {"schema_version": 1, **plan, "evidence_proposals": [], "contradiction_candidates": []}
        return httpx.Response(200, json={
            "id": "resp_synthetic", "object": "response", "created_at": 1, "status": "completed", "model": wire["model"],
            "output": [{"type": "message", "role": "assistant", "status": "completed", "id": "msg_synthetic",
                        "content": [{"type": "output_text", "text": json.dumps(validated), "annotations": []}]}],
            "usage": {"input_tokens": 80, "output_tokens": 40, "total_tokens": 120},
        })

    transport = AsyncOpenAI(api_key="synthetic", base_url="https://api.openai.com/v1/",
                            http_client=httpx.AsyncClient(transport=httpx.MockTransport(provider)))
    monkeypatch.setattr(career_interviews, "get_model_runtime", lambda: ModelRuntime(client_factory=lambda: transport))
    try:
        response = events(client.post(f"{path}/turns", headers=A, json=turn(content=content)))
    finally:
        client.portal.call(transport.close)
    assert len(requests) == 1 and response[-1][1]["proposal_validated"]
    with Session(engine) as db:
        record = db.scalar(select(CareerRunRow))
        run = LineageService(db, identities["owner"]).get_run(record.id)
        assert run.metadata.application_commit == commit
        assert run.metadata.input_tokens == 80 and run.metadata.output_tokens == 40
        assert run.manifest.store_response is False


def start_turn_asgi(path, payload, spec_version="2.4"):
    incoming = asyncio.Queue()
    outgoing = asyncio.Queue()
    body = json.dumps(payload).encode()
    incoming.put_nowait({"type": "http.request", "body": body, "more_body": False})
    scope = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": spec_version},
        "http_version": "1.1", "method": "POST", "scheme": "http",
        "path": path, "raw_path": path.encode(), "root_path": "", "query_string": b"",
        "headers": [(b"content-type", b"application/json"), (b"authorization", b"Bearer owner"),
                    (b"accept", b"text/event-stream"), (b"accept-encoding", b"gzip"), (b"host", b"testserver")],
        "client": ("127.0.0.1", 11111), "server": ("testserver", 80),
    }
    task = asyncio.create_task(app(scope, incoming.get, outgoing.put))
    return incoming, outgoing, task


@pytest.mark.asyncio
async def test_asgi_sends_status_frames_before_provider_completes(api, monkeypatch):
    client, _, _ = api
    path = f"{create_session(client)}/turns"
    release = Event()

    def provider():
        assert release.wait(8)

    monkeypatch.setattr(career_interviews, "_turn_model", lambda: SyntheticModel(provider, malformed=False))
    incoming, outgoing, task = start_turn_asgi(path, turn())
    try:
        async with asyncio.timeout(8):
            start = await outgoing.get()
            assert start["status"] == 200
            headers = dict(start["headers"])
            assert headers[b"content-type"].startswith(b"text/event-stream")
            assert b"content-encoding" not in headers
            for event in (b"turn.started", b"analysis.progress"):
                frame = await outgoing.get()
                assert frame["more_body"]
                assert frame["body"].startswith(b"event: " + event + b"\n")
    finally:
        release.set()
        await asyncio.wait_for(task, timeout=8)
    remaining = []
    while not outgoing.empty():
        remaining.append(outgoing.get_nowait()["body"])
    tail = b"".join(remaining)
    assert b"event: assistant.message\n" in tail and b"event: turn.completed\n" in tail


def test_utf8_input_under_the_body_limit_reaches_the_model_intact(api, monkeypatch):
    client, _, _ = api
    path = create_session(client)
    model = SyntheticModel(malformed=False)
    monkeypatch.setattr(career_interviews, "_turn_model", lambda: model)
    content = "😀" * 1500
    response = events(client.post(f"{path}/turns", headers=A, json=turn(content=content)))
    assert response[-1][1]["proposal_validated"]
    assert model.requests[0]["recent_messages"] == [{"role": "user", "content": content}]


@pytest.mark.parametrize("isolation_level", ["REPEATABLE READ", "SERIALIZABLE", "AUTOCOMMIT"])
def test_turn_requires_transactional_read_committed(api, monkeypatch, isolation_level):
    client, engine, _ = api
    path = create_session(client)
    incompatible = engine.execution_options(isolation_level=isolation_level)

    def sessions():
        with Session(incompatible, autoflush=False) as db:
            yield db

    model = SyntheticModel()
    monkeypatch.setitem(app.dependency_overrides, get_db, sessions)
    monkeypatch.setattr(career_interviews, "_turn_model", lambda: model)

    response = client.post(f"{path}/turns", headers=A, json=turn())
    assert response.status_code == 503
    assert model.requests == []
    assert client.get(f"{path}/messages", headers=A).json() == []
    assert client.get(path, headers=A).json()["state_version"] == 1


def test_matching_turn_key_replays_saved_reply_without_a_second_model_call(api, monkeypatch):
    client, engine, _ = api
    model = SyntheticModel(malformed=False)
    monkeypatch.setattr(career_interviews, "_turn_model", lambda: model)
    path = create_session(client)
    payload = turn()
    result = events(client.post(f"{path}/turns", headers=A, json=payload))
    reply = result[-2][1]["message"]

    replay = events(client.post(f"{path}/turns", headers=A, json=payload))
    assert replay == [("turn.replayed", {"type": "turn.replayed", "message": reply,
                                         "state": result[-1][1]["state"], "recovered": False})]
    assert client.post(f"{path}/turns", headers=A,
                       json={**payload, "content": "A different answer"}).status_code == 409
    assert client.post(f"{path}/turns", headers=B, json=payload).status_code == 404
    assert len(model.requests) == 1
    assert len(client.get(f"{path}/messages", headers=A).json()) == 2
    with Session(engine) as db:
        assert len(db.scalars(select(CareerRunRow)).all()) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("spec_version", ["2.3", "2.4"])
async def test_disconnect_cancels_provider_and_recovery_reuses_saved_message(api, monkeypatch, spec_version):
    client, engine, _ = api
    opened = client.post(SESSIONS, headers=A, json={"mode": "foundation"})
    assert opened.status_code == 201
    path = f"{SESSIONS}/{opened.json()['session_id']}"
    payload = {**turn(), "candidate_stage": "experienced_ic"}
    started, cancelled, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

    class WaitingModel(SyntheticModel):
        async def propose(self, request):
            self.requests.append(json.loads(request.context))
            started.set()
            try:
                await release.wait()
            finally:
                cancelled.set()

    model = WaitingModel()
    monkeypatch.setattr(career_interviews, "_turn_model", lambda: model)
    incoming, _, task = start_turn_asgi(f"{path}/turns", payload, spec_version)
    try:
        await asyncio.wait_for(started.wait(), timeout=5)
        duplicate = await asyncio.to_thread(client.post, f"{path}/turns", headers=A, json={**payload, "retry": True})
        assert events(duplicate)[0][0] == "turn.pending"
        incoming.put_nowait({"type": "http.disconnect"})
        await asyncio.wait_for(asyncio.shield(task), timeout=5)
        assert cancelled.is_set() and len(model.requests) == 1
    finally:
        release.set()
        await asyncio.wait_for(task, timeout=5)

    with TestClient(app) as reconnected:
        history = reconnected.get(f"{path}/messages", headers=A).json()
        assert [row["processing_status"] for row in history] == ["interrupted"]
        assert history[0]["turn_recovery"] == {"candidate_stage": "experienced_ic"}
        interrupted = events(reconnected.post(f"{path}/turns", headers=A, json=payload))
        assert interrupted[0][0] == "turn.interrupted" and interrupted[0][1]["can_retry"]
        state_version = interrupted[0][1]["state_version"]
        retry = {**payload, "retry": True, "expected_state_version": state_version}
        recovered = events(reconnected.post(f"{path}/turns", headers=A, json=retry))
        assert recovered[0][0] == "turn.replayed" and recovered[0][1]["recovered"]
        tokens = interview_turn_service.SESSION_TOKENS - interview_turn_service.ATTEMPT_TOKENS
        assert recovered[0][1]["state"]["tokens_remaining"] == tokens
        assert recovered[0][1]["state"]["turns_remaining"] == interview_turn_service.SESSION_TURNS - 1
        assert events(reconnected.post(f"{path}/turns", headers=A, json=retry))[0][1]["state"]["tokens_remaining"] == tokens
        final = reconnected.get(f"{path}/messages", headers=A).json()
        assert [row["processing_status"] for row in final] == ["complete", "complete"]
        assert final[0]["position"] == history[0]["position"]
    assert len(model.requests) == 1
    with Session(engine) as db:
        assert db.scalars(select(CareerRunRow)).all() == []


@pytest.mark.parametrize("dispatched", [False, True])
def test_expired_turn_is_reconciled_once_and_concurrent_retries_share_one_reply(api, monkeypatch, dispatched):
    client, engine, identities = api
    path = create_session(client)
    session_id = path.rsplit("/", 1)[1]
    payload = turn()
    monkeypatch.setattr(interview_turn_service, "TURN_LEASE", timedelta(seconds=1))
    with Session(engine) as db:
        service = interview_turn_service.InterviewTurnService(db, identities["owner"])
        orphan = service.begin(session_id, TurnInput(**payload), create_model=SyntheticModel)
        if dispatched:
            service.record_dispatch(orphan)
    sleep(1.05)
    assert client.get(f"{path}/messages", headers=A).json()[0]["processing_status"] == "interrupted"
    with Session(engine) as db:
        assert db.scalar(select(InterviewMessageRow)).processing_status == "pending"

    def unexpected_model():
        pytest.fail("Recovery should not resolve or call a provider")

    monkeypatch.setattr(career_interviews, "_turn_model", unexpected_model)
    change = client.post(f"{path}/turns", headers=A, json={**payload, "candidate_stage": "new_graduate"})
    assert change.status_code == 409
    retry = {**payload, "retry": True, "expected_state_version": orphan.state.state_version}
    assert client.post(f"{path}/turns", headers=B, json=retry).status_code == 404
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = [pool.submit(client.post, f"{path}/turns", headers=A, json=retry) for _ in range(2)]
        receipts = [events(response.result(timeout=5))[0][1] for response in responses]
    assert sum(receipt["recovered"] for receipt in receipts) == 1
    assert receipts[0]["message"] == receipts[1]["message"]
    assert receipts[0]["state"] == receipts[1]["state"]
    balance = interview_turn_service.SESSION_TOKENS - dispatched * interview_turn_service.ATTEMPT_TOKENS
    assert receipts[0]["state"]["tokens_remaining"] == balance
    assert len(client.get(f"{path}/messages", headers=A).json()) == 2


def test_stale_and_unknown_retries_do_not_replay_state(api, monkeypatch):
    client, engine, identities = api
    path = create_session(client)
    session_id = path.rsplit("/", 1)[1]
    payload = turn()
    assert client.post(f"{path}/turns", headers=A, json={**payload, "retry": True}).status_code == 409
    with Session(engine) as db:
        service = interview_turn_service.InterviewTurnService(db, identities["owner"])
        orphan = service.begin(session_id, TurnInput(**payload), create_model=SyntheticModel)
        service.interrupt(orphan)
    with engine.begin() as conn:
        conn.execute(text("UPDATE career_interview_sessions SET state_version = state_version + 1"))
    report = events(client.post(f"{path}/turns", headers=A, json=payload))[0][1]
    assert not report["can_retry"]
    assert client.post(f"{path}/turns", headers=A, json={
        **payload, "retry": True, "expected_state_version": report["state_version"],
    }).status_code == 409
    assert len(client.get(f"{path}/messages", headers=A).json()) == 1
    assert client.get(path, headers=A).json()["tokens_remaining"] == interview_turn_service.SESSION_TOKENS


def test_timeout_fallback_is_saved_and_replayed_without_another_dispatch(api, monkeypatch):
    client, engine, _ = api
    path = create_session(client)

    class TimeoutModel(SyntheticModel):
        async def propose(self, request):
            self.requests.append(request)
            raise TimeoutError

    model = TimeoutModel()
    monkeypatch.setattr(career_interviews, "_turn_model", lambda: model)
    result = events(client.post(f"{path}/turns", headers=A, json=turn()))
    assert result[-1][0] == "turn.completed" and not result[-1][1]["proposal_validated"]
    assert result[-1][1]["tokens_reserved"] == interview_turn_service.ATTEMPT_TOKENS
    replay = events(client.post(f"{path}/turns", headers=A, json={**turn(), "retry": True}))
    assert replay[0][0] == "turn.replayed" and replay[0][1]["message"] == result[-2][1]["message"]
    assert len(model.requests) == 1
    with Session(engine) as db:
        assert db.scalar(select(InterviewMessageRow).where(InterviewMessageRow.role == "user")).turn_tokens_dispatched == interview_turn_service.ATTEMPT_TOKENS


def test_new_turn_reconciles_expired_reservation_and_fences_old_retry(api, monkeypatch):
    client, engine, identities = api
    path = create_session(client)
    session_id = path.rsplit("/", 1)[1]
    monkeypatch.setattr(interview_turn_service, "TURN_LEASE", timedelta(seconds=1))
    with Session(engine) as db:
        service = interview_turn_service.InterviewTurnService(db, identities["owner"])
        old = service.begin(session_id, TurnInput(**turn()), create_model=SyntheticModel)
    sleep(1.05)

    monkeypatch.setattr(interview_turn_service, "TURN_LEASE", timedelta(seconds=60))
    reply = events(client.post(f"{path}/turns", headers=A, json=turn(
        key="new-turn", expected_state_version=old.state.state_version,
    )))
    current = reply[-1][1]["state"]
    assert current["tokens_remaining"] == interview_turn_service.SESSION_TOKENS
    assert client.post(f"{path}/turns", headers=A, json={
        **turn(expected_state_version=current["state_version"]), "retry": True,
    }).status_code == 409
    with Session(engine) as db:
        messages = db.scalars(select(InterviewMessageRow).order_by(InterviewMessageRow.position)).all()
        assert [row.processing_status for row in messages] == ["interrupted", "complete", "complete"]


def test_recovery_migration_preserves_legacy_turns_and_guarded_downgrade(api, migrated_database):
    client, engine, identities = api
    _, config = migrated_database
    previous = "2026_11_16_career_turns"
    path = create_session(client)
    session_id = path.rsplit("/", 1)[1]
    command.downgrade(config, previous)
    from app.application.career_encryption import career_cipher

    cipher = career_cipher()
    with engine.begin() as conn:
        for position, role, key, content in (
            (1, "user", "legacy-completed", "Synthetic legacy answer"),
            (2, "assistant", "legacy-completed", "Synthetic legacy reply"),
            (3, "user", "legacy-interrupted", "Synthetic lost answer"),
        ):
            conn.execute(text("""
                INSERT INTO career_interview_messages (user_id, session_id, position, key, role,
                    content_ciphertext, processing_status, turn_lease_expires_at, created_at)
                VALUES (:owner, :session, :position, :key, :role, :encrypted, :status,
                    CASE WHEN :role = 'user' THEN statement_timestamp() - interval '1 minute' END,
                    statement_timestamp() - interval '2 minutes')
            """), {"owner": identities["owner"], "session": session_id, "position": position, "key": key,
                   "role": role, "encrypted": cipher.encrypt(content.encode()).decode(),
                   "status": "pending" if position == 3 else "complete"})
        conn.execute(text("UPDATE career_interview_sessions SET message_count = 3, state_version = 4 WHERE id = :id"),
                     {"id": session_id})

    command.upgrade(config, "head")
    saved = events(client.post(f"{path}/turns", headers=A, json=turn(
        key="legacy-completed", content="Synthetic legacy answer",
    )))
    assert saved[0][1]["message"]["content"] == "Synthetic legacy reply"
    interrupted = events(client.post(f"{path}/turns", headers=A, json=turn(
        key="legacy-interrupted", content="Synthetic lost answer",
    )))
    assert interrupted[0][0] == "turn.interrupted" and not interrupted[0][1]["can_retry"]
    command.downgrade(config, previous)
    command.upgrade(config, "head")
    assert len(client.get(f"{path}/messages", headers=A).json()) == 3
    events(client.post(f"{path}/turns", headers=A, json=turn(key="new", expected_state_version=4)))
    with pytest.raises(DBAPIError, match="Career turn admission records must be preserved for recovery"):
        command.downgrade(config, previous)


def test_deterministic_turn_keeps_active_session_with_one_attempt_of_capacity(api):
    client, engine, _ = api
    path = create_session(client)
    first = events(client.post(f"{path}/turns", headers=A, json=turn()))
    version = first[-1][1]["state"]["state_version"]
    remaining = interview_turn_service.ATTEMPT_TOKENS
    with engine.begin() as conn:
        conn.execute(text("UPDATE career_interview_sessions SET tokens_remaining = :remaining"),
                     {"remaining": remaining})
    second = events(client.post(f"{path}/turns", headers=A, json=turn(key="next", expected_state_version=version)))
    assert second[-1][1]["state"]["status"] == "active"
    assert second[-1][1]["state"]["tokens_remaining"] == remaining


def test_invalid_model_configuration_prevents_new_admission_but_preserves_replay(api, monkeypatch):
    from app.application.errors import ExternalServiceError

    client, _, _ = api
    path = create_session(client)
    completed = events(client.post(f"{path}/turns", headers=A, json=turn()))
    current = completed[-1][1]["state"]

    def broken_configuration():
        raise ExternalServiceError("Synthetic configuration error")

    monkeypatch.setattr(career_interviews, "_turn_model", broken_configuration)
    assert events(client.post(f"{path}/turns", headers=A, json=turn()))[0][0] == "turn.replayed"
    response = client.post(f"{path}/turns", headers=A, json=turn(
        key="next", expected_state_version=current["state_version"],
    ))
    assert response.status_code == 503
    assert client.get(path, headers=A).json() == current
    assert len(client.get(f"{path}/messages", headers=A).json()) == 2
