# 📁 Location: backend/apps/feed/tests/test_cache.py
# ▶  Run:      pytest apps/feed/tests/test_cache.py -v

import pytest
from core.redis.client import get_redis_client, reset_client
from apps.feed.cache import (
    feed_push_post, feed_get_page, feed_exists, feed_size,
    feed_remove_post, feed_delete, feed_push_batch,
    mark_feed_warm, is_feed_warm,
    explore_push, explore_get_page,
)
from apps.feed.constants import FEED_MAX_SIZE

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def clean_redis():
    reset_client()
    get_redis_client().flushall()
    yield
    get_redis_client().flushall()
    reset_client()


class TestFeedPushGet:
    def test_push_and_get_single_post(self):
        feed_push_post("user:1", "post:100", score=0.9)
        result = feed_get_page("user:1", cursor=0, page_size=10)
        assert "post:100" in result

    def test_higher_score_returned_first(self):
        feed_push_post("user:1", "post:old",  score=0.3)
        feed_push_post("user:1", "post:new",  score=0.9)
        result = feed_get_page("user:1", cursor=0, page_size=10)
        assert result[0] == "post:new"
        assert result[1] == "post:old"

    def test_cursor_pagination(self):
        for i in range(10):
            feed_push_post("user:page", f"post:{i}", score=float(i))
        page1 = feed_get_page("user:page", cursor=0, page_size=5)
        page2 = feed_get_page("user:page", cursor=5, page_size=5)
        assert len(page1) == 5
        assert len(page2) == 5
        assert set(page1).isdisjoint(set(page2))

    def test_batch_push(self):
        feed_push_batch("user:batch", {"post:a": 0.8, "post:b": 0.6, "post:c": 0.4})
        result = feed_get_page("user:batch", cursor=0, page_size=10)
        assert set(result) == {"post:a", "post:b", "post:c"}

    def test_empty_feed_returns_empty_list(self):
        result = feed_get_page("user:empty", cursor=0, page_size=10)
        assert result == []


class TestFeedExistsAndSize:
    def test_feed_exists_after_push(self):
        assert not feed_exists("user:new")
        feed_push_post("user:new", "post:1", score=1.0)
        assert feed_exists("user:new")

    def test_feed_size(self):
        for i in range(5):
            feed_push_post("user:sz", f"post:{i}", score=float(i))
        assert feed_size("user:sz") == 5


class TestFeedInvalidation:
    def test_remove_post_from_feed(self):
        feed_push_post("user:rm", "post:x", score=1.0)
        feed_remove_post("user:rm", "post:x")
        result = feed_get_page("user:rm", cursor=0, page_size=10)
        assert "post:x" not in result

    def test_delete_entire_feed(self):
        feed_push_post("user:del", "post:1", score=1.0)
        feed_delete("user:del")
        assert not feed_exists("user:del")


class TestFeedTrimming:
    def test_feed_trimmed_to_max_size(self):
        for i in range(FEED_MAX_SIZE + 10):
            feed_push_post("user:trim", f"post:{i}", score=float(i))
        assert feed_size("user:trim") <= FEED_MAX_SIZE


class TestFeedWarmUp:
    def test_mark_and_check_warm(self):
        assert not is_feed_warm("user:cold")
        mark_feed_warm("user:cold")
        assert is_feed_warm("user:cold")


class TestExploreFeed:
    def test_push_and_get_explore(self):
        explore_push("post:trending", score=0.99)
        result = explore_get_page(cursor=0, page_size=10)
        assert "post:trending" in result

    def test_explore_returns_highest_score_first(self):
        explore_push("post:low",  score=0.1)
        explore_push("post:high", score=0.9)
        result = explore_get_page(cursor=0, page_size=10)
        assert result[0] == "post:high"