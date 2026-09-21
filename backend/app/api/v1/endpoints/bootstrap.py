"""Bearer-authenticated, idempotent session bootstrap."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.application.bootstrap import bootstrap_account
from app.application.errors import ExternalServiceError, ResourceConflictError
from app.core.auth import get_current_user_claims
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/bootstrap", status_code=204, response_class=Response)
def bootstrap(claims: dict = Depends(get_current_user_claims), db: Session = Depends(get_db)):
    # Never accept account identity or grant amounts from the request body.
    email = claims.get("email") or None
    if len(claims["sub"]) > 100 or (email is not None and (
        not isinstance(email, str) or len(email) > 255
    )):
        raise HTTPException(status_code=401, detail="Invalid account claims")
    try:
        bootstrap_account(db, user_id=claims["sub"], email=email)
    except ResourceConflictError as exc:
        raise HTTPException(status_code=409, detail="Account setup conflicts with existing data") from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=503, detail="Account setup service unavailable") from exc
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
