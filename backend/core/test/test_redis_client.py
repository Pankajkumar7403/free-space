# 📁 Location: backend/core/tests/test_redis_client.py
# ▶  Run:      pytest core/tests/test_redis_client.py -v
"""
test_redis_client.py
~~~~~~~~~~~~~~~~~~~~
Tests for core/redis/client.py and core/redis/cache.py

All tests use fakeredis — no real Redis needed.
"""
from __future__ import annotations

import pytest

from core.redis.cache import (
    blacklist_token,
    cache_delete,
    cache_get,
    cache_set,
    counter_decr,
    counter_get,
    counter_incr,
    feed_get,
    feed_push,
    feed_remove,
    feed_trim,
    is_token_blacklisted,
)
from core.redis.client import get_redis_client, reset_client

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def fresh_redis():
    """Flush fakeredis between tests."""
    reset_client()
    client = get_redis_client()
    client.flushall()
    yield
    client.flushall()
    reset_client()


class TestRedisClient:
    def test_client_is_reachable(self):
        client = get_redis_client()
        assert client.ping()

    def test_singleton_returns_same_instance(self):
        c1 = get_redis_client()
        c2 = get_redis_client()
        assert c1 is c2

    def test_reset_forces_new_instance(self):
        c1 = get_redis_client()
        reset_client()
        c2 = get_redis_client()
        # After reset a new object is created
        assert c1 is not c2


class TestCacheGetSet:
    def test_set_and_get_string(self):
        cache_set("test:str", "hello")
        assert cache_get("test:str") == "hello"

    def test_set_and_get_dict(self):
        data = {"user_id": "abc", "score": 99}
        cache_set("test:dict", data)
        assert cache_get("test:dict") == data

    def test_get_returns_none_on_miss(self):
        assert cache_get("test:missing") is None

    def test_delete_removes_key(self):
        cache_set("test:del", "value")
        cache_delete("test:del")
        assert cache_get("test:del") is None

    def test_ttl_is_respected(self):
        """Set with TTL=1 and verify it was stored (we don't wait 1s — just check TTL set)."""
        cache_set("test:ttl", "temporary", ttl=1)
        client = get_redis_client()
        ttl = client.ttl("test:ttl")
        assert ttl > 0


class TestCounters:
    def test_incr_returns_new_value(self):
        result = counter_incr("counter:test")
        assert result == 1

    def test_incr_accumulates(self):
        counter_incr("counter:acc")
        counter_incr("counter:acc")
        assert counter_get("counter:acc") == 2

    def test_decr_reduces_count(self):
        counter_incr("counter:dec")
        counter_incr("counter:dec")
        result = counter_decr("counter:dec")
        assert result == 1

    def test_decr_floors_at_zero(self):
        result = counter_decr("counter:empty")
        assert result == 0

    def test_get_returns_zero_on_miss(self):
        assert counter_get("counter:missing") == 0


class TestFeedOperations:
    def test_push_and_get(self):
        feed_push("user:1", "post:100", score=1000.0)
        feed_push("user:1", "post:200", score=2000.0)
        result = feed_get("user:1")
        # Highest score (newest) first
        assert result[0] == "post:200"
        assert result[1] == "post:100"

    def test_remove_from_feed(self):
        feed_push("user:1", "post:100", score=1000.0)
        feed_remove("user:1", "post:100")
        assert feed_get("user:1") == []

    def test_trim_keeps_max_items(self):
        for i in range(10):
            feed_push("user:trim", f"post:{i}", score=float(i))
        feed_trim("user:trim", max_size=5)
        result = feed_get("user:trim", count=100)
        assert len(result) == 5

    def test_pagination(self):
        for i in range(5):
            feed_push("user:page", f"post:{i}", score=float(i))
        page1 = feed_get("user:page", cursor=0, count=3)
        page2 = feed_get("user:page", cursor=3, count=3)
        assert len(page1) == 3
        assert len(page2) == 2
        assert set(page1).isdisjoint(set(page2))


class TestTokenBlacklist:
    def test_blacklisted_token_is_detected(self):
        blacklist_token("jti-abc123", ttl=60)
        assert is_token_blacklisted("jti-abc123") is True

    def test_non_blacklisted_token_passes(self):
        assert is_token_blacklisted("jti-not-blacklisted") is False