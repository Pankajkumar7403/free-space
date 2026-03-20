# 📁 Location: backend/apps/feed/tests/test_views.py
# ▶  Run:      pytest apps/feed/tests/test_views.py -v

import pytest
from unittest.mock import patch, MagicMock

from apps.users.tests.factories import UserFactory
from apps.posts.tests.factories import PostFactory
from apps.posts.constants import PostVisibility
from apps.users.models import Follow
from core.testing.base import BaseAPITestCase

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]


class TestFeedView(BaseAPITestCase):
    url = "/api/v1/feed/"

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    @patch("apps.feed.views.get_user_feed")
    def test_returns_feed_page(self, mock_feed):
        mock_feed.return_value = MagicMock(posts=[], next_cursor=None, source="redis")
        res = self.client.get(self.url)
        self.assert_ok(res)
        assert "results" in res.data
        assert "next_cursor" in res.data
        assert "source" in res.data

    def test_unauthenticated_returns_401(self):
        self.logout()
        res = self.client.get(self.url)
        self.assert_unauthorized(res)

    @patch("apps.feed.views.get_user_feed")
    def test_accepts_cursor_param(self, mock_feed):
        mock_feed.return_value = MagicMock(posts=[], next_cursor=None, source="db")
        res = self.client.get(self.url, {"cursor": 20})
        self.assert_ok(res)
        kwargs = mock_feed.call_args.kwargs
        assert kwargs["cursor"] == 20

    @patch("apps.feed.views.get_user_feed")
    def test_page_size_capped_at_50(self, mock_feed):
        mock_feed.return_value = MagicMock(posts=[], next_cursor=None, source="redis")
        res = self.client.get(self.url, {"page_size": 999})
        self.assert_ok(res)
        kwargs = mock_feed.call_args.kwargs
        assert kwargs["page_size"] <= 50


class TestExploreFeedView(BaseAPITestCase):
    url = "/api/v1/feed/explore/"

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    @patch("apps.feed.views.get_explore_feed")
    def test_returns_explore_page(self, mock_explore):
        mock_explore.return_value = MagicMock(posts=[], next_cursor=None, source="redis")
        res = self.client.get(self.url)
        self.assert_ok(res)
        assert "results" in res.data


class TestHashtagSubscriptionView(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_subscribe_to_hashtag(self):
        res = self.client.post("/api/v1/feed/hashtags/pride/subscribe/")
        self.assert_created(res)
        assert res.data["subscribed"] is True
        assert res.data["hashtag"] == "pride"

    def test_unsubscribe_from_hashtag(self):
        self.client.post("/api/v1/feed/hashtags/pride/subscribe/")
        res = self.client.delete("/api/v1/feed/hashtags/pride/subscribe/")
        self.assert_no_content(res)

    def test_unauthenticated_subscribe_rejected(self):
        self.logout()
        res = self.client.post("/api/v1/feed/hashtags/pride/subscribe/")
        self.assert_unauthorized(res)