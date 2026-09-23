"""Fail-closed credit preconditions; SQLite does not prove row serialization."""

import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import NoResultFound

from app.core.config import settings
from app.models.credit_ledger import CreditLedger
from app.services.credits.ledger import debit, refund, grant_monthly


@pytest.mark.parametrize("operation", [debit, refund])
@pytest.mark.parametrize("amount", [0, -1, True, False, 1.5, "1", None])
def test_invalid_amount_never_accesses_database(operation, amount):
    db = MagicMock()
    with pytest.raises(ValueError, match="amount must be a positive integer"):
        operation(db, "alice", amount, "test")
    assert db.mock_calls == []


def test_invalid_amounts_are_rejected_under_optimized_python():
    code = '''
from app.services.credits.ledger import debit, refund
for operation in (debit, refund):
    for amount in (0, -1, True, False, 1.5, "1", None):
        try:
            operation(None, "alice", amount, "test")
        except ValueError as exc:
            if "amount must be a positive integer" not in str(exc):
                raise RuntimeError("unstable error") from exc
        else:
            raise RuntimeError("invalid amount accepted")
print("all invalid amounts rejected")
'''
    env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT") if key in os.environ}
    env.update(OPENAI_API_KEY="test", SUPABASE_URL="https://test.supabase.co",
               SUPABASE_ANON_KEY="test", SUPABASE_SERVICE_ROLE_KEY="test",
               SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", ENVIRONMENT="test")
    result = subprocess.run([sys.executable, "-O", "-c", code],
                            cwd=Path(__file__).parents[3], env=env,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "all invalid amounts rejected"


def test_lock_exception_stops_before_balance_query_or_write():
    db = MagicMock()
    db.get_bind.return_value.dialect.name = "postgresql"
    db.connection.return_value.get_isolation_level.return_value = "READ COMMITTED"
    db.connection.return_value.connection.dbapi_connection.autocommit = False
    error = RuntimeError("lock transport failure")
    db.execute.side_effect = [error, MagicMock(scalar=lambda: 10)]
    with pytest.raises(RuntimeError, match="lock transport failure"):
        debit(db, "alice", 1, "test")
    assert db.execute.call_count == 1
    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_missing_user_does_not_create_orphan_grant(db_session):
    with pytest.raises(NoResultFound):
        grant_monthly(db_session, "missing", 5)
    assert db_session.query(CreditLedger).count() == 0


@pytest.mark.parametrize("environment", ["development", "test"])
def test_sqlite_supported_local_modes(db_session, test_user_id, monkeypatch, environment):
    monkeypatch.setattr(settings, "ENVIRONMENT", environment)
    assert grant_monthly(db_session, test_user_id, 5).balance_after == 5


def test_sqlite_not_allowed_in_production(db_session, test_user_id, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="SQLite credit writes"):
        grant_monthly(db_session, test_user_id, 5)
    assert db_session.query(CreditLedger).count() == 0


def test_unknown_dialect_never_falls_back_to_unlocked_write():
    db = MagicMock()
    db.get_bind.return_value.dialect.name = "mysql"
    with pytest.raises(RuntimeError, match="Unsupported credit database"):
        grant_monthly(db, "alice", 5)
    db.execute.assert_not_called()
    db.add.assert_not_called()
