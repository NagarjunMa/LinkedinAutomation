"""Tests for monthly grant Celery task (Task 9).

Tests the pure-function ``grant_monthly_to_all`` using the conftest db_session
fixture so no real Celery/Redis is required.
"""
import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import pytest
from sqlalchemy.orm import Session


def _add_user(db: Session, user_id: str, email: str) -> None:
    """Helper: insert a user row directly."""
    from app.models.user import User
    u = User(user_id=user_id, email=email)
    db.add(u)
    db.commit()


def test_grant_monthly_to_all_grants_all_users(db_session: Session):
    """grant_monthly_to_all should grant credits to every user in the table."""
    from app.services.credits.ledger import get_balance
    from app.tasks.credit_tasks import grant_monthly_to_all

    # Arrange: two users, no prior credits
    _add_user(db_session, "user-grant-1", "u1@example.com")
    _add_user(db_session, "user-grant-2", "u2@example.com")

    # Act
    count = grant_monthly_to_all(db_session, amount=20)

    # Assert
    assert count == 2
    assert get_balance(db_session, "user-grant-1") == 20
    assert get_balance(db_session, "user-grant-2") == 20


def test_grant_monthly_to_all_returns_zero_when_no_users(db_session: Session):
    """Returns 0 when the users table is empty (no test_user_id fixture used)."""
    from app.tasks.credit_tasks import grant_monthly_to_all

    count = grant_monthly_to_all(db_session, amount=20)
    assert count == 0
