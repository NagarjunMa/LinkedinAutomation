"""Tests for the admin cost-per-user metrics endpoint (Task 11)."""
import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper: override get_current_user_id to a specific value
# ---------------------------------------------------------------------------

def _make_admin_client(db_session, admin_user_id: str, tmp_path):
    """Return a TestClient where the authed user is admin_user_id."""
    from unittest.mock import patch, MagicMock
    import sqlalchemy.sql.schema as _schema_mod
    from app.models.user import User

    # Ensure admin user row exists
    existing = db_session.query(User).filter_by(user_id=admin_user_id).first()
    if not existing:
        db_session.add(User(user_id=admin_user_id, email=f"{admin_user_id}@test.com"))
        db_session.commit()

    def _noop_create_all(self, bind=None, tables=None, checkfirst=False):
        pass

    with patch.object(_schema_mod.MetaData, "create_all", _noop_create_all):
        from fastapi.testclient import TestClient
        from app.main import app

    import app.db.session as _session_mod
    from app.core.auth import get_current_user_id
    from app.db.session import get_db

    def _override_get_db():
        yield db_session

    def _override_user():
        return admin_user_id

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user_id] = _override_user

    # Mock storage singleton so tests never hit Supabase
    import app.services.storage.supabase_storage as _storage_mod
    from pathlib import Path as _Path
    _original_singleton = _storage_mod._client_instance
    _mock_storage = MagicMock()
    _mock_storage.upload.side_effect = lambda user_id, file_id, content, filename: f"{user_id}/{file_id}_{filename}"
    fixture_path = _Path(__file__).parent.parent / "fixtures/resumes/simple.pdf"
    _mock_storage.download.return_value = fixture_path.read_bytes() if fixture_path.exists() else b"%PDF-stub"
    _storage_mod._client_instance = _mock_storage

    tc = TestClient(app)

    # Yield and then clean up
    return tc, app, get_db, get_current_user_id, _storage_mod, _original_singleton


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_admin_metrics_returns_cost_by_user(
    client: TestClient, db_session, test_user_id, monkeypatch
):
    """Admin user can view per-user debit totals."""
    from app.services.credits.ledger import grant_monthly, debit

    grant_monthly(db_session, test_user_id, 20)
    debit(db_session, test_user_id, 1, "evaluate")
    debit(db_session, test_user_id, 2, "tailor")
    db_session.commit()

    # Patch ADMIN_USER_IDS so test_user_id is considered admin
    monkeypatch.setenv("ADMIN_USER_IDS", test_user_id)

    resp = client.get("/api/v1/admin/metrics/cost-per-user")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "users" in data
    assert any(
        u["user_id"] == test_user_id and u["total_debited"] == 3
        for u in data["users"]
    ), f"Expected total_debited=3 for {test_user_id}; got: {data['users']}"


def test_admin_metrics_non_admin_gets_403(
    client: TestClient, db_session, test_user_id, monkeypatch
):
    """Non-admin user receives 403 Forbidden."""
    # Set ADMIN_USER_IDS to some other user, not test_user_id
    monkeypatch.setenv("ADMIN_USER_IDS", "some-other-admin-user")

    resp = client.get("/api/v1/admin/metrics/cost-per-user")
    assert resp.status_code == 403, resp.text


def test_admin_metrics_empty_admin_ids_gets_403(
    client: TestClient, db_session, test_user_id, monkeypatch
):
    """When ADMIN_USER_IDS is empty/unset, all users get 403."""
    monkeypatch.delenv("ADMIN_USER_IDS", raising=False)

    resp = client.get("/api/v1/admin/metrics/cost-per-user")
    assert resp.status_code == 403, resp.text
