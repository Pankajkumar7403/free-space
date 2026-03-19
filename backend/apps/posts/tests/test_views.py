# 📁 Location: backend/apps/posts/tests/test_views.py
# ▶  Run:      pytest apps/posts/tests/test_views.py -v

import pytest
from unittest.mock import patch

from apps.posts.constants import PostVisibility
from apps.posts.tests.factories import MediaFactory, PostFactory
from apps.users.tests.factories import UserFactory
from core.testing.base import BaseAPITestCase

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]


class TestPostCreateView(BaseAPITestCase):
    url = "/api/v1/posts/"

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    @patch("apps.posts.services.emit_post_created")
    def test_create_post_success(self, mock_emit):
        res = self.client.post(self.url, {
            "content": "My first post #pride",
            "visibility": "public",
        })
        self.assert_created(res)
        assert res.data["content"] == "My first post #pride"
        assert any(t["name"] == "pride" for t in res.data["hashtags"])

    @patch("apps.posts.services.emit_post_created")
    def test_create_post_default_visibility_followers_only(self, mock_emit):
        res = self.client.post(self.url, {"content": "quiet post"})
        self.assert_created(res)
        assert res.data["visibility"] == "followers_only"

    def test_create_post_empty_content_rejected(self):
        res = self.client.post(self.url, {"content": ""})
        self.assert_bad_request(res)

    def test_create_post_unauthenticated_rejected(self):
        self.logout()
        res = self.client.post(self.url, {"content": "hello"})
        self.assert_unauthorized(res)

    @patch("apps.posts.services.emit_post_created")
    def test_create_anonymous_post(self, mock_emit):
        res = self.client.post(self.url, {
            "content": "anonymous post",
            "is_anonymous": True,
        })
        self.assert_created(res)
        assert res.data["is_anonymous"] is True
        # Author username hidden in anonymous posts - serializer returns None for avatar


class TestPostDetailView(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    @patch("apps.posts.services.emit_post_created")
    def test_get_own_post(self, mock_emit):
        post = PostFactory(author=self.user, visibility=PostVisibility.PUBLIC)
        res  = self.client.get(f"/api/v1/posts/{post.pk}/")
        self.assert_ok(res)
        assert str(res.data["id"]) == str(post.pk)

    @patch("apps.posts.services.emit_post_created")
    def test_get_public_post_from_other_user(self, mock_emit):
        other = UserFactory()
        post  = PostFactory(author=other, visibility=PostVisibility.PUBLIC)
        res   = self.client.get(f"/api/v1/posts/{post.pk}/")
        self.assert_ok(res)

    @patch("apps.posts.services.emit_post_created")
    def test_private_post_returns_404_for_others(self, mock_emit):
        other = UserFactory()
        post  = PostFactory(author=other, private=True)
        res   = self.client.get(f"/api/v1/posts/{post.pk}/")
        self.assert_not_found(res)
        self.assert_error_code(res, "POST_NOT_FOUND")

    @patch("apps.posts.services.emit_post_created")
    def test_update_own_post(self, mock_emit):
        post = PostFactory(author=self.user, visibility=PostVisibility.PUBLIC)
        res  = self.client.patch(f"/api/v1/posts/{post.pk}/", {"content": "updated"})
        self.assert_ok(res)
        assert res.data["content"] == "updated"

    @patch("apps.posts.services.emit_post_created")
    def test_update_other_post_forbidden(self, mock_emit):
        other = UserFactory()
        post  = PostFactory(author=other, visibility=PostVisibility.PUBLIC)
        res   = self.client.patch(f"/api/v1/posts/{post.pk}/", {"content": "hacked"})
        self.assert_forbidden(res)

    @patch("apps.posts.services.emit_post_created")
    @patch("apps.posts.services.emit_post_deleted")
    def test_delete_own_post(self, mock_del, mock_create):
        post = PostFactory(author=self.user, visibility=PostVisibility.PUBLIC)
        res  = self.client.delete(f"/api/v1/posts/{post.pk}/")
        self.assert_no_content(res)

    @patch("apps.posts.services.emit_post_created")
    @patch("apps.posts.services.emit_post_deleted")
    def test_delete_other_post_forbidden(self, mock_del, mock_create):
        other = UserFactory()
        post  = PostFactory(author=other, visibility=PostVisibility.PUBLIC)
        res   = self.client.delete(f"/api/v1/posts/{post.pk}/")
        self.assert_forbidden(res)


class TestPostListView(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    @patch("apps.posts.services.emit_post_created")
    def test_lists_own_posts(self, mock_emit):
        PostFactory(author=self.user, visibility=PostVisibility.PUBLIC)
        PostFactory(author=self.user, visibility=PostVisibility.PUBLIC)
        res = self.client.get("/api/v1/posts/")
        self.assert_ok(res)
        assert len(res.data["results"]) >= 2


class TestMediaPresignView(BaseAPITestCase):
    url = "/api/v1/posts/media/presign/"

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    @patch("apps.media.services.generate_presigned_upload_url",
           return_value="https://s3.example.com/upload?token=abc")
    def test_returns_presigned_url(self, mock_presign):
        res = self.client.post(self.url, {
            "mime_type": "image/jpeg",
            "file_size": 1024 * 500,
        })
        self.assert_created(res)
        assert "upload_url" in res.data
        assert "media_id" in res.data
        assert res.data["media_type"] == "image"

    def test_rejects_unsupported_mime_type(self):
        res = self.client.post(self.url, {
            "mime_type": "application/exe",
            "file_size": 1024,
        })
        self.assert_bad_request(res)
        self.assert_error_code(res, "INVALID_MEDIA_TYPE")

    def test_rejects_file_too_large(self):
        res = self.client.post(self.url, {
            "mime_type": "image/jpeg",
            "file_size": 100 * 1024 * 1024,  # 100 MB — over 20 MB limit
        })
        self.assert_bad_request(res)
        self.assert_error_code(res, "FILE_TOO_LARGE")

    def test_unauthenticated_rejected(self):
        self.logout()
        res = self.client.post(self.url, {"mime_type": "image/jpeg", "file_size": 1024})
        self.assert_unauthorized(res)


class TestMediaConfirmView(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    @patch("apps.media.tasks.process_media_task.delay")
    def test_confirm_upload_triggers_processing(self, mock_task):
        media = MediaFactory(owner=self.user, pending=True)
        res   = self.client.post(f"/api/v1/posts/media/{media.pk}/confirm/")
        self.assert_ok(res)
        assert res.data["status"] == "uploaded"
        mock_task.assert_called_once_with(str(media.pk))

    def test_confirm_other_users_media_fails(self):
        other = UserFactory()
        media = MediaFactory(owner=other, pending=True)
        res   = self.client.post(f"/api/v1/posts/media/{media.pk}/confirm/")
        self.assert_not_found(res)


class TestHashtagViews(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    @patch("apps.posts.services.emit_post_created")
    def test_get_posts_by_hashtag(self, mock_emit):
        from apps.posts.tests.factories import HashtagFactory
        tag  = HashtagFactory(name="testpride")
        post = PostFactory(author=self.user, visibility=PostVisibility.PUBLIC)
        post.hashtags.add(tag)
        res  = self.client.get("/api/v1/posts/hashtag/testpride/")
        self.assert_ok(res)

    def test_trending_hashtags(self):
        res = self.client.get("/api/v1/posts/hashtags/trending/")
        self.assert_ok(res)
        assert isinstance(res.data, list)