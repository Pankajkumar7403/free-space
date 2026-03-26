# 📁 Location: backend/apps/feed/cache.py

from __future__ import annotations

import logging

from apps.feed.constants import FEED_MAX_SIZE, FEED_TTL_SECONDS
from core.redis.client import get_redis_client

logger = logging.getLogger(__name__)

# ── Key schema ─────────────────────────────────────────────────────────────────
# feed:{user_id}            ZSet  — post_id → score (ranked feed)
# feed:warm:{user_id}       str   — flag: feed has been warmed up
# explore:trending          ZSet  — post_id → score (global explore feed)


def _feed_key(user_id: str) -> str:
    return f"feed:{user_id}"


def _warm_key(user_id: str) -> str:
    return f"feed:warm:{user_id}"


# ── Write helpers ─────────────────────────────────────────────────────────────


def feed_push_post(user_id: str, post_id: str, score: float) -> None:
    """
    Add a single post to a user's Redis feed ZSet.
    Sets TTL on first write. Trims feed to FEED_MAX_SIZE.
    """
    client = get_redis_client()
    key = _feed_key(user_id)
    pipe = client.pipeline()
    pipe.zadd(key, {post_id: score})
    pipe.expire(key, FEED_TTL_SECONDS)
    pipe.execute()
    # Trim asynchronously: keep only the top FEED_MAX_SIZE by score
    _trim_feed(client, key)


def feed_push_batch(user_id: str, post_scores: dict[str, float]) -> None:
    """
    Bulk-add multiple posts to a user's feed in a single pipeline.
    Used by the fanout task for efficiency.
    """
    if not post_scores:
        return
    client = get_redis_client()
    key = _feed_key(user_id)
    pipe = client.pipeline()
    pipe.zadd(key, post_scores)
    pipe.expire(key, FEED_TTL_SECONDS)
    pipe.execute()
    _trim_feed(client, key)


def feed_remove_post(user_id: str, post_id: str) -> None:
    """Remove a deleted post from a user's feed."""
    get_redis_client().zrem(_feed_key(user_id), post_id)


def feed_delete(user_id: str) -> None:
    """Invalidate an entire feed (e.g. on unfollow)."""
    get_redis_client().delete(_feed_key(user_id))


# ── Read helpers ──────────────────────────────────────────────────────────────


def feed_get_page(
    user_id: str,
    cursor: int = 0,
    page_size: int = 20,
) -> list[str]:
    """
    Return a page of post IDs from the user's Redis feed.

    Posts are ordered by score DESC (highest ranked first).
    Returns a list of post_id strings, empty list on cache miss.

    Parameters
    ----------
    cursor    : offset into the ZSet (0-based)
    page_size : number of items to return
    """
    key = _feed_key(user_id)
    return get_redis_client().zrevrange(key, cursor, cursor + page_size - 1)


def feed_exists(user_id: str) -> bool:
    """Return True if this user has a feed in Redis."""
    return get_redis_client().exists(_feed_key(user_id)) == 1


def feed_size(user_id: str) -> int:
    """Return the number of items in the user's Redis feed."""
    return get_redis_client().zcard(_feed_key(user_id))


# ── TTL / warm-up ─────────────────────────────────────────────────────────────


def mark_feed_warm(user_id: str) -> None:
    """Mark that this user's feed has been warmed up from DB."""
    get_redis_client().setex(_warm_key(user_id), FEED_TTL_SECONDS, "1")


def is_feed_warm(user_id: str) -> bool:
    """Check if feed warm-up has already been done for this user."""
    return get_redis_client().exists(_warm_key(user_id)) == 1


# ── Explore feed ──────────────────────────────────────────────────────────────

EXPLORE_KEY = "explore:trending"


def explore_push(post_id: str, score: float) -> None:
    """Add a post to the global explore/trending feed."""
    client = get_redis_client()
    client.zadd(EXPLORE_KEY, {post_id: score})
    client.expire(EXPLORE_KEY, FEED_TTL_SECONDS)
    _trim_feed(client, EXPLORE_KEY)


def explore_get_page(cursor: int = 0, page_size: int = 20) -> list[str]:
    """Return a page of trending post IDs."""
    return get_redis_client().zrevrange(EXPLORE_KEY, cursor, cursor + page_size - 1)


# ── Internal ──────────────────────────────────────────────────────────────────


def _trim_feed(client, key: str) -> None:
    """Keep only the top FEED_MAX_SIZE items. Removes lowest-scored items."""
    # zremrangebyrank removes items ranked 0..N (lowest scores)
    # Keeping rank -(FEED_MAX_SIZE)..−1 means we keep top FEED_MAX_SIZE items
    client.zremrangebyrank(key, 0, -(FEED_MAX_SIZE + 1))
