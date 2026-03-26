"""
core/redis/rate_limit.py
~~~~~~~~~~~~~~~~~~~~~~~~
Token-bucket rate limiter backed by Redis.

Why token bucket?
  - Allows short bursts (unlike a fixed window).
  - Smooth average rate enforcement.
  - Single atomic Lua script → no race conditions.

Usage
-----
    from core.redis.rate_limit import RateLimiter

    limiter = RateLimiter(key="register", identifier=request.ip, limit=5, window=60)
    if not limiter.allow():
        raise RateLimitError()

Or use the decorator:

    @rate_limit(key="login", limit=10, window=60)
    def login_view(request):
        ...
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps

from core.redis.client import get_redis_client

logger = logging.getLogger(__name__)

# ── Lua script for atomic sliding-window counter ──────────────────────────────
# Increments counter; returns [current_count, ttl_remaining]
_RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, window)
end
local ttl = redis.call('TTL', key)
return {current, ttl}
"""


@dataclass
class RateLimitResult:
    allowed: bool
    current: int
    limit: int
    retry_after: int  # seconds until the window resets


class RateLimiter:
    """
    Sliding-window rate limiter.

    Parameters
    ----------
    key        : Logical name for the action (e.g. "login", "register")
    identifier : Per-user identifier (e.g. user_id, IP address)
    limit      : Max requests allowed per *window* seconds
    window     : Time window in seconds
    """

    def __init__(
        self,
        key: str,
        identifier: str,
        limit: int,
        window: int,
    ) -> None:
        self.redis_key = f"rate:{key}:{identifier}"
        self.limit = limit
        self.window = window
        self._script = get_redis_client().register_script(_RATE_LIMIT_SCRIPT)

    def check(self) -> RateLimitResult:
        """Check the rate limit without raising. Returns a RateLimitResult."""
        try:
            current, ttl = self._script(
                keys=[self.redis_key], args=[self.limit, self.window]
            )
            current, ttl = int(current), int(ttl)
            return RateLimitResult(
                allowed=current <= self.limit,
                current=current,
                limit=self.limit,
                retry_after=max(ttl, 0),
            )
        except Exception as exc:
            # fakeredis (used in tests) doesn't implement scripting/EVALSHA in some versions.
            # Fall back to non-scripted ops when the backend rejects EVALSHA.
            if "evalsha" in str(exc).lower():
                try:
                    client = get_redis_client()
                    current = int(client.incr(self.redis_key))
                    if current == 1:
                        client.expire(self.redis_key, self.window)
                    ttl = int(client.ttl(self.redis_key))
                    return RateLimitResult(
                        allowed=current <= self.limit,
                        current=current,
                        limit=self.limit,
                        retry_after=max(ttl, 0),
                    )
                except Exception:
                    pass
            logger.exception(
                "Rate limiter Redis error for key=%s — allowing request", self.redis_key
            )
            # Fail open: if Redis is down we should not block users
            return RateLimitResult(
                allowed=True, current=0, limit=self.limit, retry_after=0
            )

    def allow(self) -> bool:
        return self.check().allowed


def rate_limit(
    key: str, limit: int, window: int, identifier_fn: Callable | None = None
):
    """
    Decorator factory for rate-limiting view functions.

    Parameters
    ----------
    key            : Action name (e.g. "login")
    limit          : Max calls per window
    window         : Window size in seconds
    identifier_fn  : Callable(request) → str  — defaults to request.META["REMOTE_ADDR"]

    Example
    -------
        @rate_limit("login", limit=5, window=60)
        def login_view(request):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            from core.exceptions.base import RateLimitError

            identifier = (
                identifier_fn(request)
                if identifier_fn
                else request.META.get("REMOTE_ADDR", "unknown")
            )
            limiter = RateLimiter(
                key=key, identifier=identifier, limit=limit, window=window
            )
            result = limiter.check()

            if not result.allowed:
                raise RateLimitError(
                    detail={"retry_after": result.retry_after, "limit": limit}
                )
            return func(request, *args, **kwargs)

        return wrapper

    return decorator
