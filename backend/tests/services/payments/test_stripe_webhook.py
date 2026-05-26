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
