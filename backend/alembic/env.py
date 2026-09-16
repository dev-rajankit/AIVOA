"""
AIVOA — Alembic Migration Environment

Configured for async SQLAlchemy (asyncpg).

Key design decisions:
- DATABASE_URL is read from the application settings (pydantic-settings),
  not hardcoded in alembic.ini. This ensures migrations always use the
  same connection string as the running application.
- Async engine is used for online migrations because the application
  uses async SQLAlchemy everywhere; using a sync engine here would
  require a separate sync driver dependency (psycopg2).
- target_metadata is wired to Base.metadata from our models, enabling
  Alembic's autogenerate to detect model changes automatically.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import all models so their tables are registered on Base.metadata
from app.db.models import Base  # noqa: F401
from app.core.config import settings

# Alembic Config object
config = context.config

# Override sqlalchemy.url with the value from our application settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up Python logging from the .ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what Alembic compares against when running autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for reviewing migration SQL before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Run migrations with an active connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode using an async engine.

    Creates an async engine from the configuration, connects,
    and runs migrations within that connection.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations — delegates to async."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
