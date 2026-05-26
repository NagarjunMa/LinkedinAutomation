"""Tests for app.core.auth — _ensure_user_row."""

import os
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")

import pytest
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import _ensure_user_row, get_current_user_id, get_current_user_email
from app.models.user import User
from app.models.credit_ledger import CreditLedger


def test_ensure_user_row_creates_user_and_grants_welcome_credits(db_session, test_user_id):
    """First-time sign-in creates User row + 10 welcome credits (reason='grant')."""
    new_user_id = "brand-new-user"
    _ensure_user_row(db_session, new_user_id, "new@example.com")
    # _ensure_user_row commits internally; no extra commit needed

    user = db_session.query(User).filter(User.user_id == new_user_id).first()
    assert user is not None
    assert user.email == "new@example.com"

    ledger_entries = db_session.query(CreditLedger).filter_by(user_id=new_user_id).all()
    assert len(ledger_entries) == 1
    assert ledger_entries[0].delta == 10
    # grant_monthly uses reason="grant" (not "welcome_grant")
    assert ledger_entries[0].reason == "grant"
    # external_ref encodes the intent
    assert ledger_entries[0].external_ref == f"welcome:{new_user_id}"


def test_ensure_user_row_idempotent_on_existing_user(db_session, test_user_id):
    """Repeat call on existing user returns immediately without adding credits."""
    # First call: user already exists (created by test_user_id fixture)
    _ensure_user_row(db_session, test_user_id, "existing@example.com")

    # Second call: also no-op
    _ensure_user_row(db_session, test_user_id, "existing@example.com")

    # test_user_id fixture does NOT grant credits, and _ensure_user_row should
    # skip the welcome grant because the user row already exists.
    ledger_entries = db_session.query(CreditLedger).filter_by(user_id=test_user_id).all()
    assert len(ledger_entries) == 0


def test_ensure_user_row_handles_integrity_error_race(db_session):
    """Concurrent first sign-in: IntegrityError on commit is swallowed gracefully."""
    new_user_id = "race-condition-user"

    # Patch db.commit to raise IntegrityError on the first call (simulating a
    # race where another request inserted the row between our SELECT and INSERT).
    original_commit = db_session.commit
    call_count = {"n": 0}

    def flaky_commit(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # Roll back manually so the session stays usable after the patch
            db_session.rollback()
            raise IntegrityError("statement", "params", Exception("duplicate key"))
        return original_commit(*args, **kwargs)

    with patch.object(db_session, "commit", side_effect=flaky_commit):
        # Should swallow the IntegrityError and return without raising
        _ensure_user_row(db_session, new_user_id, "race@example.com")

    # No exception raised = pass


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


def test_decode_supabase_jwt_valid_token_returns_claims(monkeypatch):
    """Valid token → claims dict with sub + email."""
    fake_signing_key = MagicMock()
    fake_signing_key.key = "fake-key"
    fake_client = MagicMock()
    fake_client.get_signing_key_from_jwt.return_value = fake_signing_key
    monkeypatch.setattr("app.core.auth._jwks_client", lambda: fake_client)

    # Patch jwt.decode to return canned claims
    monkeypatch.setattr(
        "app.core.auth.jwt.decode",
        lambda *a, **k: {"sub": "user-123", "email": "test@x.com", "aud": "authenticated"},
    )

    claims = decode_supabase_jwt("valid-token")
    assert claims["sub"] == "user-123"
    assert claims["email"] == "test@x.com"


# ---------------------------------------------------------------------------
# get_current_user_id + get_current_user_email dependency-injection tests
# ---------------------------------------------------------------------------


def test_get_current_user_id_returns_sub_claim(monkeypatch, db_session):
    """Valid bearer token → returns sub claim, ensures user row exists."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: {"sub": "user-from-jwt", "email": "jwt@x.com", "aud": "authenticated"},
    )

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")
    user_id = get_current_user_id(credentials=creds, db=db_session)

    assert user_id == "user-from-jwt"

    # Verify _ensure_user_row was called (user row was created)
    user = db_session.query(User).filter_by(user_id="user-from-jwt").first()
    assert user is not None


def test_get_current_user_id_raises_401_on_bad_token(monkeypatch, db_session):
    """Invalid token bubbles up as 401."""
    def raise_unauthorized(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    monkeypatch.setattr("app.core.auth.decode_supabase_jwt", raise_unauthorized)

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(credentials=creds, db=db_session)
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
        get_current_user_id(credentials=None, db=db_session)
    assert exc_info.value.status_code == 401


def test_get_current_user_id_raises_401_when_sub_missing(monkeypatch, db_session):
    """Token with no sub claim → 401."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: {"email": "no-sub@x.com", "aud": "authenticated"},
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-no-sub")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id(credentials=creds, db=db_session)
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
    result = get_optional_user_id(credentials=None, db=db_session)
    assert result is None


def test_get_optional_user_id_returns_user_id_on_valid_token(monkeypatch, db_session):
    """Valid token → returns sub claim."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: {"sub": "optional-user", "email": "opt@x.com", "aud": "authenticated"},
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
    result = get_optional_user_id(credentials=creds, db=db_session)
    assert result == "optional-user"


def test_get_optional_user_id_returns_none_on_bad_token(monkeypatch, db_session):
    """Invalid token → returns None (not 401)."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: (_ for _ in ()).throw(HTTPException(status_code=401, detail="bad")),
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")
    result = get_optional_user_id(credentials=creds, db=db_session)
    assert result is None


def test_get_authenticated_user_id_returns_sub_claim(monkeypatch, db_session):
    """Valid token through get_authenticated_user_id → returns sub."""
    monkeypatch.setattr(
        "app.core.auth.decode_supabase_jwt",
        lambda token: {"sub": "auth-user", "email": "auth@x.com", "aud": "authenticated"},
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="auth-token")
    result = get_authenticated_user_id(credentials=creds, db=db_session)
    assert result == "auth-user"


def test_get_authenticated_user_id_raises_401_when_no_credentials(db_session):
    """No credentials → 401 from get_authenticated_user_id."""
    with pytest.raises(HTTPException) as exc_info:
        get_authenticated_user_id(credentials=None, db=db_session)
    assert exc_info.value.status_code == 401
