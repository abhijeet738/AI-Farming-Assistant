"""
Authentication and security utilities.

Supports two modes:
  1. Supabase Auth (production) — verifies Supabase JWTs
  2. Dev mode (no Supabase) — allows unauthenticated access with a default user
"""


import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings

logger = structlog.get_logger()

# FastAPI security scheme — extracts Bearer token from Authorization header
security = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """Represents the authenticated user extracted from the JWT."""
    id: str
    email: str | None = None
    role: str = "user"


def _verify_supabase_jwt(token: str) -> dict:
    """Verify a Supabase JWT and return the payload by calling the Supabase API.

    This avoids issues with incorrect SUPABASE_JWT_SECRET environment variables
    by having the Supabase server validate the token for us.
    """
    from app.core.supabase_client import get_supabase_client
    
    client = get_supabase_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client not configured",
        )

    try:
        # get_user validates the token remotely against Supabase
        res = client.auth.get_user(token)
        if not res or not res.user:
            raise JWTError("User not found or token invalid")
            
        # Return a payload dictionary compatible with the rest of the app
        return {
            "sub": res.user.id,
            "email": res.user.email,
            "role": res.user.role or "authenticated"
        }
    except Exception as e:
        logger.warning("JWT verification failed via Supabase API", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
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
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser | None:
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
