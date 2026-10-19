"""
HotWAY Telemetry Service & Redis GeoStore Integration.
Provides connection pooling and driver location caching.
"""

import logging
from typing import Optional

logger = logging.getLogger("hotway.telemetry")

_redis_pool: Optional[object] = None


async def init_redis_pool() -> None:
    """Initialize Redis connection pool if configured."""
    global _redis_pool
    try:
        from backend.app.core.config import settings
        import redis.asyncio as aioredis
        _redis_pool = aioredis.from_url(settings.redis_connection_url, decode_responses=True)
        # Test ping with a short timeout
        await _redis_pool.ping()
        logger.info("Connected to Redis successfully.")
    except Exception as exc:
        logger.warning("Redis connection unavailable, running with in-memory telemetry fallback: %s", exc)
        _redis_pool = None


async def close_redis_pool() -> None:
    """Close Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        try:
            await _redis_pool.aclose()
        except Exception as exc:
            logger.warning("Error closing Redis pool: %s", exc)
        finally:
            _redis_pool = None
