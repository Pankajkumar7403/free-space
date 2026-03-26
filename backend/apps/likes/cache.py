# 📁 Location: backend/apps/likes/cache.py
#
# Redis is the SOURCE OF TRUTH for like counts.
# The DB column is a reconciled backup, updated every 5 minutes by Celery.
#
# Key schema
# ----------
# likes:count:{ct}:{object_id}       →  integer (total like count)
# likes:member:{user_id}:{ct}:{id}   →  "1" (has this user liked this object?)

from __future__ import annotations

from apps.likes.constants import LIKE_COUNTER_TTL
from core.redis.client import get_redis_client


def _count_key(content_type: str, object_id: str) -> str:
    return f"likes:count:{content_type}:{object_id}"


def _member_key(user_id: str, content_type: str, object_id: str) -> str:
    return f"likes:member:{user_id}:{content_type}:{object_id}"


# ── Write ─────────────────────────────────────────────────────────────────────


def like_incr(content_type: str, object_id: str, user_id: str) -> int:
    """
    Atomically increment the like counter and mark this user as having liked.
    Returns the new count.
    """
    client = get_redis_client()
    pipe = client.pipeline()
    count_key = _count_key(content_type, object_id)
    member_key = _member_key(user_id, content_type, object_id)
    pipe.incr(count_key)
    pipe.expire(count_key, LIKE_COUNTER_TTL)
    pipe.set(member_key, "1", ex=LIKE_COUNTER_TTL)
    results = pipe.execute()
    return int(results[0])


def like_decr(content_type: str, object_id: str, user_id: str) -> int:
    """
    Atomically decrement the like counter and remove the member flag.
    Returns the new count (floor 0).
    """
    client = get_redis_client()
    pipe = client.pipeline()
    count_key = _count_key(content_type, object_id)
    member_key = _member_key(user_id, content_type, object_id)
    pipe.decr(count_key)
    pipe.delete(member_key)
    results = pipe.execute()
    count = int(results[0])
    if count < 0:
        client.set(count_key, 0)
        return 0
    return count


def set_like_count(content_type: str, object_id: str, count: int) -> None:
    """Called by the DB reconciliation task to sync count from DB to Redis."""
    client = get_redis_client()
    key = _count_key(content_type, object_id)
    client.set(key, count, ex=LIKE_COUNTER_TTL)


# ── Read ──────────────────────────────────────────────────────────────────────


def get_like_count(content_type: str, object_id: str) -> int | None:
    """
    Return the like count from Redis.
    Returns None if the key doesn't exist (cache miss — caller should use DB).
    """
    val = get_redis_client().get(_count_key(content_type, object_id))
    return int(val) if val is not None else None


def has_user_liked(user_id: str, content_type: str, object_id: str) -> bool:
    """Check if a specific user has liked this object."""
    return get_redis_client().exists(_member_key(user_id, content_type, object_id)) == 1
