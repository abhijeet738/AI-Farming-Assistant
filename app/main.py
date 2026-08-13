"""
FastAPI Application Entry Point.

Initializes the app with:
  - Lifespan context manager (replaces deprecated on_event)
  - Database table creation
  - ML model loading
  - Middleware and exception handlers
"""

from dotenv import load_dotenv
load_dotenv(override=True)  # Load environment variables from .env (override existing)

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# pyrefly: ignore [missing-import]
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.core.rate_limit import limiter

# Setup logging first
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""

    # ── Startup ─────────────────────────────────────────────────────
    logger.info("🚀 Starting Farming Assistant API...")

    # 1. Create database tables (for SQLite dev mode)
    try:
        from app.db.database import create_tables
        create_tables()
        logger.info("✅ Database tables ready")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))

    # 2. Load ML models
    try:
        from app.ml.model_registry import registry
        results = registry.load_all()
        loaded = sum(1 for v in results.values() if v)
        logger.info(f"✅ ML models loaded: {loaded}/{len(results)}", status=results)
    except Exception as e:
        logger.warning("ML model loading failed (non-fatal)", error=str(e))

    # 3. Initialize Supabase client
    try:
        from app.core.supabase_client import get_supabase_client
        client = get_supabase_client()
        if client:
            logger.info("✅ Supabase client connected")
        else:
            logger.info("ℹ️  Running in local dev mode (no Supabase)")
    except Exception as e:
        logger.warning("Supabase initialization skipped", error=str(e))

    logger.info("🟢 Farming Assistant API is ready!")

    yield  # App is running

    # ── Shutdown ────────────────────────────────────────────────────
    logger.info("🔴 Shutting down Farming Assistant API...")


# Create the FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    description="AI-powered agricultural advisory platform with multi-modal agentic capabilities",
    lifespan=lifespan,
)

# Setup middleware (CORS, request ID, timing)
setup_middleware(app)

# Setup exception handlers
setup_exception_handlers(app)

# Attach rate limiter state and 429 handler
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded. Try again in {exc.retry_after} seconds."},
    )

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Farming Assistant API",
        "version": settings.version,
        "status": "running",
    }


@app.get("/ping")
async def ping():
    return {"message": "pong"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
