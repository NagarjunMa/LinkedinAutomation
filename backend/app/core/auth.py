"""
Authentication utilities for JWT token validation with Supabase.

Supabase migrated from HS256 (shared secret) to ES256 (asymmetric, JWKS-based)
signing in 2026. We fetch public keys from the project's JWKS endpoint, cache
them, and verify access tokens against the matching `kid`.
"""

import jwt
import logging
from typing import Optional
from fastapi import HTTPException, Security, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError, PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError
from functools import lru_cache

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
    except PyJWKClientConnectionError as exc:
        _auth_logger.warning("Supabase JWKS connection unavailable")
        raise HTTPException(status_code=503, detail="Authentication service unavailable") from exc
    except PyJWTError as exc:
        _auth_logger.info("JWT verification rejected: %s", type(exc).__name__)
        raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL) from exc
    except Exception as exc:
        _auth_logger.exception("Supabase JWKS verification unavailable")
        raise HTTPException(
            status_code=503,
            detail="Authentication service unavailable",
        ) from exc


def get_current_user_claims(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    """Validate identity without accessing application storage."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token required")
    payload = decode_supabase_jwt(credentials.credentials)
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL)
    return payload


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """Return the verified identity; account setup is an explicit use case."""
    return get_current_user_claims(credentials)["sub"]


def get_optional_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Optional[str]:
    """Allow anonymous access only when no Authorization header was supplied."""
    # HTTPBearer(auto_error=False) also returns None for malformed/non-Bearer
    # headers. Those are rejected credentials, not an anonymous request.
    if "authorization" not in request.headers:
        return None
    if not credentials:
        raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL)
    return get_current_user_id(credentials)


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
) -> str:
    """Main authentication dependency for API endpoints.

    Requires proper authentication in all environments.
    """
    return get_current_user_id(credentials)


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
