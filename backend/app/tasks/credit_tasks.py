"""Monthly credit grant tasks.

Provides:
- ``grant_monthly_to_all(db, amount=20) -> int``
    Pure function that iterates all users and grants *amount* credits to each.
    Returns the number of users granted.  Testable without Celery or Redis.

- ``grant_monthly_celery_task()``
    Celery task wrapper that opens its own DB session, calls
    ``grant_monthly_to_all``, and commits/closes on completion.
    Scheduled via celery beat to run at midnight UTC on the 1st of each month.
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.services.credits.ledger import grant_monthly
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


def grant_monthly_to_all(db: Session, amount: int = 20) -> int:
    """Grant *amount* credits to every user in the database.

    This is a pure function that accepts a *db* session so it can be tested
    directly using the conftest ``db_session`` fixture without any Celery
    infrastructure.

    Returns the number of users that received a grant.
    """
    users = db.execute(select(User)).scalars().all()
    count = 0
    for user in users:
        try:
            grant_monthly(db, user_id=user.user_id, amount=amount)
            count += 1
        except Exception as exc:
            logger.warning(
                "Failed to grant credits to user %s: %s", user.user_id, exc
            )
    db.commit()
    return count


@celery_app.task(name="credits.grant_monthly")
def grant_monthly_celery_task() -> int:
    """Celery task: grant monthly credits to all users.

    Opens its own DB session (SessionLocal) so it runs independently of any
    request-scoped session.  Do not test this wrapper directly — test the
    ``grant_monthly_to_all`` pure function instead.
    """
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        count = grant_monthly_to_all(db, amount=20)
        logger.info("Monthly grant completed: %d users credited", count)
        return count
    except Exception:
        logger.exception("Monthly grant task failed")
        raise
    finally:
        db.close()
