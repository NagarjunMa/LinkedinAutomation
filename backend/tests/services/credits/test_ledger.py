import pytest
import sys
import os
from sqlalchemy.orm import Session
from app.services.credits.ledger import (
    get_balance, debit, refund, grant_monthly, InsufficientCredits
)
from app.models.credit_ledger import CreditLedger

# ---------------------------------------------------------------------------
# Basic ledger operations
# ---------------------------------------------------------------------------

def test_grant_then_balance(db_session: Session, test_user_id: str):
    grant_monthly(db_session, user_id=test_user_id, amount=20)
    assert get_balance(db_session, test_user_id) == 20


def test_debit_reduces_balance(db_session: Session, test_user_id: str):
    grant_monthly(db_session, user_id=test_user_id, amount=20)
    debit(db_session, user_id=test_user_id, amount=2, reason="tailor")
    assert get_balance(db_session, test_user_id) == 18


def test_debit_raises_on_insufficient(db_session: Session, test_user_id: str):
    grant_monthly(db_session, user_id=test_user_id, amount=1)
    with pytest.raises(InsufficientCredits):
        debit(db_session, user_id=test_user_id, amount=5, reason="tailor")


def test_refund_increases_balance(db_session: Session, test_user_id: str):
    grant_monthly(db_session, user_id=test_user_id, amount=20)
    debit(db_session, user_id=test_user_id, amount=2, reason="tailor")
    refund(db_session, user_id=test_user_id, amount=2, reason="tailor_failed")
    assert get_balance(db_session, test_user_id) == 20


def test_balance_zero_for_new_user(db_session: Session, test_user_id: str):
    assert get_balance(db_session, test_user_id) == 0


def test_multiple_debits_accumulate(db_session: Session, test_user_id: str):
    grant_monthly(db_session, user_id=test_user_id, amount=10)
    debit(db_session, user_id=test_user_id, amount=3, reason="evaluate")
    debit(db_session, user_id=test_user_id, amount=3, reason="tailor")
    assert get_balance(db_session, test_user_id) == 4


def test_debit_does_not_commit_on_insufficient(db_session: Session, test_user_id: str):
    """Balance must remain unchanged when InsufficientCredits is raised."""
    grant_monthly(db_session, user_id=test_user_id, amount=5)
    with pytest.raises(InsufficientCredits):
        debit(db_session, user_id=test_user_id, amount=10, reason="tailor")
    # Balance unchanged
    assert get_balance(db_session, test_user_id) == 5


# ---------------------------------------------------------------------------
# Concurrent-debit test — skip on SQLite (no real row-lock support)
# ---------------------------------------------------------------------------

_is_sqlite = True  # using SQLite in-memory for tests


@pytest.mark.skipif(_is_sqlite, reason="with_for_update() is a no-op on SQLite; test requires Postgres")
def test_concurrent_debit_prevented(db_session: Session, test_user_id: str):
    """Two threads both try to debit 10 from a balance of 15 — only one should succeed."""
    import threading
    grant_monthly(db_session, user_id=test_user_id, amount=15)
    db_session.commit()

    results = []

    def do_debit():
        try:
            debit(db_session, user_id=test_user_id, amount=10, reason="concurrent")
            db_session.commit()
            results.append("ok")
        except InsufficientCredits:
            results.append("insufficient")
        except Exception as e:
            results.append(f"error:{e}")

    t1 = threading.Thread(target=do_debit)
    t2 = threading.Thread(target=do_debit)
    t1.start(); t2.start()
    t1.join(); t2.join()

    assert results.count("ok") == 1
    assert results.count("insufficient") == 1


# ---------------------------------------------------------------------------
# New Postgres-only concurrent-debit test (row-lock on users row)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    "postgres" not in os.getenv("DATABASE_URL", ""),
    reason="requires Postgres for SELECT FOR UPDATE on users row",
)
def test_concurrent_debits_do_not_double_spend(db_session: Session, test_user_id: str):
    """Two threads each try to debit 3 from a balance of 5.
    With the correct users-row lock, exactly one succeeds and one gets
    InsufficientCredits (5 - 3 = 2 < 3).
    """
    import threading
    grant_monthly(db_session, user_id=test_user_id, amount=5)
    db_session.commit()

    errors = []

    def do_debit():
        try:
            debit(db_session, user_id=test_user_id, amount=3, reason="test")
            db_session.commit()
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=do_debit)
    t2 = threading.Thread(target=do_debit)
    t1.start(); t2.start()
    t1.join(); t2.join()

    assert sum(isinstance(e, InsufficientCredits) for e in errors) == 1
