"""Stripe webhook handler.

Provides:
- ``verify_event`` — validates Stripe-Signature; when
  STRIPE_WEBHOOK_SECRET == "test" the signature check is skipped so tests
  can POST plain JSON without computing a real HMAC.
- ``handle_event`` — dispatches to the correct business-logic handler.
  Currently handles ``checkout.session.completed`` events to grant credits.
  Returns a dict with ``status``: "ok" | "already_processed" | "ignored".

Idempotency strategy: before calling ``grant_monthly`` we check whether a
``credit_ledger`` row with ``external_ref == event.id`` already exists.  If
it does, we return "already_processed".  This avoids relying on catching an
IntegrityError, which would leave the SQLAlchemy session in a broken state.
"""

import json
import os
import logging
from typing import Any

import stripe
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.credit_ledger import CreditLedger
from app.services.credits.ledger import grant_monthly

logger = logging.getLogger(__name__)

_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
_TEST_MODE = _WEBHOOK_SECRET == "test"


def verify_event(payload: bytes, sig_header: str) -> dict:
    """Parse and verify a Stripe webhook payload.

    In test mode (STRIPE_WEBHOOK_SECRET == "test"), signature verification is
    skipped and the raw JSON is returned as a dict.

    Raises:
        stripe.error.SignatureVerificationError: when signature is invalid in
            production mode.
        ValueError: when the payload is not valid JSON (test mode only).
    """
    if _TEST_MODE:
        return json.loads(payload)

    event = stripe.Webhook.construct_event(
        payload, sig_header, _WEBHOOK_SECRET
    )
    return event


def _is_already_processed(db: Session, event_id: str) -> bool:
    """Return True if a ledger row with external_ref == event_id already exists."""
    row = db.execute(
        select(CreditLedger).where(CreditLedger.external_ref == event_id)
    ).scalar_one_or_none()
    return row is not None


def handle_event(db: Session, event: Any) -> dict:
    """Dispatch a verified Stripe event to the appropriate handler.

    Returns a dict with at least a ``"status"`` key.
    """
    event_type = event.get("type") if isinstance(event, dict) else event.type
    event_id = event.get("id") if isinstance(event, dict) else event.id

    if event_type == "checkout.session.completed":
        return _handle_checkout_completed(db, event, event_id)

    # Unknown / unhandled events are silently ignored
    logger.info("Unhandled Stripe event type: %s", event_type)
    return {"status": "ignored", "event_type": event_type}


def _handle_checkout_completed(db: Session, event: Any, event_id: str) -> dict:
    """Grant credits for a successful checkout session.

    Reads ``user_id`` and ``credit_amount`` from the session's metadata.
    Falls back to 90 credits if ``credit_amount`` is absent.
    """
    # Support both dict (test mode) and Stripe object (production)
    if isinstance(event, dict):
        session_obj = event["data"]["object"]
        metadata = session_obj.get("metadata", {})
    else:
        session_obj = event.data.object
        metadata = session_obj.metadata or {}

    user_id = metadata.get("user_id")
    if not user_id:
        logger.warning("checkout.session.completed missing user_id in metadata")
        return {"status": "ignored", "reason": "no_user_id"}

    try:
        amount = int(metadata.get("credit_amount", 90))
    except (ValueError, TypeError):
        amount = 90

    # Idempotency check
    if _is_already_processed(db, event_id):
        logger.info("Stripe event %s already processed — skipping", event_id)
        return {"status": "already_processed", "event_id": event_id}

    grant_monthly(db, user_id=user_id, amount=amount, external_ref=event_id)
    db.commit()

    logger.info(
        "Granted %d credits to user %s via Stripe event %s",
        amount, user_id, event_id,
    )
    return {"status": "ok", "event_id": event_id, "credits_granted": amount}
