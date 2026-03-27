# 📁 Location: backend/apps/likes/tests/test_cache.py
# ▶  Run:      pytest apps/likes/tests/test_cache.py -v

import pytest

from apps.likes.cache import (
    get_like_count,
    has_user_liked,
    like_decr,
    like_incr,
    set_like_count,
)
from core.redis.client import get_redis_client, reset_client

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def clean_redis():
    reset_client()
    get_redis_client().flushall()
    yield
    get_redis_client().flushall()
    reset_client()


class TestLikeIncr:
    def test_incr_returns_new_count(self):
        count = like_incr("post", "post-1", "user-1")
        assert count == 1

    def test_multiple_incr_accumulates(self):
        like_incr("post", "post-1", "user-1")
        like_incr("post", "post-1", "user-2")
        count = like_incr("post", "post-1", "user-3")
        assert count == 3

    def test_sets_user_membership_flag(self):
        like_incr("post", "post-1", "user-1")
        assert has_user_liked("user-1", "post", "post-1") is True

    def test_different_objects_are_independent(self):
        like_incr("post", "post-1", "user-1")
        like_incr("post", "post-2", "user-1")
        assert get_like_count("post", "post-1") == 1
        assert get_like_count("post", "post-2") == 1


class TestLikeDecr:
    def test_decr_reduces_count(self):
        like_incr("post", "post-1", "user-1")
        like_incr("post", "post-1", "user-2")
        count = like_decr("post", "post-1", "user-1")
        assert count == 1

    def test_decr_removes_membership_flag(self):
        like_incr("post", "post-1", "user-1")
        like_decr("post", "post-1", "user-1")
        assert has_user_liked("user-1", "post", "post-1") is False

    def test_decr_floors_at_zero(self):
        count = like_decr("post", "post-empty", "user-1")
        assert count == 0


class TestGetLikeCount:
    def test_returns_none_on_cache_miss(self):
        assert get_like_count("post", "post-missing") is None

    def test_returns_count_after_set(self):
        set_like_count("post", "post-1", 42)
        assert get_like_count("post", "post-1") == 42


class TestHasUserLiked:
    def test_false_before_like(self):
        assert has_user_liked("user-1", "post", "post-1") is False

    def test_true_after_like(self):
        like_incr("post", "post-1", "user-1")
        assert has_user_liked("user-1", "post", "post-1") is True

    def test_different_users_are_independent(self):
        like_incr("post", "post-1", "user-1")
        assert has_user_liked("user-2", "post", "post-1") is False
