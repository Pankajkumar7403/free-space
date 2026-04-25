# 📁 Location: backend/apps/feed/tests/test_views.py
# ▶  Run:      pytest apps/feed/tests/test_views.py -v

import pytest

from apps.users.tests.factories import UserFactory
from core.testing.base import BaseAPITestCase

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]


class TestFeedView(BaseAPITestCase):
    url = "/api/v1/feed/"

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_returns_feed_page(self):
        res = self.client.get(self.url)
        self.assert_ok(res)
        assert "results" in res.data
        assert "pagination" in res.data
        assert "next_cursor" in res.data["pagination"]

    def test_unauthenticated_returns_401(self):
        self.logout()
        res = self.client.get(self.url)
        self.assert_unauthorized(res)

    def test_accepts_page_size_param(self):
        res = self.client.get(self.url, {"page_size": 5})
        self.assert_ok(res)

    def test_page_size_capped_at_max(self):
        res = self.client.get(self.url, {"page_size": 999})
        self.assert_ok(res)


class TestExploreFeedView(BaseAPITestCase):
    url = "/api/v1/feed/explore/"

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_returns_explore_page(self):
        res = self.client.get(self.url)
        self.assert_ok(res)
        assert "results" in res.data
        assert "pagination" in res.data


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
