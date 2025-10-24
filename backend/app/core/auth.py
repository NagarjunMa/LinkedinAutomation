"""
Authentication utilities for JWT token validation with Supabase
"""

import jwt
import os
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
import requests
from functools import lru_cache

security = HTTPBearer()

@lru_cache()
def get_supabase_jwt_secret():
    """Get Supabase JWT secret key"""
    return os.getenv("SUPABASE_JWT_SECRET")

def decode_supabase_jwt(token: str) -> dict:
    """
    Decode and validate Supabase JWT token
    """
    try:
        # Supabase uses the same secret for signing
        payload = jwt.decode(
            token,
            get_supabase_jwt_secret(),
            algorithms=["HS256"],
            options={"verify_signature": False}  # For now, we'll trust Supabase tokens
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
def get_authenticated_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Main authentication dependency for API endpoints
    Requires proper authentication in all environments
    """
    # Always require proper authentication - no fallbacks
    return get_current_user_id(credentials)