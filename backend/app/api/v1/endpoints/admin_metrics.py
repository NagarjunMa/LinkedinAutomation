"""Admin metrics endpoint — per-user credit debit totals.

GET /admin/metrics/cost-per-user
    Returns aggregated debit amounts per user from the credit_ledger table.
    Gated by require_admin dependency (ADMIN_USER_IDS env var allowlist).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.db.session import get_db
from app.core.auth import require_admin_user
from app.models.credit_ledger import CreditLedger

router = APIRouter(prefix="/admin/metrics", tags=["admin"])


@router.get("/cost-per-user")
def cost_per_user(
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_user),
):
    """Return per-user total debit amounts from the credit ledger.

    Aggregates all rows where delta < 0 (debits), summing -delta per user.
    Response shape: {"users": [{"user_id": str, "total_debited": int}, ...]}
    """
    rows = (
        db.query(
            CreditLedger.user_id,
            func.sum(
                case((CreditLedger.delta < 0, -CreditLedger.delta), else_=0)
            ).label("total_debited"),
        )
        .group_by(CreditLedger.user_id)
        .all()
    )
    return {
        "users": [
            {"user_id": row[0], "total_debited": int(row[1] or 0)}
            for row in rows
        ]
    }
