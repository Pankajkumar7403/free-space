"""
core/feature_flags/client.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Redis-based feature flags with three rollout modes:

1. Global on/off        - feature:{name}:enabled = "1"
2. Per-user canary      - feature:{name}:users   = Set{user_id, ...}
3. Percentage rollout   - feature:{name}:pct     = "25"  (0-100)
   Uses MD5(user_id) % 100 for stable, consistent per-user assignment.

Admin API (management command or Django admin) writes to Redis.
Application code only reads.

Usage
-----
    from core.feature_flags import is_enabled, FeatureFlag

    # Simple check
    if is_enabled("graphql_relay", user_id=request.user.id):
        ...

    # Class-based
    GRAPHQL = FeatureFlag("graphql_relay")
    if GRAPHQL.check(user_id=user.id):
        ...
"""

from __future__ import annotations

import hashlib
import logging
import uuid

logger = logging.getLogger(__name__)

# Redis key patterns
_KEY_ENABLED = "feature:{name}:enabled"
_KEY_USERS = "feature:{name}:users"
_KEY_PCT = "feature:{name}:pct"


class FeatureFlag:
    """Represents a single named feature flag."""

    def __init__(self, name: str) -> None:
        self.name = name

    def check(self, user_id: uuid.UUID | str | None = None) -> bool:
        return is_enabled(self.name, user_id=user_id)

    def enable(self) -> None:
        _get_redis().set(_KEY_ENABLED.format(name=self.name), "1")

    def disable(self) -> None:
        pipe = _get_redis().pipeline()
        pipe.delete(_KEY_ENABLED.format(name=self.name))
        pipe.delete(_KEY_PCT.format(name=self.name))
        pipe.execute()

    def set_percentage(self, pct: int) -> None:
        """Enable for pct% of users (0-100)."""
        pct = max(0, min(100, pct))
        _get_redis().set(_KEY_PCT.format(name=self.name), str(pct))

    def add_user(self, user_id: uuid.UUID | str) -> None:
        """Add a specific user to the canary set."""
        _get_redis().sadd(_KEY_USERS.format(name=self.name), str(user_id))

    def remove_user(self, user_id: uuid.UUID | str) -> None:
        _get_redis().srem(_KEY_USERS.format(name=self.name), str(user_id))

    def status(self) -> dict:
        """Return current flag configuration."""
        r = _get_redis()
        return {
            "name": self.name,
            "global": bool(r.get(_KEY_ENABLED.format(name=self.name))),
            "percentage": int(r.get(_KEY_PCT.format(name=self.name)) or 0),
            "user_count": r.scard(_KEY_USERS.format(name=self.name)),
        }


def is_enabled(name: str, user_id: uuid.UUID | str | None = None) -> bool:
    """
    Return True if the feature is enabled for the given user (or globally).
    Safe to call even if Redis is down - returns False on error.
    """
    try:
        r = _get_redis()

        # 1. Global flag
        if r.get(_KEY_ENABLED.format(name=name)):
            return True

        # 2. Per-user canary set
        if user_id and r.sismember(_KEY_USERS.format(name=name), str(user_id)):
            return True

        # 3. Percentage rollout
        raw_pct = r.get(_KEY_PCT.format(name=name))
        if raw_pct and user_id:
            pct = int(raw_pct)
            user_hash = int(
                hashlib.md5(str(user_id).encode(), usedforsecurity=False).hexdigest(),
                16,
            )
            return (user_hash % 100) < pct

        return False

    except Exception as exc:
        logger.warning(
            "feature_flag.check_failed",
            extra={"flag": name, "error": str(exc)},
        )
        return False  # Fail open: don't block users on Redis errors


def _get_redis():
    from core.redis.client import RedisClient

    return RedisClient.get_instance()
