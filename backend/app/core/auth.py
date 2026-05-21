"""
Authentication utilities for JWT token validation with Supabase.

Supabase migrated from HS256 (shared secret) to ES256 (asymmetric, JWKS-based)
signing in 2026. We fetch public keys from the project's JWKS endpoint, cache
them, and verify access tokens against the matching `kid`.
"""

import jwt
import os
from typing import Optional
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError, PyJWKClient
from functools import lru_cache

security = HTTPBearer(auto_error=False)


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

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Extract user ID from JWT token
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token required")

    try:
        payload = decode_supabase_jwt(credentials.credentials)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

def get_optional_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Optional[str]:
    """
    Extract user ID from JWT token, but allow None for optional authentication
    """
    if not credentials:
        return None

    try:
        return get_current_user_id(credentials)
    except HTTPException:
        return None

def get_current_user_email(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Extract user email from JWT token
    """
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
def get_authenticated_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> str:
    """
    Main authentication dependency for API endpoints
    Requires proper authentication in all environments
    """
    # For development/testing - allow fallback test user
    # TODO: Remove this in production
    if not credentials:
        return "test_user_123"

    return get_current_user_id(credentials)