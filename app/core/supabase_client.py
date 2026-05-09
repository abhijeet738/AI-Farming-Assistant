"""
Supabase client initialization.

Provides a singleton Supabase client for auth operations.
Database access goes through SQLAlchemy (db/database.py), NOT this client.
"""

from typing import Optional
from app.config import settings
import structlog

logger = structlog.get_logger()

_supabase_client = None


def get_supabase_client():
    """Get or create the Supabase client singleton.
    
    Returns None if Supabase is not configured (local dev mode).
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not settings.supabase_url or not settings.supabase_key:
        logger.warning(
            "Supabase not configured — auth endpoints will be disabled. "
            "Set SUPABASE_URL and SUPABASE_KEY in .env for full functionality."
        )
        return None

    try:
        # pyrefly: ignore [missing-import]
        from supabase import create_client
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client initialized", url=settings.supabase_url)
        return _supabase_client
    except Exception as e:
        logger.error("Failed to initialize Supabase client", error=str(e))
        return None


def get_supabase_admin_client():
    """Get a Supabase client with service_role key for admin operations.
    
    Used for server-side operations like deleting users, bypassing RLS, etc.
    """
    if not settings.supabase_url or not settings.supabase_service_key:
        return None

    try:
        # pyrefly: ignore [missing-import]
        from supabase import create_client
        return create_client(settings.supabase_url, settings.supabase_service_key)
    except Exception as e:
        logger.error("Failed to initialize Supabase admin client", error=str(e))
        return None
