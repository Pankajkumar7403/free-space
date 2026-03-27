"""
core/redis/cache.py
~~~~~~~~~~~~~~~~~~~
High-level cache helpers that wrap raw Redis calls with:
  - Consistent key namespacing
  - JSON serialisation / deserialisation
  - TTL defaults from settings
  - Type safety

These helpers are used by feed, likes, notifications, etc.
Never import redis_client directly in app code — use these helpers or
write a new one here.

Key schema
----------
    feed:{user_id}              ZSet  — ranked post IDs for a user's feed
    post:likes:{post_id}        str   — like counter (integer)
    rate:{action}:{identifier}  str   — rate limit counter
    session:{token_jti}         str   — JWT blacklist entry
"""

from __future__ import annotations

import json
import logging
from typing import Any

from core.redis.client import get_redis_client

logger = logging.getLogger(__name__)

# ── Default TTLs (seconds) ────────────────────────────────────────────────────
FEED_TTL = 60 * 60 * 24 * 7  # 7 days
COUNTER_TTL = 60 * 60 * 24  # 24 hours
SESSION_TTL = 60 * 60 * 24 * 30  # 30 days (refresh token lifetime)


# ── Generic helpers ───────────────────────────────────────────────────────────


def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    """Serialise *value* to JSON and store it in Redis."""
    client = get_redis_client()
    serialised = json.dumps(value)
    if ttl:
        client.setex(key, ttl, serialised)
    else:
        client.set(key, serialised)


def cache_get(key: str) -> Any | None:
    """Retrieve and deserialise a JSON value; returns None on cache miss."""
    client = get_redis_client()
    raw = client.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning("cache_get: failed to deserialise key=%s", key)
        return None


def cache_delete(key: str) -> None:
    get_redis_client().delete(key)


def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching *pattern* (use sparingly — O(N) scan)."""
    client = get_redis_client()
    keys = client.keys(pattern)
    if keys:
        return client.delete(*keys)
    return 0


# ── Counter helpers (likes, view counts) ─────────────────────────────────────


def counter_incr(key: str, ttl: int = COUNTER_TTL) -> int:
    """Atomically increment a counter; sets TTL on first creation."""
    client = get_redis_client()
    pipe = client.pipeline()
    pipe.incr(key)
    pipe.expire(key, ttl)
    result, _ = pipe.execute()
    return result


def counter_decr(key: str) -> int:
    """Atomically decrement a counter (floor at 0)."""
    client = get_redis_client()
    pipe = client.pipeline()
    pipe.decr(key)
    (result,) = pipe.execute()[:1]
    # Prevent negative counts from cache drift
    if result < 0:
        client.set(key, 0)
        return 0
    return result


def counter_get(key: str) -> int:
    """Return counter value; returns 0 on cache miss."""
    client = get_redis_client()
    val = client.get(key)
    return int(val) if val is not None else 0


# ── Feed sorted set helpers ───────────────────────────────────────────────────


def feed_push(user_id: str, post_id: str, score: float) -> None:
    """Add *post_id* to a user's feed sorted set with *score* (Unix timestamp)."""
    key = f"feed:{user_id}"
    client = get_redis_client()
    client.zadd(key, {post_id: score})
    client.expire(key, FEED_TTL)


def feed_trim(user_id: str, max_size: int = 1000) -> None:
    """Keep only the most recent *max_size* items in the feed."""
    key = f"feed:{user_id}"
    # ZREMRANGEBYRANK removes lowest scores first; keep top max_size
    get_redis_client().zremrangebyrank(key, 0, -(max_size + 1))


def feed_get(user_id: str, cursor: int = 0, count: int = 20) -> list[str]:
    """Return paginated post IDs from the user's feed (newest first)."""
    key = f"feed:{user_id}"
    return get_redis_client().zrevrange(key, cursor, cursor + count - 1)


def feed_remove(user_id: str, post_id: str) -> None:
    """Remove a single post from the user's feed (e.g. post deleted)."""
    get_redis_client().zrem(f"feed:{user_id}", post_id)


# ── JWT blacklist helpers ─────────────────────────────────────────────────────


def blacklist_token(jti: str, ttl: int = SESSION_TTL) -> None:
    """Mark a JWT (by its jti claim) as revoked."""
    get_redis_client().setex(f"blacklist:{jti}", ttl, "1")


def is_token_blacklisted(jti: str) -> bool:
    return get_redis_client().exists(f"blacklist:{jti}") == 1
