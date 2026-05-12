"""
Database engine and session factory.

Supports both SQLite (local dev) and PostgreSQL (Supabase production).
Uses SQLAlchemy 2.0 patterns with the new DeclarativeBase.
"""

import structlog
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = structlog.get_logger()


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def _get_engine():
    """Create the SQLAlchemy engine based on DATABASE_URL."""
    url = settings.database_url
    
    # Handle empty or None DATABASE_URL (fallback to SQLite for HF Spaces)
    if not url or url.strip() == "":
        logger.warning("DATABASE_URL is empty, falling back to SQLite")
        url = "sqlite:///./farming_assistant.db"
    
    # SQLAlchemy 2.0+ requires postgresql:// instead of postgres://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    if url.startswith("sqlite"):
        # SQLite — enable WAL mode for better concurrency
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=settings.debug,
        )

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        logger.info("Database engine created", backend="SQLite", url=url)
    else:
        # PostgreSQL (Supabase)
        try:
            engine = create_engine(
                url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=settings.debug,
            )
            logger.info("Database engine created", backend="PostgreSQL")
        except Exception as e:
            logger.error("Failed to create PostgreSQL engine, falling back to SQLite", error=str(e))
            # Fallback to SQLite if PostgreSQL fails
            url = "sqlite:///./farming_assistant.db"
            engine = create_engine(
                url,
                connect_args={"check_same_thread": False},
                echo=settings.debug,
            )
            logger.info("Database engine created (fallback)", backend="SQLite", url=url)

    return engine


engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables defined by ORM models.

    Called at startup for SQLite. For Supabase, tables are created
    via the SQL Editor or Alembic migrations.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
