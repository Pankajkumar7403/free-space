# 📁 Location: backend/apps/comments/tests/test_views.py
# ▶  Run:      pytest apps/comments/tests/test_views.py -v

import pytest
from unittest.mock import patch
from core.redis.client import get_redis_client, reset_client
from apps.comments.tests.factories import CommentFactory
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


class TestCommentListCreateView(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user  = UserFactory()
        self.other = UserFactory()
        self.post  = PostFactory(author=self.other, visibility=PostVisibility.PUBLIC)
        self.authenticate(self.user)
        self.url = f"/api/v1/posts/{self.post.pk}/comments/"

    def test_list_comments_empty(self):
        res = self.client.get(self.url)
        self.assert_ok(res)
        assert res.data["results"] == []

    @patch("apps.comments.services.emit_comment_created")
    def test_create_comment(self, mock_emit):
        res = self.client.post(self.url, {"content": "Nice post!"})
        self.assert_created(res)
        assert res.data["content"] == "Nice post!"
        assert res.data["depth"] == 0

    @patch("apps.comments.services.emit_comment_created")
    def test_create_reply(self, mock_emit):
        comment = CommentFactory(post=self.post, author=self.user)
        res = self.client.post(self.url, {
            "content": "I agree!", "parent_id": str(comment.pk)
        })
        self.assert_created(res)
        assert res.data["depth"] == 1

    def test_empty_content_rejected(self):
        res = self.client.post(self.url, {"content": ""})
        self.assert_bad_request(res)

    def test_unauthenticated_rejected(self):
        self.logout()
        res = self.client.post(self.url, {"content": "test"})
        self.assert_unauthorized(res)


class TestCommentDetailView(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user    = UserFactory()
        self.other   = UserFactory()
        self.post    = PostFactory(author=self.other, visibility=PostVisibility.PUBLIC)
        self.comment = CommentFactory(post=self.post, author=self.user)
        self.authenticate(self.user)
        self.url = f"/api/v1/posts/comments/{self.comment.pk}/"

    def test_get_comment(self):
        res = self.client.get(self.url)
        self.assert_ok(res)
        assert str(res.data["id"]) == str(self.comment.pk)

    def test_update_own_comment(self):
        res = self.client.patch(self.url, {"content": "edited"})
        self.assert_ok(res)
        assert res.data["content"] == "edited"

    def test_update_other_comment_forbidden(self):
        self.authenticate(self.other)
        res = self.client.patch(self.url, {"content": "hacked"})
        self.assert_forbidden(res)

    def test_delete_own_comment(self):
        res = self.client.delete(self.url)
        self.assert_no_content(res)

    def test_delete_other_comment_forbidden(self):
        stranger = UserFactory()
        self.authenticate(stranger)
        res = self.client.delete(self.url)
        self.assert_forbidden(res)


class TestCommentModerationViews(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.owner    = UserFactory()
        self.commenter = UserFactory()
        self.post     = PostFactory(author=self.owner, visibility=PostVisibility.PUBLIC)
        self.comment  = CommentFactory(post=self.post, author=self.commenter)
        self.authenticate(self.owner)

    def test_post_owner_can_pin_comment(self):
        res = self.client.post(f"/api/v1/posts/comments/{self.comment.pk}/pin/")
        self.assert_ok(res)
        assert res.data["is_pinned"] is True

    def test_non_owner_cannot_pin(self):
        self.authenticate(self.commenter)
        res = self.client.post(f"/api/v1/posts/comments/{self.comment.pk}/pin/")
        self.assert_forbidden(res)

    def test_post_owner_can_hide_comment(self):
        res = self.client.post(f"/api/v1/posts/comments/{self.comment.pk}/hide/")
        self.assert_ok(res)
        assert res.data["is_hidden"] is True

    def test_report_comment(self):
        res = self.client.post(
            f"/api/v1/posts/comments/{self.comment.pk}/report/",
            {"reason": "harassment"},
        )
        self.assert_ok(res)
        assert res.data["reported"] is True