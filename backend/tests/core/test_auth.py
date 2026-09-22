"""Tests for pure JWT authentication and stable error semantics."""

import os
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")

import pytest

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials


from app.core.auth import get_current_user_id, get_current_user_email
from app.models.user import User


# ---------------------------------------------------------------------------
# decode_supabase_jwt + _jwks_client tests
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock
from app.core.auth import decode_supabase_jwt, _jwks_client


def test_jwks_client_is_cached(monkeypatch):
    """_jwks_client uses @lru_cache(maxsize=1) — same instance returned across calls."""
    # Clear the cache to start fresh
    _jwks_client.cache_clear()
    c1 = _jwks_client()
    c2 = _jwks_client()
    assert c1 is c2


def test_decode_supabase_jwt_raises_on_invalid_token(monkeypatch):
    """Malformed token → HTTPException 401."""
    from jwt import PyJWTError

    # Raise a PyJWTError subclass so it is caught by decode_supabase_jwt's
    # `except PyJWTError` handler and converted to an HTTPException 401.
    fake_client = MagicMock()
    fake_client.get_signing_key_from_jwt.side_effect = PyJWTError("bad key")
    monkeypatch.setattr("app.core.auth._jwks_client", lambda: fake_client)

    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt("not-a-real-token")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired authentication token"
    assert "bad key" not in exc_info.value.detail


def test_decode_supabase_jwt_valid_token_returns_claims(monkeypatch):
    """Valid token → claims dict with sub + email."""
    fake_signing_key = MagicMock()
    fake_signing_key.key = "fake-key"
    fake_client = MagicMock()
    fake_client.get_signing_key_from_jwt.return_value = fake_signing_key
    monkeypatch.setattr("app.core.auth._jwks_client", lambda: fake_client)

    decode_arguments = {}

    def fake_decode(*args, **kwargs):
        decode_arguments.update(kwargs)
        return {"sub": "user-123", "email": "test@x.com", "aud": "authenticated"}

    monkeypatch.setattr("app.core.auth.jwt.decode", fake_decode)

    claims = decode_supabase_jwt("valid-token")
    assert claims["sub"] == "user-123"
    assert claims["email"] == "test@x.com"
    assert decode_arguments["audience"] == "authenticated"
    assert decode_arguments["issuer"] == "https://test.supabase.co/auth/v1"
    assert decode_arguments["algorithms"] == ["ES256"]
    assert decode_arguments["options"]["verify_iss"] is True
    assert set(decode_arguments["options"]["require"]) == {"aud", "exp", "iss", "sub"}


