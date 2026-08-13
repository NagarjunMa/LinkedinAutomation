"""
Authentication utilities for JWT token validation with Supabase.

Supabase migrated from HS256 (shared secret) to ES256 (asymmetric, JWKS-based)
signing in 2026. We fetch public keys from the project's JWKS endpoint, cache
them, and verify access tokens against the matching `kid`.
"""

import jwt
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, Security, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError, PyJWKClient
from functools import lru_cache
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings

security = HTTPBearer(auto_error=False)

_auth_logger = logging.getLogger("auth")
_INVALID_TOKEN_DETAIL = "Invalid or expired authentication token"


def _supabase_issuer() -> str:
    return f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    """JWKS client for Supabase project. Lifespan controls cache TTL."""
    url = f"{_supabase_issuer()}/.well-known/jwks.json"
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
            issuer=_supabase_issuer(),
            options={
                "verify_aud": True,
                "verify_exp": True,
                "verify_iss": True,
                "require": ["aud", "exp", "iss", "sub"],
            },
        )
        return payload
    except PyJWTError as exc:
        _auth_logger.info("JWT verification rejected: %s", type(exc).__name__)
        raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL) from exc
    except Exception as exc:
        _auth_logger.exception("Supabase JWKS verification unavailable")
        raise HTTPException(
            status_code=503,
            detail="Authentication service unavailable",
        ) from exc


def _ensure_user_row(db: Session, user_id: str, email: str) -> None:
    """Upsert a ``users`` row for *user_id* and grant this month's freemium credits.

    The credit grant uses ``external_ref="monthly:YYYY-MM:<user_id>"`` which is
    UNIQUE-constrained in the credit_ledger table, so duplicate first-contact or
    monthly backfill attempts are safely ignored.
    """
    from app.models.user import User
    from app.services.credits.ledger import grant_monthly

    existing = db.query(User).filter(User.user_id == user_id).first()
    if not existing:
        try:
            db.add(User(user_id=user_id, email=email))
            db.commit()
        except IntegrityError:
            db.rollback()

    period = datetime.now(timezone.utc).strftime("%Y-%m")
    external_ref = f"monthly:{period}:{user_id}"
    try:
        grant_monthly(
            db,
            user_id=user_id,
            amount=settings.FREEMIUM_MONTHLY_CREDITS,
            external_ref=external_ref,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
    except Exception as exc:
        db.rollback()
        _auth_logger.warning("Freemium credit grant failed for %s: %s", user_id, exc)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
) -> str:
    """Decode JWT, ensure a ``users`` row exists, and return the user ID.

    On first contact for a new OAuth user the row is created and the current
    monthly freemium credits are granted before the user_id is returned.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token required")

    try:
        payload = decode_supabase_jwt(credentials.credentials)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL)

        email = payload.get("email") or f"{user_id}@unknown.local"
        _ensure_user_row(db, user_id, email)

        return user_id
    except HTTPException:
        raise
    except Exception as exc:
        _auth_logger.warning("Authentication dependency failed: %s", type(exc).__name__)
        raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL) from exc

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
            raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL)

        return email
    except HTTPException:
        raise
    except Exception as exc:
        _auth_logger.warning("Email claim extraction failed: %s", type(exc).__name__)
        raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL) from exc


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
        raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL)
    email = payload.get("email") or f"{user_id}@unknown.local"
    _ensure_user_row(db, user_id, email)
    return user_id


def require_path_user_matches_current(
    request: Request,
    current_user_id: str = Depends(get_current_user_id),
) -> str:
    """Require auth and reject routes whose path user_id targets another user."""
    path_user_id = request.path_params.get("user_id")
    if path_user_id and path_user_id != current_user_id:
        raise HTTPException(status_code=403, detail="User mismatch")
    return current_user_id


def require_admin_user(current_user_id: str = Depends(get_current_user_id)) -> str:
    """Require the authenticated user to be present in ADMIN_USER_IDS."""
    admins = {
        user_id.strip()
        for user_id in settings.ADMIN_USER_IDS.split(",")
        if user_id.strip()
    }
    if current_user_id not in admins:
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user_id
