"""Stripe webhook receiver endpoint.

POST /webhooks/stripe
  - Verifies the Stripe-Signature header (bypassed in test mode).
  - Delegates to the stripe_webhook_handler service.
  - Always returns HTTP 200 so Stripe doesn't retry on expected no-ops.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.session import get_db
from app.services.payments.stripe_webhook_handler import verify_event, handle_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Receive and process Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = verify_event(payload, sig_header)
    except Exception as exc:
        logger.warning("Stripe webhook signature verification failed: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid signature")

    result = handle_event(db, event)
    return result
