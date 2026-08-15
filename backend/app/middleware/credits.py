"""Credit middleware: context manager and endpoint decorator.

``credit_transaction`` is a synchronous context manager that:
  1. Debits *amount* credits from *user_id* on entry (and commits).
  2. Yields control to the caller.
  3. On any exception inside the block: issues a refund commit, then re-raises.
  4. Raises ``HTTPException(402)`` immediately when the user has insufficient
     credits (before yielding).
  5. Raises ``HTTPException(503)`` when a refund requires reconciliation.

``require_credits`` wraps an async FastAPI endpoint function.  It expects the
endpoint to accept ``db: Session`` and ``current_user_id: str`` keyword
arguments (injected by FastAPI's ``Depends`` in production; supplied directly
in tests).
"""

from contextlib import contextmanager
from functools import wraps

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.credits import paid_operation
from app.application.errors import CreditReconciliationError, InsufficientBalanceError


@contextmanager
def credit_transaction(db: Session, user_id: str, amount: int, reason: str):
    """HTTP compatibility adapter around the application credit boundary."""
    try:
        with paid_operation(db, user_id, amount, reason):
            yield
    except InsufficientBalanceError as exc:
        raise HTTPException(status_code=402, detail="Insufficient credits") from exc
    except CreditReconciliationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Credit refund requires reconciliation",
        ) from exc


def require_credits(amount: int, reason: str):
    """Decorator factory that wraps an async FastAPI endpoint.

    The decorated function must accept ``db: Session`` and
    ``current_user_id: str`` as keyword arguments.  In a real FastAPI app
    these are provided via ``Depends``; in tests they are passed directly.

    Usage::

        @router.post("/evaluate")
        @require_credits(amount=2, reason="evaluate")
        async def evaluate_resume(
            ...,
            db: Session = Depends(get_db),
            current_user_id: str = Depends(get_current_user_id),
        ):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, db: Session, current_user_id: str, **kwargs):
            with credit_transaction(db, current_user_id, amount, reason):
                return await func(*args, db=db, current_user_id=current_user_id, **kwargs)

        return wrapper

    return decorator
