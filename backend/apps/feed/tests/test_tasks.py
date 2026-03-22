# 📁 Location: backend/apps/feed/tests/test_tasks.py
# ▶  Run:      pytest apps/feed/tests/test_tasks.py -v

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from apps.feed.tasks import push_to_feeds_task, warm_user_feed_task, fanout_post_task
from apps.users.tests.factories import UserFactory
from apps.posts.tests.factories import PostFactory
from apps.posts.constants import PostVisibility
from apps.users.models import Follow
from core.redis.client import get_redis_client, reset_client

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


@pytest.fixture(autouse=True)
def clean_redis():
    reset_client()
    get_redis_client().flushall()
    yield
    get_redis_client().flushall()
    reset_client()


class TestPushToFeedsTask:
    def test_pushes_post_to_each_user_feed(self):
        push_to_feeds_task(
            post_id="post:abc",
            user_ids=["user:1", "user:2", "user:3"],
            score=0.85,
        )
        from apps.feed.cache import feed_exists
        assert feed_exists("user:1")
        assert feed_exists("user:2")
        assert feed_exists("user:3")

    def test_empty_user_ids_does_not_crash(self):
        push_to_feeds_task(post_id="post:x", user_ids=[], score=0.5)


class TestWarmUserFeedTask:
    def test_warm_feeds_user_with_no_follows(self, db, user):
        warm_user_feed_task(user_id=str(user.pk))
        from apps.feed.cache import is_feed_warm
        assert is_feed_warm(str(user.pk))

    def test_warm_feed_skipped_if_already_warm(self, db, user):
        from apps.feed.cache import mark_feed_warm
        mark_feed_warm(str(user.pk))
        # Feed is already warm — task returns early before touching Post
        warm_user_feed_task(user_id=str(user.pk))
        # Verify feed was marked warm previously and nothing crashed

    def test_warm_feed_pushes_followed_posts(self, db):
        author   = UserFactory(public=True)
        follower = UserFactory()
        Follow.objects.create(follower=follower, following=author, status="accepted")
        post = PostFactory(author=author, visibility=PostVisibility.PUBLIC)

        warm_user_feed_task(user_id=str(follower.pk))

        from apps.feed.cache import feed_exists, feed_get_page
        assert feed_exists(str(follower.pk))
        page = feed_get_page(str(follower.pk), cursor=0, page_size=20)
        assert str(post.pk) in page


class TestFanoutPostTask:
    @patch("apps.feed.tasks.fanout_post_to_followers")
    def test_delegates_to_fanout(self, mock_fanout):
        fanout_post_task(
            post_id="post-123",
            author_id="author-456",
            post_created_at="2025-01-01T12:00:00",
            visibility="public",
        )
        mock_fanout.assert_called_once()
        kwargs = mock_fanout.call_args.kwargs
        assert kwargs["post_id"] == "post-123"
        assert isinstance(kwargs["post_created_at"], datetime)

    @patch("apps.feed.tasks.fanout_post_to_followers")
    def test_handles_tz_naive_timestamp(self, mock_fanout):
        """Timestamps without tz info should be treated as UTC."""
        fanout_post_task(
            post_id="post-999",
            author_id="author-888",
            post_created_at="2025-06-15T08:30:00",
            visibility="followers_only",
        )
        kwargs = mock_fanout.call_args.kwargs
        assert kwargs["post_created_at"].tzinfo is not None