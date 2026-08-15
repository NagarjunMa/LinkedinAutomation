"""Transport-neutral transaction boundary for paid application operations."""

import hashlib
import logging
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.application.errors import CreditReconciliationError, InsufficientBalanceError
from app.services.credits.ledger import InsufficientCredits, debit, refund


logger = logging.getLogger(__name__)


@contextmanager
def paid_operation(db: Session, user_id: str, amount: int, reason: str):
    try:
        debit(db, user_id=user_id, amount=amount, reason=reason)
        db.commit()
    except InsufficientCredits as exc:
        db.rollback()
        raise InsufficientBalanceError("Insufficient credits") from exc

    try:
        yield
    except Exception:
        try:
            refund(db, user_id=user_id, amount=amount, reason=reason)
            db.commit()
        except Exception as refund_error:
            db.rollback()
            logger.critical(
                "Paid operation refund requires reconciliation",
                extra={
                    "user_ref": hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:16],
                    "amount": amount,
                    "reason": reason,
                },
                exc_info=True,
            )
            raise CreditReconciliationError(
                "Credit refund requires reconciliation"
            ) from refund_error
        raise
