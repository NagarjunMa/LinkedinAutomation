"""
Authentication utilities for JWT token validation with Supabase.

Supabase migrated from HS256 (shared secret) to ES256 (asymmetric, JWKS-based)
signing in 2026. We fetch public keys from the project's JWKS endpoint, cache
them, and verify access tokens against the matching `kid`.
"""

import jwt
import logging
import os
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError, PyJWKClient
from functools import lru_cache
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db

security = HTTPBearer(auto_error=False)

_auth_logger = logging.getLogger("auth")


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    """JWKS client for Supabase project. Lifespan controls cache TTL."""
    url = f"{os.environ['SUPABASE_URL'].rstrip('/')}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(url, cache_keys=True, lifespan=3600)


def decode_supabase_jwt(token: str) -> dict:
    """Decode and validate Supabase JWT (ES256, JWKS-based)."""
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
            options={"verify_aud": True, "verify_exp": True, "verify_iss": False},
        )
        return payload
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def _ensure_user_row(db: Session, user_id: str, email: str) -> None:
    """Upsert a ``users`` row for *user_id* and grant welcome credits on first contact.

    Idempotent: if the row already exists this is a no-op.  The welcome credit
    grant uses ``external_ref="welcome:<user_id>"`` which is UNIQUE-constrained
    in the credit_ledger table, so a duplicate grant attempt is silently ignored.
    """
    from app.models.user import User
    from app.services.credits.ledger import grant_monthly

    existing = db.query(User).filter(User.user_id == user_id).first()
    if existing:
        return

    # First contact — create the users row.
    try:
        db.add(User(user_id=user_id, email=email))
        db.commit()
    except IntegrityError:
        db.rollback()
        return  # Another concurrent request created the row; skip welcome grant

    # Grant 10 welcome credits.
    try:
        grant_monthly(db, user_id=user_id, amount=10,
                      external_ref=f"welcome:{user_id}")
        db.commit()
    except Exception as exc:
        # Don't fail auth if the grant fails (e.g. duplicate external_ref).
        db.rollback()
        _auth_logger.warning("Welcome credit grant failed for %s: %s", user_id, exc)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
) -> str:
    """Decode JWT, ensure a ``users`` row exists, and return the user ID.

    On first contact for a new OAuth user the row is created and 10 welcome
    credits are granted atomically before the user_id is returned.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token required")

    try:
        payload = decode_supabase_jwt(credentials.credentials)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

        email = payload.get("email") or f"{user_id}@unknown.local"
        _ensure_user_row(db, user_id, email)

        return user_id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db),
) -> Optional[str]:
    """Extract user ID from JWT token, but allow None for optional authentication."""
    if not credentials:
        return None

    try:
        payload = decode_supabase_jwt(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        email = payload.get("email") or f"{user_id}@unknown.local"
        _ensure_user_row(db, user_id, email)
        return user_id
    except HTTPException:
        return None


def get_current_user_email(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Extract user email from JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token required")

    try:
        payload = decode_supabase_jwt(credentials.credentials)
        email = payload.get("email")

        if not email:
            raise HTTPException(status_code=401, detail="Invalid token: missing email")

        return email
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# Main authentication dependency - use this in endpoints
def get_authenticated_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db),
) -> str:
    """Main authentication dependency for API endpoints.

    Requires proper authentication in all environments.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token required")

    payload = decode_supabase_jwt(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
    email = payload.get("email") or f"{user_id}@unknown.local"
    _ensure_user_row(db, user_id, email)
    return user_id