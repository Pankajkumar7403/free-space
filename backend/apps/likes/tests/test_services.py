# 📁 Location: backend/apps/likes/tests/test_services.py
# ▶  Run:      pytest apps/likes/tests/test_services.py -v

import pytest
from unittest.mock import patch
from core.redis.client import get_redis_client, reset_client
from apps.likes.services import get_like_count, is_liked_by, like_object, unlike_object
from apps.likes.exceptions import AlreadyLikedError, NotLikedError
from apps.likes.models import Like
from apps.posts.tests.factories import PostFactory
from apps.posts.constants import PostVisibility
from apps.users.tests.factories import UserFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


@pytest.fixture(autouse=True)
def clean_redis():
    reset_client()
    get_redis_client().flushall()
    yield
    get_redis_client().flushall()
    reset_client()


class TestLikeObject:
    @patch("apps.likes.services.emit_like_created")
    def test_like_post_successfully(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        like = like_object(user=user, obj=post)
        assert like.pk is not None
        assert Like.objects.filter(user=user, object_id=post.pk).exists()

    @patch("apps.likes.services.emit_like_created")
    def test_like_increments_redis_counter(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        like_object(user=user, obj=post)
        count = get_like_count(obj=post)
        assert count == 1

    @patch("apps.likes.services.emit_like_created")
    def test_multiple_likes_increment_counter(self, mock_emit, db):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        u1 = UserFactory()
        u2 = UserFactory()
        u3 = UserFactory()
        like_object(user=u1, obj=post)
        like_object(user=u2, obj=post)
        like_object(user=u3, obj=post)
        assert get_like_count(obj=post) == 3

    @patch("apps.likes.services.emit_like_created")
    def test_raises_on_duplicate_like(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        like_object(user=user, obj=post)
        with pytest.raises(AlreadyLikedError):
            like_object(user=user, obj=post)

    @patch("apps.likes.services.emit_like_created")
    def test_emits_kafka_event(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        like_object(user=user, obj=post)
        mock_emit.assert_called_once()


class TestUnlikeObject:
    @patch("apps.likes.services.emit_like_created")
    def test_unlike_removes_db_row(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        like_object(user=user, obj=post)
        unlike_object(user=user, obj=post)
        assert not Like.objects.filter(user=user, object_id=post.pk).exists()

    @patch("apps.likes.services.emit_like_created")
    def test_unlike_decrements_redis_counter(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        like_object(user=user, obj=post)
        unlike_object(user=user, obj=post)
        assert get_like_count(obj=post) == 0

    def test_unlike_raises_if_not_liked(self, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        with pytest.raises(NotLikedError):
            unlike_object(user=user, obj=post)

    @patch("apps.likes.services.emit_like_created")
    def test_counter_never_goes_below_zero(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        like_object(user=user, obj=post)
        unlike_object(user=user, obj=post)
        # Counter is 0, calling again raises NotLikedError not negative count
        with pytest.raises(NotLikedError):
            unlike_object(user=user, obj=post)
        assert get_like_count(obj=post) == 0


class TestGetLikeCount:
    @patch("apps.likes.services.emit_like_created")
    def test_count_from_redis(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        like_object(user=user, obj=post)
        count = get_like_count(obj=post)
        assert count == 1

    def test_count_fallback_from_db_on_cache_miss(self, db, user):
        """When Redis is cold, count comes from DB."""
        from apps.likes.models import Like
        from django.contrib.contenttypes.models import ContentType
        from apps.posts.models import Post
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        ct   = ContentType.objects.get_for_model(Post)
        Like.objects.create(user=user, content_type=ct, object_id=post.pk)
        # Redis is flushed — count must come from DB
        count = get_like_count(obj=post)
        assert count == 1


class TestIsLikedBy:
    @patch("apps.likes.services.emit_like_created")
    def test_returns_true_after_like(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        like_object(user=user, obj=post)
        assert is_liked_by(user=user, obj=post) is True

    def test_returns_false_before_like(self, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        assert is_liked_by(user=user, obj=post) is False

    @patch("apps.likes.services.emit_like_created")
    def test_returns_false_after_unlike(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        like_object(user=user, obj=post)
        unlike_object(user=user, obj=post)
        assert is_liked_by(user=user, obj=post) is False