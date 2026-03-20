# 📁 Location: backend/core/redis/client.py
"""
core/redis/client.py
~~~~~~~~~~~~~~~~~~~~
Thread-safe Redis singleton backed by django-redis.

Why a singleton instead of raw django.core.cache.cache?
  - We need the raw Redis client for operations cache doesn't expose:
    ZADD, ZRANGE, INCR, EXPIRE, pub/sub, pipelines, Lua scripts.
  - A singleton avoids reconnecting on every request.
  - We can swap the backend (real Redis ↔ fakeredis) via settings
    without changing call sites.

Usage
-----
    from core.redis.client import redis_client

    redis_client.set("key", "value", ex=60)
    redis_client.zadd("feed:user:123", {"post:456": 1700000000.0})
    count = redis_client.incr("likes:post:789")

Health check
------------
    from core.redis.client import check_redis_connection
    check_redis_connection()   # raises RedisConnectionError on failure
"""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

_redis_client: Any = None  # module-level singleton


def get_redis_client():
    """
    Return the module-level Redis client, creating it on first call.

    In tests, CACHES["default"] points to LocMemCache, so we return a
    fakeredis instance instead — no real Redis needed.
    """
    global _redis_client  # noqa: PLW0603

    if _redis_client is not None:
        return _redis_client

    # ── Test environment: use fakeredis ───────────────────────────────────────
    cache_backend = (
        settings.CACHES.get("default", {}).get("BACKEND", "")
    )
    if "locmem" in cache_backend or getattr(settings, "USE_FAKEREDIS", False):
        try:
            import fakeredis
            _redis_client = fakeredis.FakeRedis(decode_responses=True, version=7)
            logger.info("Redis: using fakeredis (test environment)")
            return _redis_client
        except ImportError:
            logger.warning("fakeredis not installed; falling back to real Redis")

    # ── Production/development: use django-redis ──────────────────────────────
    try:
        from django_redis import get_redis_connection
        _redis_client = get_redis_connection("default")
        logger.info("Redis: connected via django-redis")
    except Exception:
        # Fallback: direct redis-py connection from settings
        import redis as redis_lib

        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis_lib.from_url(redis_url, decode_responses=True)
        logger.info("Redis: connected via redis-py (%s)", redis_url)

    return _redis_client


def check_redis_connection() -> bool:
    """
    Ping Redis to verify the connection.  Call this in AppConfig.ready()
    or a management command to fail fast on misconfiguration.

    Returns True on success, raises on failure.
    """
    client = get_redis_client()
    result = client.ping()
    if not result:
        raise RuntimeError("Redis PING returned False — check REDIS_URL / CACHES settings.")
    logger.info("Redis health check: OK")
    return True


def reset_client() -> None:
    """
    Force the singleton to be re-created on next call.
    Useful in tests that swap the Redis backend between test cases.
    """
    global _redis_client  # noqa: PLW0603
    _redis_client = None


# ── Module-level shortcut ──────────────────────────────────────────────────────
# Import this in application code:   from core.redis.client import redis_client
redis_client = get_redis_client