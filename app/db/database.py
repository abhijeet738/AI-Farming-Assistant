"""
Database engine and session factory.

Supports both SQLite (local dev) and PostgreSQL (Supabase production).
Uses SQLAlchemy 2.0 patterns with the new DeclarativeBase.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import settings
import structlog

logger = structlog.get_logger()


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def _get_engine():
    """Create the SQLAlchemy engine based on DATABASE_URL."""
    url = settings.database_url

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
        engine = create_engine(
            url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=settings.debug,
        )
        logger.info("Database engine created", backend="PostgreSQL")

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
