"""
FastAPI dependency injection utilities.

Provides reusable dependencies for database sessions,
authentication, and configuration.
"""

from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.database import get_db
from app.config import settings
from app.core.security import get_current_user, get_optional_user, CurrentUser


# Database dependency
def get_database() -> Session:
    """Get a database session (for use outside of FastAPI routes)."""
    return next(get_db())


# Settings dependency
def get_settings():
    """Get the application settings."""
    return settings


# Weather service dependency
def get_weather_service():
    """Get a WeatherService instance."""
    from app.services.weather_service import WeatherService
    return WeatherService()
