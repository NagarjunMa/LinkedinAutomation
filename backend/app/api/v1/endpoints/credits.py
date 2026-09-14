"""Credits balance endpoint (Task 19)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.services.credits.ledger import get_balance
from app.api.response_contracts import PrivateResponseRoute
from app.schemas.workflow_responses import CreditBalanceResponse

router = APIRouter(prefix="/credits", tags=["credits"], route_class=PrivateResponseRoute)


@router.get("/balance", response_model=CreditBalanceResponse)
def balance(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """GET /credits/balance — return current credit balance for authenticated user."""
    return {"balance": get_balance(db, current_user_id)}
