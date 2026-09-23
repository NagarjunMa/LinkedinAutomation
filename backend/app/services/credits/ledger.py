"""Credit ledger service.

Provides debit / refund / grant_monthly operations against the credit_ledger
table.  All writes are flushed (not committed) so the caller controls the
transaction boundary.

PostgreSQL writes require a users-row lock in a READ COMMITTED transaction.
SQLite is supported only for sequential local development/tests, not as proof
of production concurrency safety. Lock failures always propagate to the caller.
"""

import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.credit_ledger import CreditLedger
from app.models.user import User


class InsufficientCredits(Exception):
    """Raised when a debit would take the balance below zero."""


class CreditLockUnavailable(RuntimeError):
    """The configured database cannot provide the required credit write boundary."""


def validate_credit_transaction(db: Session) -> str:
    """Require a supported write transaction before any caller-owned mutation.

    Return the validated dialect for callers that also insert the account.
    """
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        connection = db.connection()
        # get_isolation_level() alone does not report DBAPI autocommit. The
        # supported synchronous PostgreSQL driver (psycopg2) exposes it here.
        if (connection.connection.dbapi_connection.autocommit
                or connection.get_isolation_level() != "READ COMMITTED"):
            raise CreditLockUnavailable("Credit writes require transactional READ COMMITTED")
    elif dialect == "sqlite":
        if settings.ENVIRONMENT.lower() not in {"development", "test"}:
            raise CreditLockUnavailable("SQLite credit writes are limited to development/test")
    else:
        raise CreditLockUnavailable("Unsupported credit database")
    return dialect


def _lock_user(db: Session, user_id: str) -> None:
    dialect = validate_credit_transaction(db)
    statement = select(User.user_id).where(User.user_id == user_id)
    if dialect == "postgresql":
        statement = statement.with_for_update()
    # A successful SELECT with no matching row provides no lock. Missing users
    # and database errors must escape before balance calculation or appending.
    db.execute(statement).scalar_one()


def get_balance(db: Session, user_id: str) -> int:
    """Return the current credit balance for *user_id*.

    Computed as SUM(delta) across all ledger rows for the user.  This is the
    authoritative calculation and is robust to ties in ``created_at``
    (relevant on SQLite where timestamps have 1-second resolution).

    On Postgres, ``balance_after`` on the latest row could be used as a
    performance optimisation — but SUM is fast enough for typical ledger sizes
    and avoids ordering ambiguity.

    Returns 0 if the user has no rows yet.
    """
    result = db.execute(
        select(func.sum(CreditLedger.delta))
        .where(CreditLedger.user_id == user_id)
    ).scalar()
    # func.sum returns None when there are no rows
    return int(result) if result is not None else 0


def _append(
    db: Session,
    user_id: str,
    delta: int,
    reason: str,
    external_ref: str | None = None,
) -> CreditLedger:
    """Low-level: append one ledger row and flush (no commit).

    Acquires a row-level lock on the ``users`` row for *user_id* before
    computing the new balance. Every Python ledger write for the same user
    serializes through this row; READ COMMITTED gives the subsequent balance
    query a fresh snapshot after waiting. The caller must roll back on failure.
    """
    _lock_user(db, user_id)

    balance = get_balance(db, user_id)
    new_balance = balance + delta

    if new_balance < 0:
        raise InsufficientCredits(
            f"User {user_id} has {balance} credit(s), requested {-delta}"
        )

    entry = CreditLedger(
        id=str(uuid.uuid4()),
        user_id=user_id,
        delta=delta,
        reason=reason,
        balance_after=new_balance,
        external_ref=external_ref,
    )
    db.add(entry)
    db.flush()
    return entry


def debit(db: Session, user_id: str, amount: int, reason: str) -> CreditLedger:
    """Debit *amount* credits from *user_id*.  Raises InsufficientCredits if
    the resulting balance would be negative."""
    _validate_amount(amount, "Debit")
    return _append(db, user_id, -amount, reason)


def refund(db: Session, user_id: str, amount: int, reason: str) -> CreditLedger:
    """Refund *amount* credits to *user_id* (inverse of a failed debit)."""
    _validate_amount(amount, "Refund")
    return _append(db, user_id, amount, f"refund:{reason}")


def _validate_amount(amount: int, operation: str) -> None:
    if type(amount) is not int or amount <= 0:
        raise ValueError(f"{operation} amount must be a positive integer")


def grant_monthly(
    db: Session,
    user_id: str,
    amount: int = 90,
    external_ref: str | None = None,
) -> CreditLedger:
    """Grant *amount* credits to *user_id* (monthly allowance or manual grant).

    *external_ref* should be set for idempotency.
    """
    return _append(db, user_id, amount, "grant", external_ref=external_ref)
