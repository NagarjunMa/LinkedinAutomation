"""Tests for Stripe webhook receiver (Task 8).

Uses STRIPE_WEBHOOK_SECRET=test to bypass signature verification so we can
POST plain JSON without computing a real Stripe-Signature header.
"""
import os
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "test")

import json
import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.skipif(
    os.getenv("ENABLE_BILLING", "false").lower() != "true",
    reason="Stripe webhooks are dormant unless ENABLE_BILLING=true",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _checkout_event(event_id: str, user_id: str, amount: int = 20) -> dict:
    """Build a minimal checkout.session.completed Stripe event payload."""
    return {
        "id": event_id,
        "type": "checkout.session.completed",
        "object": "event",
        "data": {
            "object": {
                "id": f"cs_{event_id}",
                "object": "checkout.session",
                "metadata": {
                    "user_id": user_id,
                    "credit_amount": str(amount),
                },
                "payment_status": "paid",
            }
        },
    }


def _post_event(client: TestClient, payload: dict) -> object:
    return client.post(
        "/api/v1/webhooks/stripe",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json", "Stripe-Signature": "test"},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_first_event_grants_credits(
    client: TestClient, db_session, test_user_id
):
    """POSTing a checkout.session.completed event grants credits to the user."""
    from app.services.credits.ledger import get_balance

    payload = _checkout_event("evt_001", test_user_id, amount=20)
    resp = _post_event(client, payload)

    assert resp.status_code == 200, resp.text
    assert resp.json().get("status") == "ok"

    db_session.expire_all()
    assert get_balance(db_session, test_user_id) == 20


def test_replay_is_noop(
    client: TestClient, db_session, test_user_id
):
    """Replaying the same event_id must not grant credits a second time."""
    from app.services.credits.ledger import get_balance

    payload = _checkout_event("evt_002", test_user_id, amount=20)

    # First call
    resp1 = _post_event(client, payload)
    assert resp1.status_code == 200

    # Replay same event
    resp2 = _post_event(client, payload)
    assert resp2.status_code == 200
    assert resp2.json().get("status") == "already_processed"

    db_session.expire_all()
    # Balance should still be 20, not 40
    assert get_balance(db_session, test_user_id) == 20


def test_different_event_id_grants_again(
    client: TestClient, db_session, test_user_id
):
    """Two distinct event IDs each grant credits independently."""
    from app.services.credits.ledger import get_balance

    payload_a = _checkout_event("evt_003a", test_user_id, amount=20)
    payload_b = _checkout_event("evt_003b", test_user_id, amount=20)

    resp_a = _post_event(client, payload_a)
    resp_b = _post_event(client, payload_b)

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    assert resp_a.json().get("status") == "ok"
    assert resp_b.json().get("status") == "ok"

    db_session.expire_all()
    # Both grants applied: 20 + 20 = 40
    assert get_balance(db_session, test_user_id) == 40
