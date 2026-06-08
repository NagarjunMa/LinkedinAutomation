"""Integration tests: new-user bootstrap — freemium credits + empty profile.

These tests verify that:
1. _ensure_user_row creates a users row + grants 90 monthly credits on
   first call, and is idempotent on subsequent calls.
2. GET /api/v1/user-profiles/{user_id} returns 200 with exists=False for
   a user that has no UserProfile row yet.
"""

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.credits.ledger import grant_monthly, get_balance
from app.core.auth import _ensure_user_row


# ---------------------------------------------------------------------------
# Unit-level: _ensure_user_row
# ---------------------------------------------------------------------------


def test_ensure_user_row_creates_user_and_grants_monthly_credits(db_session: Session):
    """First call should insert users row and grant 90 monthly credits."""
    user_id = "new-user-bootstrap-1"
    email = "bootstrap1@example.com"

    assert db_session.query(User).filter(User.user_id == user_id).first() is None

    _ensure_user_row(db_session, user_id, email)

    user = db_session.query(User).filter(User.user_id == user_id).first()
    assert user is not None
    assert user.email == email

    balance = get_balance(db_session, user_id)
    assert balance == 90, f"Expected 90 monthly freemium credits, got {balance}"


def test_ensure_user_row_is_idempotent(db_session: Session):
    """Calling _ensure_user_row twice must NOT double-grant credits."""
    user_id = "new-user-bootstrap-2"
    email = "bootstrap2@example.com"

    _ensure_user_row(db_session, user_id, email)
    _ensure_user_row(db_session, user_id, email)  # second call — must be no-op

    balance = get_balance(db_session, user_id)
    assert balance == 90, f"Expected 90 credits after idempotent call, got {balance}"


def test_ensure_user_row_backfills_existing_user_current_month(db_session: Session):
    """Existing users receive the current monthly grant if it is missing."""
    user_id = "existing-user-no-grant"
    email = "existing@example.com"

    # Pre-insert the user row with 5 credits already.
    db_session.add(User(user_id=user_id, email=email))
    db_session.commit()
    grant_monthly(db_session, user_id=user_id, amount=5)
    db_session.commit()

    _ensure_user_row(db_session, user_id, email)
    _ensure_user_row(db_session, user_id, email)

    balance = get_balance(db_session, user_id)
    assert balance == 95, f"Expected existing 5 credits + 90 monthly credits, got {balance}"


# ---------------------------------------------------------------------------
# HTTP-level: empty profile for new users
# ---------------------------------------------------------------------------


def test_get_profile_returns_empty_for_new_user(client, db_session: Session, test_user_id: str):
    """GET /api/v1/user-profiles/{user_id} returns 200 with exists=False."""
    response = client.get(f"/api/v1/user-profiles/{test_user_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user_id"] == test_user_id
    assert data["exists"] is False
    assert data["full_name"] == ""
    assert data["programming_languages"] == []
    assert data["total_applications"] == 0
