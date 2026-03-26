# 📁 Location: backend/apps/feed/tests/test_fanout.py
# ▶  Run:      pytest apps/feed/tests/test_fanout.py -v

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from apps.feed.constants import CELEBRITY_FOLLOWER_THRESHOLD
from apps.feed.fanout import (
    fanout_post_to_followers,
    invalidate_user_feed,
    remove_post_from_feeds,
)
from apps.users.models import Follow
from apps.users.tests.factories import UserFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestFanoutPostToFollowers:

    @patch("apps.feed.tasks.push_to_feeds_task")
    def test_fanout_pushes_to_all_followers(self, mock_task, db):
        author = UserFactory(public=True)
        f1 = UserFactory()
        f2 = UserFactory()
        f3 = UserFactory()
        Follow.objects.create(follower=f1, following=author, status="accepted")
        Follow.objects.create(follower=f2, following=author, status="accepted")
        Follow.objects.create(follower=f3, following=author, status="accepted")

        now = datetime(2025, 1, 1, tzinfo=UTC)
        fanout_post_to_followers(
            post_id="post-abc",
            author_id=str(author.pk),
            post_created_at=now,
            visibility="public",
        )
        assert mock_task.delay.called

    @patch("apps.feed.tasks.push_to_feeds_task")
    def test_celebrity_mode_skips_fanout(self, mock_task, db):
        """Authors with > threshold followers must NOT trigger write fanout."""
        author = UserFactory(public=True)
        # Create enough followers to trigger celebrity mode
        for _ in range(CELEBRITY_FOLLOWER_THRESHOLD + 1):
            follower = UserFactory()
            Follow.objects.create(
                follower=follower, following=author, status="accepted"
            )

        now = datetime(2025, 1, 1, tzinfo=UTC)
        fanout_post_to_followers(
            post_id="celeb-post",
            author_id=str(author.pk),
            post_created_at=now,
            visibility="public",
        )
        mock_task.delay.assert_not_called()

    @patch("apps.feed.tasks.push_to_feeds_task")
    def test_pending_follows_excluded(self, mock_task, db):
        """Only accepted follows trigger fanout."""
        author = UserFactory()
        pending = UserFactory()
        Follow.objects.create(follower=pending, following=author, status="pending")

        now = datetime(2025, 1, 1, tzinfo=UTC)
        fanout_post_to_followers(
            post_id="post-xyz",
            author_id=str(author.pk),
            post_created_at=now,
            visibility="public",
        )
        mock_task.delay.assert_not_called()

    @patch("apps.feed.tasks.push_to_feeds_task")
    def test_unknown_author_is_handled_gracefully(self, mock_task, db):
        """Missing author should not crash — just log and return."""
        fanout_post_to_followers(
            post_id="post-ghost",
            author_id="00000000-0000-0000-0000-000000000000",
            post_created_at=datetime(2025, 1, 1, tzinfo=UTC),
            visibility="public",
        )
        mock_task.delay.assert_not_called()


class TestRemovePostFromFeeds:
    @patch("apps.feed.fanout.feed_remove_post")
    def test_removes_from_all_follower_feeds(self, mock_remove, db):
        author = UserFactory()
        f1 = UserFactory()
        f2 = UserFactory()
        Follow.objects.create(follower=f1, following=author, status="accepted")
        Follow.objects.create(follower=f2, following=author, status="accepted")

        remove_post_from_feeds(post_id="post:del", author_id=str(author.pk))
        assert mock_remove.call_count == 2


class TestInvalidateUserFeed:
    @patch("apps.feed.fanout.feed_delete")
    def test_deletes_feed_from_redis(self, mock_delete, db):
        invalidate_user_feed(user_id="user:123")
        mock_delete.assert_called_once_with("user:123")
