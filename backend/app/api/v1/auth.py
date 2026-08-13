"""
Authentication and User Profile endpoints.

Uses Supabase Auth for registration/login and SQLAlchemy for farm profile data.
"""


import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, get_current_user
from app.core.supabase_client import get_supabase_client
from app.db import crud
from app.db.database import get_db

logger = structlog.get_logger()
router = APIRouter()


# ─── Request/Response Models ───────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    name: str | None = Field(None, description="Full name")

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Password")

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str

class UserProfile(BaseModel):
    id: str
    email: str | None = None
    role: str = "user"

class FarmProfileCreate(BaseModel):
    farm_name: str | None = None
    state: str | None = None
    district: str | None = None
    area_hectares: float | None = Field(None, gt=0)
    soil_type: str | None = None
    irrigation_type: str | None = None
    crops: list | None = None
    latitude: float | None = None
    longitude: float | None = None

class FarmProfileResponse(BaseModel):
    id: str
    farm_name: str | None = None
    state: str | None = None
    district: str | None = None
    area_hectares: float | None = None
    soil_type: str | None = None
    irrigation_type: str | None = None
    crops: list | None = None

    class Config:
        from_attributes = True


# ─── Auth Endpoints ────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user via Supabase Auth."""
    client = get_supabase_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not configured. Set SUPABASE_URL and SUPABASE_KEY.",
        )

    try:
        response = client.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {"name": request.name or ""}
            }
        })

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed. The email may already be in use.",
            )

        session = response.session
        if not session:
            # Supabase may require email confirmation
            return AuthResponse(
                access_token="check-email-for-confirmation",
                user_id=response.user.id,
                email=request.email,
            )

        logger.info("User registered", user_id=response.user.id, email=request.email)

        return AuthResponse(
            access_token=session.access_token,
            user_id=response.user.id,
            email=request.email,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login with email and password via Supabase Auth."""
    client = get_supabase_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not configured.",
        )

    try:
        response = client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        logger.info("User logged in", user_id=response.user.id)

        return AuthResponse(
            access_token=response.session.access_token,
            user_id=response.user.id,
            email=request.email,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


@router.get("/me", response_model=UserProfile)
async def get_me(user: CurrentUser = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return UserProfile(id=user.id, email=user.email, role=user.role)


# ─── Farm Profile Endpoints ───────────────────────────────────────────────

@router.post("/farm-profile", response_model=FarmProfileResponse)
async def create_farm(
    request: FarmProfileCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new farm profile for the authenticated user."""
    profile = crud.create_farm_profile(
        db=db,
        user_id=user.id,
        **request.model_dump(exclude_none=True),
    )
    return profile


@router.get("/farm-profiles", response_model=list[FarmProfileResponse])
async def list_farms(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all farm profiles for the authenticated user."""
    profiles = crud.get_farm_profiles(db, user.id)
    return profiles


@router.put("/farm-profile/{profile_id}", response_model=FarmProfileResponse)
async def update_farm(
    profile_id: str,
    request: FarmProfileCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a farm profile."""
    profile = crud.update_farm_profile(
        db=db,
        profile_id=profile_id,
        user_id=user.id,
        **request.model_dump(exclude_none=True),
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Farm profile not found")
    return profile


@router.delete("/farm-profile/{profile_id}")
async def delete_farm(
    profile_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a farm profile."""
    success = crud.delete_farm_profile(db, profile_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Farm profile not found")
    return {"message": "Farm profile deleted", "id": profile_id}
