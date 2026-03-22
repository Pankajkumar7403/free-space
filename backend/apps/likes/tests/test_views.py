# 📁 Location: backend/apps/likes/tests/test_views.py
# ▶  Run:      pytest apps/likes/tests/test_views.py -v

import pytest
from unittest.mock import patch
from core.redis.client import get_redis_client, reset_client
from apps.posts.tests.factories import PostFactory
from apps.posts.constants import PostVisibility
from apps.users.tests.factories import UserFactory
from core.testing.base import BaseAPITestCase

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]


@pytest.fixture(autouse=True)
def clean_redis():
    reset_client()
    get_redis_client().flushall()
    yield
    get_redis_client().flushall()
    reset_client()


class TestPostLikeView(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user  = UserFactory()
        self.other = UserFactory()
        self.post  = PostFactory(author=self.other, visibility=PostVisibility.PUBLIC)
        self.authenticate(self.user)
        self.url = f"/api/v1/posts/{self.post.pk}/like/"

    def test_get_like_count(self):
        res = self.client.get(self.url)
        self.assert_ok(res)
        assert res.data["count"] == 0
        assert res.data["liked_by_me"] is False

    @patch("apps.likes.services.emit_like_created")
    def test_like_post(self, mock_emit):
        res = self.client.post(self.url)
        self.assert_created(res)
        assert res.data["count"] == 1
        assert res.data["liked_by_me"] is True

    @patch("apps.likes.services.emit_like_created")
    def test_unlike_post(self, mock_emit):
        self.client.post(self.url)
        res = self.client.delete(self.url)
        self.assert_ok(res)
        assert res.data["liked_by_me"] is False

    @patch("apps.likes.services.emit_like_created")
    def test_double_like_returns_409(self, mock_emit):
        self.client.post(self.url)
        res = self.client.post(self.url)
        self.assert_status(res, 409)
        self.assert_error_code(res, "ALREADY_LIKED")

    def test_unlike_without_like_returns_400(self):
        res = self.client.delete(self.url)
        self.assert_bad_request(res)
        self.assert_error_code(res, "NOT_LIKED")

    def test_unauthenticated_returns_401(self):
        self.logout()
        res = self.client.post(self.url)
        self.assert_unauthorized(res)