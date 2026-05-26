"""Tests for app.services.payments.stripe_webhook_handler."""

import os

os.environ.setdefault("STRIPE_API_KEY", "sk_test_fake")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_fake")
os.environ.setdefault("OPENAI_API_KEY", "test")

import pytest
from unittest.mock import patch

from app.services.payments.stripe_webhook_handler import (
    verify_event, handle_event, _is_already_processed
)


def test_verify_event_raises_on_bad_signature():
    """Tampered payload or wrong signature → SignatureVerificationError."""
    import stripe
    payload = b'{"id":"evt_test","object":"event","type":"checkout.session.completed"}'
    bad_sig = "t=0,v1=invalid"

    with pytest.raises(stripe.error.SignatureVerificationError):
        verify_event(payload, bad_sig)


def test_verify_event_returns_event_for_valid_signature(monkeypatch):
    """Valid signature returns the constructed event."""
    import stripe

    fake_event = {"id": "evt_test_123", "type": "checkout.session.completed", "data": {}}
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda payload, sig, secret: fake_event)

    result = verify_event(b'{"x":"y"}', "valid-sig")
    assert result["id"] == "evt_test_123"


def test_handle_event_checkout_completed_grants_credits(db_session, test_user_id):
    """checkout.session.completed grants credits per metadata.credit_amount."""
    event = {
        "id": "evt_checkout_1",
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_test_1",
            "metadata": {
                "user_id": test_user_id,
                "credit_amount": "50",
            },
        }},
    }

    result = handle_event(db_session, event)
    # handler commits internally; no extra commit needed
    assert result["status"] == "ok"
    assert result["credits_granted"] == 50

    from app.services.credits.ledger import get_balance
    # test_user_id starts with 0 credits; +50 = 50
    assert get_balance(db_session, test_user_id) == 50


def test_handle_event_unknown_type_is_acked(db_session):
    """Non-billing event types return ack without action."""
    event = {
        "id": "evt_unknown_1",
        "type": "payment_method.attached",
        "data": {"object": {}},
    }
    result = handle_event(db_session, event)
    # ack with no error — status should be "ignored"
    assert result is not None
    assert result["status"] == "ignored"


def test_handle_event_idempotent_on_replay(db_session, test_user_id):
    """Same event_id replayed → second call detects already-processed, no double-grant."""
    event = {
        "id": "evt_idempotent_1",
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_idem_1",
            "metadata": {
                "user_id": test_user_id,
                "credit_amount": "30",
            },
        }},
    }

    result_first = handle_event(db_session, event)
    # handler commits internally
    assert result_first["status"] == "ok"

    from app.services.credits.ledger import get_balance
    balance_after_first = get_balance(db_session, test_user_id)
    assert balance_after_first == 30

    result_second = handle_event(db_session, event)
    assert result_second["status"] == "already_processed"

    balance_after_replay = get_balance(db_session, test_user_id)
    assert balance_after_first == balance_after_replay  # no double-grant


def test_handle_event_checkout_missing_user_id_is_ignored(db_session):
    """checkout.session.completed with no user_id in metadata → ignored."""
    event = {
        "id": "evt_no_user_1",
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_no_user_1",
            "metadata": {},  # no user_id
        }},
    }
    result = handle_event(db_session, event)
    assert result["status"] == "ignored"
    assert result.get("reason") == "no_user_id"


def test_handle_event_checkout_invalid_credit_amount_defaults_to_20(db_session, test_user_id):
    """Non-numeric credit_amount falls back to 20."""
    event = {
        "id": "evt_bad_amount_1",
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": "cs_bad_1",
            "metadata": {
                "user_id": test_user_id,
                "credit_amount": "not-a-number",
            },
        }},
    }
    result = handle_event(db_session, event)
    assert result["status"] == "ok"
    assert result["credits_granted"] == 20

    from app.services.credits.ledger import get_balance
    assert get_balance(db_session, test_user_id) == 20
