"""
Authentication and security utilities.

Supports two modes:
  1. Supabase Auth (production) — verifies Supabase JWTs
  2. Dev mode (no Supabase) — allows unauthenticated access with a default user
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from app.config import settings
import structlog

logger = structlog.get_logger()

# FastAPI security scheme — extracts Bearer token from Authorization header
security = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """Represents the authenticated user extracted from the JWT."""
    id: str
    email: Optional[str] = None
    role: str = "user"


def _verify_supabase_jwt(token: str) -> dict:
    """Verify a Supabase JWT and return the decoded payload.
    
    Supabase JWTs use the project's JWT secret (HS256) and contain:
      - sub: user UUID
      - email: user email
      - role: 'authenticated'
      - exp: expiration timestamp
    """
    jwt_secret = settings.supabase_jwt_secret or settings.secret_key
    
    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=[settings.algorithm],
            options={"verify_aud": False},  # Supabase doesn't always set aud
        )
        return payload
    except JWTError as e:
        logger.warning("JWT verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> CurrentUser:
    """FastAPI dependency that extracts and verifies the current user.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: CurrentUser = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    # Dev mode: no Supabase configured → return a default dev user
    if not settings.supabase_url or not settings.supabase_key:
        return CurrentUser(id="dev-user", email="dev@example.com", role="dev")
    
    # Production: require a valid Bearer token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = _verify_supabase_jwt(credentials.credentials)
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: no user ID",
        )
    
    return CurrentUser(
        id=user_id,
        email=payload.get("email"),
        role=payload.get("role", "authenticated"),
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[CurrentUser]:
    """Like get_current_user but returns None instead of 401 for unauthenticated requests.
    
    Useful for endpoints that work both with and without authentication
    (e.g., chat works for anonymous users but saves history for authenticated ones).
    """
    if not credentials:
        if not settings.supabase_url:
            return CurrentUser(id="dev-user", email="dev@example.com", role="dev")
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
