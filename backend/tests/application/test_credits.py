from unittest.mock import MagicMock, patch

import pytest

from app.application.credits import paid_operation
from app.application.errors import CreditReconciliationError, InsufficientBalanceError
from app.services.credits.ledger import InsufficientCredits


def test_failed_debit_rolls_back_without_paid_work_or_refund():
    from sqlalchemy.exc import OperationalError
    from app.application.errors import ExternalServiceError

    session = MagicMock()
    failure = OperationalError("private SQL", {}, Exception("private database detail"))
    with patch("app.application.credits.debit", side_effect=failure), patch(
        "app.application.credits.refund"
    ) as refund:
        with pytest.raises(ExternalServiceError, match="Credit service unavailable") as caught:
            with paid_operation(session, "user-1", 2, "tailor"):
                pytest.fail("paid work must not start")
    assert caught.value.__cause__ is failure
    session.rollback.assert_called_once()
    session.commit.assert_not_called()
    refund.assert_not_called()


def test_unexpected_debit_failure_also_rolls_back():
    session = MagicMock()
    with patch("app.application.credits.debit", side_effect=ValueError("bad amount")):
        with pytest.raises(ValueError, match="bad amount"):
            with paid_operation(session, "user-1", 0, "tailor"):
                pytest.fail("paid work must not start")
    session.rollback.assert_called_once()


def test_credit_http_adapter_preserves_safe_database_failure():
    from fastapi import HTTPException
    from sqlalchemy.exc import OperationalError
    from app.middleware.credits import credit_transaction

    session = MagicMock()
    failure = OperationalError("private SQL", {}, Exception("private database detail"))
    with patch("app.application.credits.debit", side_effect=failure):
        with pytest.raises(HTTPException) as caught:
            with credit_transaction(session, "user-1", 2, "tailor"):
                pytest.fail("paid work must not start")
    assert caught.value.status_code == 503
    assert caught.value.detail == "Credit service unavailable"
    session.rollback.assert_called_once()


def test_paid_operation_maps_insufficient_balance_without_transport_error():
    session = MagicMock()
    with patch(
        "app.application.credits.debit",
        side_effect=InsufficientCredits("empty"),
    ):
        with pytest.raises(InsufficientBalanceError):
            with paid_operation(session, "user-1", 2, "tailor"):
                pytest.fail("operation must not start")
    session.rollback.assert_called_once()


def test_paid_operation_refunds_and_preserves_original_failure():
    session = MagicMock()
    with patch("app.application.credits.debit"), patch(
        "app.application.credits.refund"
    ) as refund:
        with pytest.raises(ValueError, match="provider failed"):
            with paid_operation(session, "user-1", 1, "evaluate"):
                raise ValueError("provider failed")
    refund.assert_called_once_with(
        session,
        user_id="user-1",
        amount=1,
        reason="evaluate",
    )
    assert session.commit.call_count == 2


def test_paid_operation_surfaces_failed_refund_for_reconciliation():
    session = MagicMock()
    with patch("app.application.credits.debit"), patch(
        "app.application.credits.refund",
        side_effect=RuntimeError("database unavailable"),
    ):
        with pytest.raises(CreditReconciliationError):
            with paid_operation(session, "user-1", 1, "export"):
                raise ValueError("render failed")
    session.rollback.assert_called_once()
