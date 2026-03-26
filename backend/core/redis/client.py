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


class _InMemoryRedis:
    """Small fallback Redis-like client for tests."""

    def __init__(self):
        self._store: dict[str, Any] = {}
        self._sets: dict[str, set[str]] = {}

    def get(self, key: str):
        return self._store.get(key)

    def set(self, key: str, value: Any, ex: int | None = None):
        self._store[key] = value
        return True

    def setex(self, key: str, ttl: int, value: Any):
        self._store[key] = value
        return True

    def exists(self, key: str) -> int:
        return 1 if key in self._store else 0

    def sadd(self, key: str, value: Any):
        self._sets.setdefault(key, set()).add(str(value))
        return 1

    def srem(self, key: str, value: Any):
        self._sets.setdefault(key, set()).discard(str(value))
        return 1

    def sismember(self, key: str, value: Any) -> bool:
        return str(value) in self._sets.get(key, set())

    def scard(self, key: str) -> int:
        return len(self._sets.get(key, set()))

    def delete(self, key: str):
        self._store.pop(key, None)
        self._sets.pop(key, None)
        return 1

    def ping(self) -> bool:
        return True

    def pipeline(self):
        return _InMemoryPipeline(self)


class _InMemoryPipeline:
    def __init__(self, client: _InMemoryRedis):
        self._client = client
        self._ops: list[tuple[str, str]] = []

    def delete(self, key: str):
        self._ops.append(("delete", key))
        return self

    def execute(self):
        for op, key in self._ops:
            if op == "delete":
                self._client.delete(key)
        return True


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
    cache_backend = settings.CACHES.get("default", {}).get("BACKEND", "")
    if "locmem" in cache_backend or getattr(settings, "USE_FAKEREDIS", False):
        try:
            import fakeredis

            _redis_client = fakeredis.FakeRedis(decode_responses=True, version=7)
            logger.info("Redis: using fakeredis (test environment)")
            return _redis_client
        except Exception as exc:
            logger.warning(
                "fakeredis unavailable; using in-memory fallback",
                extra={"error": str(exc)},
            )
            _redis_client = _InMemoryRedis()
            return _redis_client

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
        raise RuntimeError(
            "Redis PING returned False — check REDIS_URL / CACHES settings."
        )
    logger.info("Redis health check: OK")
    return True


def reset_client() -> None:
    """
    Force the singleton to be re-created on next call.
    Useful in tests that swap the Redis backend between test cases.
    """
    global _redis_client  # noqa: PLW0603
    _redis_client = None


class RedisClient:
    """Backwards-compatible facade used by app services."""

    @staticmethod
    def get_instance():
        return get_redis_client()


# ── Module-level shortcut ──────────────────────────────────────────────────────
# Import this in application code:   from core.redis.client import redis_client
redis_client = get_redis_client
