# 📁 Location: backend/core/tests/test_rate_limiter.py
# ▶  Run:      pytest core/tests/test_rate_limiter.py -v
"""
test_rate_limiter.py
~~~~~~~~~~~~~~~~~~~~
Tests for core/redis/rate_limit.py

Uses fakeredis — no real Redis needed.
"""
from __future__ import annotations

import pytest

from core.redis.client import get_redis_client, reset_client
from core.redis.rate_limit import RateLimiter

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def fresh_redis():
    reset_client()
    get_redis_client().flushall()
    yield
    get_redis_client().flushall()
    reset_client()


class TestRateLimiter:
    def test_allows_requests_within_limit(self):
        limiter = RateLimiter(key="test", identifier="user:1", limit=3, window=60)
        for _ in range(3):
            assert limiter.allow() is True

    def test_blocks_requests_over_limit(self):
        limiter = RateLimiter(key="test", identifier="user:2", limit=3, window=60)
        for _ in range(3):
            limiter.allow()
        # 4th request should be blocked
        assert limiter.allow() is False

    def test_different_identifiers_are_independent(self):
        l1 = RateLimiter(key="login", identifier="ip:1.1.1.1", limit=2, window=60)
        l2 = RateLimiter(key="login", identifier="ip:2.2.2.2", limit=2, window=60)
        l1.allow()
        l1.allow()
        # l1 is exhausted but l2 should still be allowed
        assert l1.allow() is False
        assert l2.allow() is True

    def test_different_keys_are_independent(self):
        r1 = RateLimiter(key="login", identifier="user:3", limit=1, window=60)
        r2 = RateLimiter(key="register", identifier="user:3", limit=1, window=60)
        r1.allow()
        assert r1.allow() is False
        assert r2.allow() is True   # different action, separate bucket

    def test_check_returns_result_object(self):
        limiter = RateLimiter(key="check", identifier="user:4", limit=5, window=60)
        result = limiter.check()
        assert result.allowed is True
        assert result.current == 1
        assert result.limit == 5

    def test_result_has_retry_after_when_blocked(self):
        limiter = RateLimiter(key="retry", identifier="user:5", limit=1, window=60)
        limiter.allow()
        result = limiter.check()
        assert result.allowed is False
        assert result.retry_after > 0