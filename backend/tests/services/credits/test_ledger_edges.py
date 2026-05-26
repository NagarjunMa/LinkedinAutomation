"""Edge cases for credit ledger — refund, insufficient balance, idempotency."""

import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import pytest
from sqlalchemy.orm import Session

from app.services.credits.ledger import (
    get_balance,
    debit,
    refund,
    grant_monthly,
    InsufficientCredits,
)


def test_debit_raises_insufficient_when_balance_zero(db_session: Session):
    """User with 0 credits (no ledger rows at all) cannot debit."""
    from app.models.user import User

    db_session.add(User(user_id="poor-user", email="poor@x.com"))
    db_session.commit()

    with pytest.raises(InsufficientCredits):
        debit(db_session, "poor-user", 1, "evaluate")


def test_refund_increases_balance(db_session: Session, test_user_id: str):
    """Refund adds credits back after a debit, restoring the original balance."""
    grant_monthly(db_session, test_user_id, 20)
    db_session.commit()
    initial = get_balance(db_session, test_user_id)

    debit(db_session, test_user_id, 5, "evaluate")
    db_session.commit()
    assert get_balance(db_session, test_user_id) == initial - 5

    refund(db_session, test_user_id, 5, "evaluate_refund")
    db_session.commit()
    assert get_balance(db_session, test_user_id) == initial


def test_grant_monthly_appends_credits(db_session: Session, test_user_id: str):
    """grant_monthly adds N credits on top of existing balance."""
    initial = get_balance(db_session, test_user_id)
    grant_monthly(db_session, test_user_id, 20)
    db_session.commit()
    assert get_balance(db_session, test_user_id) == initial + 20


def test_grant_monthly_with_external_ref_idempotent(db_session: Session, test_user_id: str):
    """Same external_ref must not result in a double-grant.

    The credit_ledger table has a UNIQUE constraint on external_ref.
    A second call with the same ref must either be silently skipped (service-
    level guard) or raise an IntegrityError that the caller catches.  Either
    way, the balance after the second call must equal the balance after the
    first call.
    """
    grant_monthly(db_session, test_user_id, 20, external_ref="stripe-inv-2026-05")
    db_session.commit()
    bal_after_first = get_balance(db_session, test_user_id)

    # Attempt re-grant with the same external_ref.
    # The DB unique constraint will raise; rollback so the session stays usable.
    try:
        grant_monthly(db_session, test_user_id, 20, external_ref="stripe-inv-2026-05")
        db_session.commit()
    except Exception:
        db_session.rollback()

    bal_after_second = get_balance(db_session, test_user_id)
    assert bal_after_first == bal_after_second
