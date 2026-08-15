from unittest.mock import MagicMock, patch

import pytest

from app.application.credits import paid_operation
from app.application.errors import CreditReconciliationError, InsufficientBalanceError
from app.services.credits.ledger import InsufficientCredits


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
