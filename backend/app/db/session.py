"""
AIVOA — Async Database Session Management

Centralizes SQLAlchemy async engine and session factory creation.
All database access throughout the application flows through this module.

Design decisions:
- async engine + asyncpg: required by the architecture spec (§11 checklist)
  to avoid blocking the FastAPI event loop during DB operations.
- pool_size=5 / max_overflow=10: sensible defaults for a small-to-medium
  application. Each FastAPI worker gets its own pool; with 1 worker in dev
  this means up to 15 concurrent DB connections.
- async_sessionmaker: SQLAlchemy 2.x recommended pattern for creating
  per-request sessions without manual boilerplate.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

import sys
from sqlalchemy.pool import NullPool

is_pytest = "pytest" in sys.modules

engine_kwargs = {}
if not is_pytest:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development"),
    poolclass=NullPool if is_pytest else None,
    **engine_kwargs
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """
    FastAPI dependency that yields an async database session.

    Usage in a future endpoint:
        @app.get("/complaints")
        async def list_complaints(db: AsyncSession = Depends(get_db)):
            ...

    The session is automatically closed when the request finishes,
    even if an exception occurs.
    """
    async with async_session_factory() as session:
        yield session
