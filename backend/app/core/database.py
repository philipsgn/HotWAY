"""
HotWAY Database Engine, Session Factory & Lifecycle Management
Author: Backend & WebGIS Engineer
Target: Async SQLAlchemy 2.0 with GeoAlchemy2 & Connection Pooling
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

try:
    from backend.app.core.config import settings
    from backend.app.models.base import Base
except ImportError:
    from .config import settings
    from ..models.base import Base

logger = logging.getLogger("hotway.database")


def get_engine_args(url: str) -> dict:
    """
    Construct dialect-specific engine parameters.
    Supports PostgreSQL (asyncpg) with QueuePool and SQLite (aiosqlite) with StaticPool.
    """
    if url.startswith("sqlite"):
        logger.info("Configuring SQLite Async Engine with StaticPool for testing/local mode.")
        return {
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
            "echo": settings.DB_ECHO,
        }
    
    # PostgreSQL production pool configuration
    return {
        "poolclass": QueuePool,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": 1800,  # Recycle connections every 30 minutes
        "pool_pre_ping": True,  # Test liveness before handing connection to worker
        "echo": settings.DB_ECHO,
    }


# 1. Global Async Engine Instance with Graceful SQLite Local Fallback
db_url: str = settings.async_database_url
try:
    engine: AsyncEngine = create_async_engine(db_url, **get_engine_args(db_url))
except Exception as exc:
    logger.warning(
        "Could not initialize PostgreSQL engine with %s (%s). Falling back to sqlite+aiosqlite.",
        db_url,
        exc,
    )
    db_url = "sqlite+aiosqlite:///./test_hotway.db"
    engine = create_async_engine(db_url, **get_engine_args(db_url))

# 2. Async Session Factory
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Essential: prevents MissingGreenlet on post-commit attribute access
    autoflush=False,         # Prevents unexpected flushes before explicit queries
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an asynchronous database session.
    
    Lifecycle guarantees:
    - Automatically commits if route execution completes successfully.
    - Automatically rolls back if an unhandled exception occurs.
    - Guarantees session closure and connection release back to pool.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            logger.error("Transaction rolled back due to error: %s", exc)
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database schema by creating all registered tables.
    Primarily used for SQLite test environments or initial bootstrap.
    Production systems should execute Alembic migrations.
    """
    async with engine.begin() as conn:
        logger.info("Creating database tables if not present...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized successfully.")


async def close_db() -> None:
    """
    Gracefully dispose of the database connection pool.
    Called during FastAPI application shutdown lifespan event.
    """
    logger.info("Disposing database connection engine...")
    await engine.dispose()
    logger.info("Database connection engine disposed.")