def test_decode_supabase_jwt_rejects_wrong_issuer_without_leaking_details(monkeypatch):
    from jwt import InvalidIssuerError

    fake_signing_key = MagicMock()
    fake_signing_key.key = "fake-key"
    fake_client = MagicMock()
    fake_client.get_signing_key_from_jwt.return_value = fake_signing_key
    monkeypatch.setattr("app.core.auth._jwks_client", lambda: fake_client)
    monkeypatch.setattr(
        "app.core.auth.jwt.decode",
        MagicMock(side_effect=InvalidIssuerError("foreign Supabase project")),
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt("foreign-project-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired authentication token"
    assert "foreign" not in exc_info.value.detail


def test_decode_supabase_jwt_returns_stable_503_when_jwks_is_unavailable(monkeypatch):
    fake_client = MagicMock()
    from jwt.exceptions import PyJWKClientConnectionError
    fake_client.get_signing_key_from_jwt.side_effect = PyJWKClientConnectionError("network details")
    monkeypatch.setattr("app.core.auth._jwks_client", lambda: fake_client)

    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt("otherwise-valid-token")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Authentication service unavailable"
    assert "network" not in exc_info.value.detail


# ---------------------------------------------------------------------------
# get_current_user_id + get_current_user_email dependency-injection tests
# ---------------------------------------------------------------------------


def test_get_current_user_id_returns_sub_claim(monkeypatch, db_session):
    """Valid bearer token → returns sub claim, does not create a user row."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: {"sub": "user-from-jwt", "email": "jwt@x.com", "aud": "authenticated"},
    )

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")
    user_id = get_current_user_id(credentials=creds)

    assert user_id == "user-from-jwt"

    # Authentication must not initialize application state.
    user = db_session.query(User).filter_by(user_id="user-from-jwt").first()
    assert user is None


def test_get_current_user_id_raises_401_on_bad_token(monkeypatch, db_session):
    """Invalid token bubbles up as 401."""
    def raise_unauthorized(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    monkeypatch.setattr("app.core.auth.decode_supabase_jwt", raise_unauthorized)

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(credentials=creds)
    assert exc_info.value.status_code == 401


def test_get_current_user_email_returns_email_claim(monkeypatch):
    """Valid bearer token → returns email claim."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: {"sub": "user-x", "email": "user@x.com", "aud": "authenticated"},
    )

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")
    email = get_current_user_email(credentials=creds)
    assert email == "user@x.com"


# ---------------------------------------------------------------------------
# Additional branch coverage tests
# ---------------------------------------------------------------------------

from app.core.auth import get_optional_user_id, get_authenticated_user_id


def test_get_current_user_id_raises_401_when_no_credentials(db_session):
    """Missing credentials → 401."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(credentials=None)
    assert exc_info.value.status_code == 401


def test_get_current_user_id_raises_401_when_sub_missing(monkeypatch, db_session):
    """Token with no sub claim → 401."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: {"email": "no-sub@x.com", "aud": "authenticated"},
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-no-sub")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(credentials=creds)
    assert exc_info.value.status_code == 401


def test_get_current_user_email_raises_401_when_no_credentials():
    """Missing credentials → 401 from get_current_user_email."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_email(credentials=None)
    assert exc_info.value.status_code == 401


def test_get_current_user_email_raises_401_when_email_missing(monkeypatch):
    """Token with no email claim → 401."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: {"sub": "user-y", "aud": "authenticated"},
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-no-email")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_email(credentials=creds)
    assert exc_info.value.status_code == 401


def test_get_optional_user_id_returns_none_when_no_credentials(db_session):
    """No credentials → returns None (not 401)."""
    result = get_optional_user_id(request=Request({"type": "http", "headers": []}), credentials=None)
    assert result is None


def test_get_optional_user_id_returns_user_id_on_valid_token(monkeypatch, db_session):
    """Valid token → returns sub claim."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: {"sub": "optional-user", "email": "opt@x.com", "aud": "authenticated"},
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
    request = Request({"type": "http", "headers": [(b"authorization", b"Bearer valid-token")]})
    result = get_optional_user_id(request=request, credentials=creds)
    assert result == "optional-user"


def test_get_optional_user_id_rejects_bad_token(monkeypatch, db_session):
    """Invalid credentials must never become an anonymous identity."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: (_ for _ in ()).throw(HTTPException(status_code=401, detail="bad")),
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")
    request = Request({"type": "http", "headers": [(b"authorization", b"Bearer bad-token")]})
    with pytest.raises(HTTPException) as exc_info:
        get_optional_user_id(request=request, credentials=creds)
    assert exc_info.value.status_code == 401


def test_get_authenticated_user_id_returns_sub_claim(monkeypatch, db_session):
    """Valid token through get_authenticated_user_id → returns sub."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: {"sub": "auth-user", "email": "auth@x.com", "aud": "authenticated"},
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="auth-token")
    result = get_authenticated_user_id(credentials=creds)
    assert result == "auth-user"


def test_get_authenticated_user_id_raises_401_when_no_credentials(db_session):
    """No credentials → 401 from get_authenticated_user_id."""
    with pytest.raises(HTTPException) as exc_info:
        get_authenticated_user_id(credentials=None)
    assert exc_info.value.status_code == 401
