"""Explicit account initialization; the database job owns recurring grants."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.application.errors import ExternalServiceError, ResourceConflictError
from app.core.config import settings
from app.models.user import User
from app.services.credits.ledger import grant_monthly

logger = logging.getLogger(__name__)


def bootstrap_account(db: Session, *, user_id: str, email: str | None) -> None:
    """Own one transaction: create an account and its first monthly allowance.

    A skipped insert is successful only if this identity exists. PostgreSQL can
    detect either unique key (email or user_id) first during simultaneous inserts,
    so handle both and verify identity rather than swallowing an email collision.
    """
    try:
        insert = sqlite_insert if db.get_bind().dialect.name == "sqlite" else pg_insert
        created = db.execute(
            insert(User).values(user_id=user_id, email=email)
            .on_conflict_do_nothing()
            .returning(User.user_id)
        ).scalar_one_or_none()
        if created is None:
            if db.scalar(select(User.user_id).where(User.user_id == user_id)) is None:
                db.rollback()
                raise ResourceConflictError("Account setup conflicts with existing data")
        else:
            period = datetime.now(timezone.utc).strftime("%Y-%m")
            grant_monthly(
                db, user_id=user_id, amount=settings.FREEMIUM_MONTHLY_CREDITS,
                external_ref=f"monthly:{period}:{user_id}",
            )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.warning("Account bootstrap constraint conflict")
        raise ResourceConflictError("Account setup conflicts with existing data") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.warning("Account bootstrap database unavailable: %s", type(exc).__name__)
        raise ExternalServiceError("Account setup service unavailable") from exc
