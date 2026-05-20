"""Tests for the credit_transaction context manager and require_credits decorator.

Per the task instructions these are unit tests against the context manager
directly — no full FastAPI TestClient required.  Goals:
1. Debit happens on entry.
2. Refund happens on exception (balance restored).
3. HTTPException(402) raised on insufficient credits.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.credits.ledger import grant_monthly, get_balance
from app.middleware.credits import credit_transaction


# ---------------------------------------------------------------------------
# Helper: ensure a user has N credits before each test
# ---------------------------------------------------------------------------

def _grant(db: Session, user_id: str, amount: int) -> None:
    grant_monthly(db, user_id=user_id, amount=amount)
    db.commit()


# ---------------------------------------------------------------------------
# Test 1: debit happens on entry
# ---------------------------------------------------------------------------

def test_credit_transaction_debits_on_entry(db_session: Session, test_user_id: str):
    _grant(db_session, test_user_id, 10)

    with credit_transaction(db_session, test_user_id, 3, "evaluate"):
        # Inside the with-block the debit + commit have happened
        balance_inside = get_balance(db_session, test_user_id)

    assert balance_inside == 7, "Balance inside context should be 10-3=7"
    # Balance remains deducted after successful exit
    assert get_balance(db_session, test_user_id) == 7


# ---------------------------------------------------------------------------
# Test 2: refund happens on exception (balance restored)
# ---------------------------------------------------------------------------

def test_credit_transaction_refunds_on_exception(db_session: Session, test_user_id: str):
    _grant(db_session, test_user_id, 10)

    with pytest.raises(RuntimeError, match="simulated failure"):
        with credit_transaction(db_session, test_user_id, 3, "evaluate"):
            raise RuntimeError("simulated failure")

    # Refund should have restored balance to 10
    assert get_balance(db_session, test_user_id) == 10


# ---------------------------------------------------------------------------
# Test 3: HTTPException 402 raised on insufficient credits
# ---------------------------------------------------------------------------

def test_credit_transaction_raises_402_on_insufficient(db_session: Session, test_user_id: str):
    _grant(db_session, test_user_id, 1)

    with pytest.raises(HTTPException) as exc_info:
        with credit_transaction(db_session, test_user_id, 5, "evaluate"):
            pass  # should never reach here

    assert exc_info.value.status_code == 402
    # Balance unchanged
    assert get_balance(db_session, test_user_id) == 1


# ---------------------------------------------------------------------------
# Test 4: balance unchanged after 402 (no partial debit persisted)
# ---------------------------------------------------------------------------

def test_credit_transaction_no_partial_debit_on_402(db_session: Session, test_user_id: str):
    _grant(db_session, test_user_id, 2)

    with pytest.raises(HTTPException):
        with credit_transaction(db_session, test_user_id, 10, "tailor"):
            pass

    assert get_balance(db_session, test_user_id) == 2


# ---------------------------------------------------------------------------
# Test 5: refund does not swallow the original exception
# ---------------------------------------------------------------------------

def test_credit_transaction_reraises_original_exception(db_session: Session, test_user_id: str):
    _grant(db_session, test_user_id, 10)

    with pytest.raises(ValueError, match="downstream error"):
        with credit_transaction(db_session, test_user_id, 2, "tailor"):
            raise ValueError("downstream error")

    # Balance should be restored
    assert get_balance(db_session, test_user_id) == 10


# ---------------------------------------------------------------------------
# Test 6: require_credits decorator — async endpoint happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_require_credits_decorator_success(db_session: Session, test_user_id: str):
    from app.middleware.credits import require_credits

    _grant(db_session, test_user_id, 10)

    @require_credits(amount=2, reason="evaluate")
    async def fake_endpoint(db: Session, current_user_id: str):
        return {"ok": True}

    result = await fake_endpoint(db=db_session, current_user_id=test_user_id)
    assert result == {"ok": True}
    assert get_balance(db_session, test_user_id) == 8


# ---------------------------------------------------------------------------
# Test 7: require_credits decorator — refund on endpoint exception
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_require_credits_decorator_refund_on_failure(db_session: Session, test_user_id: str):
    from app.middleware.credits import require_credits

    _grant(db_session, test_user_id, 10)

    @require_credits(amount=2, reason="evaluate")
    async def failing_endpoint(db: Session, current_user_id: str):
        raise RuntimeError("AI call failed")

    with pytest.raises(RuntimeError, match="AI call failed"):
        await failing_endpoint(db=db_session, current_user_id=test_user_id)

    assert get_balance(db_session, test_user_id) == 10
