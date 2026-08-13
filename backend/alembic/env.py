import os
import sys
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# ── Make sure app package is importable ───────────────────────────────────────
# Add the backend root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load .env so DATABASE_URL is available
load_dotenv()

# ── Alembic config ────────────────────────────────────────────────────────────
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Import your app's Base and all models ─────────────────────────────────────
# This is the critical line — it tells Alembic about your ORM tables
# so it can auto-generate migration scripts when you change your models.
import app.db.models  # noqa: F401 — ensures all models are registered on Base
from app.db.database import Base

target_metadata = Base.metadata

# ── Read DATABASE_URL from environment ────────────────────────────────────────
def get_url():
    url = os.getenv("DATABASE_URL", "sqlite:///./farming_assistant.db")
    # SQLAlchemy 2.0+ requires postgresql:// instead of postgres://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL scripts without connecting)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to DB and applies changes)."""
    # Override sqlalchemy.url with the value from .env
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # compare_type=True tells Alembic to also detect column type changes
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
