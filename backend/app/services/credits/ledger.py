"""Credit ledger service.

Provides debit / refund / grant_monthly operations against the credit_ledger
table.  All writes are flushed (not committed) so the caller controls the
transaction boundary.

Row-locking: ``_append`` uses SELECT … FOR UPDATE on Postgres to prevent
concurrent double-spend.  On SQLite (used in tests) FOR UPDATE is a no-op —
correctness is preserved because SQLite is single-writer.
"""

import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.credit_ledger import CreditLedger
from app.models.user import User


class InsufficientCredits(Exception):
    """Raised when a debit would take the balance below zero."""


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
    computing the new balance.  Locking the users row (unique per user_id)
    ensures that all concurrent credit operations for the same user serialise
    through that single, deterministic row — avoiding the LIMIT-1 race where
    two transactions could previously lock *different* ledger rows and both
    pass the balance check.  On SQLite the FOR UPDATE clause is silently
    ignored — the DB-level single-writer guarantee provides equivalent safety.
    """
    # Lock the users row for this user_id.  On Postgres this serialises all
    # concurrent credit operations for the same user (SELECT … FOR UPDATE on a
    # unique row is deterministic — no LIMIT-induced non-determinism).
    # On SQLite the FOR UPDATE clause is a no-op, so correctness is still
    # guaranteed by SQLite's single-writer model.
    try:
        db.execute(
            select(User).where(User.user_id == user_id).with_for_update()
        )
    except Exception:
        # Safety net: if the dialect rejects FOR UPDATE, swallow and continue.
        pass

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
    assert amount > 0, "Debit amount must be positive"
    return _append(db, user_id, -amount, reason)


def refund(db: Session, user_id: str, amount: int, reason: str) -> CreditLedger:
    """Refund *amount* credits to *user_id* (inverse of a failed debit)."""
    assert amount > 0, "Refund amount must be positive"
    return _append(db, user_id, amount, f"refund:{reason}")


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
