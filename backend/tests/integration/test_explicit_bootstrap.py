"""Observable PRI-20 authentication and onboarding contracts."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core import auth
from app.db.session import get_db
from app.models.user import User
from app.models.credit_ledger import CreditLedger
from sqlalchemy.exc import OperationalError
from app.application import bootstrap as service
from app.application.errors import ExternalServiceError, ResourceConflictError


@pytest.mark.parametrize("dependency", [
    auth.get_current_user_id, auth.get_authenticated_user_id, auth.get_optional_user_id,
])
def test_authentication_does_not_access_database(dependency, monkeypatch, db_session):
    monkeypatch.setattr(auth, "decode_supabase_jwt", lambda _: {"sub": "new-identity"})
    app = FastAPI()
    app.dependency_overrides[get_db] = lambda: db_session

    @app.get("/identity")
    def identity(user_id=Depends(dependency)):
        return user_id

    statements = []
    def record(_conn, _cursor, statement, *_args):
        statements.append(statement)
    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", record)
    try:
        response = TestClient(app).get("/identity", headers={"Authorization": "Bearer test"})
        assert response.status_code == 200
        assert response.json() == "new-identity"
        assert statements == []
    finally:
        event.remove(engine, "before_cursor_execute", record)


def test_bootstrap_uses_verified_identity_and_is_idempotent(client, db_session, monkeypatch):
    monkeypatch.setattr(auth, "decode_supabase_jwt", lambda _: {
        "sub": "new-account", "email": "new@example.com",
    })
    for _ in range(2):
        response = client.post("/api/v1/auth/bootstrap", headers={"Authorization": "Bearer test"},
                               json={"user_id": "victim", "amount": 9000})
        assert response.status_code == 204, response.text
        assert response.content == b""
    assert db_session.query(User).filter_by(user_id="victim").count() == 0
    assert db_session.query(User).filter_by(user_id="new-account").count() == 1
    rows = db_session.query(CreditLedger).filter_by(user_id="new-account").all()
    assert len(rows) == 1
    assert rows[0].delta == 90


def test_bootstrap_requires_bearer(client, db_session):
    before = db_session.query(User).count()
    assert client.post("/api/v1/auth/bootstrap").status_code == 401
    assert db_session.query(User).count() == before


@pytest.mark.parametrize("failure_stage", ["grant", "commit"])
def test_bootstrap_rolls_back_user_and_grant_then_can_retry(db_session, monkeypatch, failure_stage):
    def fail(*_args, **_kwargs):
        raise OperationalError("secret sql", {}, Exception("private connection"))
    with monkeypatch.context() as patch:
        if failure_stage == "grant":
            patch.setattr(service, "grant_monthly", fail)
        else:
            patch.setattr(db_session, "commit", fail)
        with pytest.raises(ExternalServiceError):
            service.bootstrap_account(db_session, user_id="atomic", email=None)
    assert db_session.query(User).filter_by(user_id="atomic").count() == 0
    assert db_session.query(CreditLedger).filter_by(user_id="atomic").count() == 0
    service.bootstrap_account(db_session, user_id="atomic", email=None)
    assert db_session.query(CreditLedger).filter_by(user_id="atomic").one().delta == 90


def test_email_conflict_does_not_grant_or_take_over_account(db_session):
    service.bootstrap_account(db_session, user_id="owner", email="same@example.com")
    with pytest.raises(ResourceConflictError):
        service.bootstrap_account(db_session, user_id="different", email="same@example.com")
    assert db_session.query(User).filter_by(user_id="different").count() == 0
    assert db_session.query(CreditLedger).filter_by(user_id="different").count() == 0
    assert db_session.query(User).filter_by(user_id="owner").one().email == "same@example.com"


@pytest.mark.parametrize("failure,status,detail", [
    ("invalid", 401, "Invalid or expired authentication token"),
    ("provider", 503, "Authentication service unavailable"),
    ("database", 503, "Account setup service unavailable"),
    ("conflict", 409, "Account setup conflicts with existing data"),
])
def test_bootstrap_errors_are_distinguishable_and_safe(client, db_session, monkeypatch, failure, status, detail):
    from jwt import InvalidTokenError
    from jwt.exceptions import PyJWKClientConnectionError
    from unittest.mock import Mock
    from app.api.v1.endpoints import bootstrap as endpoint
    if failure in ("invalid", "provider"):
        error = InvalidTokenError if failure == "invalid" else PyJWKClientConnectionError
        fake = Mock()
        fake.get_signing_key_from_jwt.side_effect = error("private details")
        monkeypatch.setattr(auth, "_jwks_client", lambda: fake)
        call = Mock(side_effect=AssertionError("bootstrap ran without authentication"))
        monkeypatch.setattr(endpoint, "bootstrap_account", call)
    else:
        monkeypatch.setattr(auth, "decode_supabase_jwt", lambda _: {"sub": "new-account"})
        error = ExternalServiceError if failure == "database" else ResourceConflictError
        monkeypatch.setattr(endpoint, "bootstrap_account", Mock(side_effect=error("private details")))
    response = client.post("/api/v1/auth/bootstrap", headers={"Authorization": "Bearer test"})
    assert response.status_code == status
    assert response.json()["detail"] == detail
    assert "private" not in response.text
    assert db_session.query(User).filter_by(user_id="new-account").count() == 0


def test_public_preview_blocks_bootstrap_before_authentication():
    from app.middleware.public_preview import PublicPreviewAccessMiddleware
    from app.api.v1.endpoints.bootstrap import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.add_middleware(PublicPreviewAccessMiddleware, enabled=True)
    response = TestClient(app).post("/api/v1/auth/bootstrap", headers={"Authorization": "Bearer bad"})
    assert response.status_code == 403


@pytest.mark.parametrize("fault", [None, "expired", "issuer", "audience", "signature", "missing-sub"])
def test_bootstrap_verifies_signed_tokens_before_creating_account(client, db_session, monkeypatch, fault):
    import time
    from types import SimpleNamespace
    import jwt
    from cryptography.hazmat.primitives.asymmetric import ec
    key = ec.generate_private_key(ec.SECP256R1())
    payload = {"sub": "signed-identity", "iss": "https://test.supabase.co/auth/v1",
               "aud": "authenticated", "exp": int(time.time()) + 120}
    if fault == "expired":
        payload["exp"] = int(time.time()) - 120
    elif fault == "issuer":
        payload["iss"] = "https://foreign.example/auth/v1"
    elif fault == "audience":
        payload["aud"] = "different-app"
    elif fault == "missing-sub":
        del payload["sub"]
    verification_key = ec.generate_private_key(ec.SECP256R1()) if fault == "signature" else key
    monkeypatch.setattr(auth, "_jwks_client", lambda: SimpleNamespace(
        get_signing_key_from_jwt=lambda _: SimpleNamespace(key=verification_key.public_key()),
    ))
    token = jwt.encode(payload, key, algorithm="ES256", headers={"kid": "fixture"})
    response = client.post("/api/v1/auth/bootstrap", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == (204 if fault is None else 401)
    assert db_session.query(User).filter_by(user_id="signed-identity").count() == (0 if fault else 1)
    assert db_session.query(CreditLedger).filter_by(user_id="signed-identity").count() == (0 if fault else 1)
