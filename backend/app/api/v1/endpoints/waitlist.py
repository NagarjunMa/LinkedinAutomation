"""Public, unauthenticated, narrowly scoped private-preview waitlist route."""

from datetime import datetime, timedelta, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.waitlist_entry import WaitlistEntry
from app.schemas.waitlist import WaitlistCreate, WaitlistResponse


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/waitlist", tags=["waitlist"])


def _success_response() -> WaitlistResponse:
    # New and duplicate submissions deliberately receive the same response.
    return WaitlistResponse()


@router.post("", response_model=WaitlistResponse, status_code=status.HTTP_202_ACCEPTED)
def join_private_preview(
    payload: WaitlistCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> WaitlistResponse:
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"

    # Honeypot submissions look successful to automated clients but are not stored.
    if payload.company_website:
        return _success_response()

    normalized_email = str(payload.email).strip().casefold()
    consented_at = datetime.now(timezone.utc)

    try:
        existing = (
            db.query(WaitlistEntry.id)
            .filter(WaitlistEntry.normalized_email == normalized_email)
            .first()
        )
        if existing:
            return _success_response()

        db.add(
            WaitlistEntry(
                normalized_email=normalized_email,
                career_stage=(
                    payload.career_stage.value if payload.career_stage else None
                ),
                target_role=payload.target_role,
                communication_challenge=payload.communication_challenge,
                consent_granted=True,
                consent_version=settings.WAITLIST_CONSENT_VERSION,
                consented_at=consented_at,
                retention_expires_at=consented_at
                + timedelta(days=settings.WAITLIST_RETENTION_DAYS),
            )
        )
        db.commit()
        logger.info(
            "Waitlist submission accepted",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
    except IntegrityError:
        # A concurrent request may win the uniqueness race. Preserve the neutral,
        # idempotent public response instead of disclosing membership.
        db.rollback()
    except SQLAlchemyError as exc:
        db.rollback()
        # Some SQLAlchemy exception strings include bound query parameters. Do not
        # attach the exception or statement here because the email is personal data.
        logger.error(
            "Waitlist persistence failed",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The waitlist is temporarily unavailable. Please try again later.",
        )

    return _success_response()
