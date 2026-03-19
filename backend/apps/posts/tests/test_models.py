# 📁 Location: backend/apps/posts/tests/test_models.py
# ▶  Run:      pytest apps/posts/tests/test_models.py -v

import uuid
import pytest
from django.db import IntegrityError

from apps.posts.constants import MediaStatus, MediaType, PostStatus, PostVisibility
from apps.posts.models import Hashtag, Media, Post, PostHashtag, PostMedia
from apps.posts.tests.factories import HashtagFactory, MediaFactory, PostFactory
from apps.users.tests.factories import UserFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestPostModel:
    def test_pk_is_uuid(self, post):
        assert isinstance(post.pk, uuid.UUID)

    def test_str_shows_preview(self, db, user):
        p = PostFactory(author=user, content="Hello world this is a test post")
        assert "Hello world" in str(p)

    def test_str_truncates_long_content(self, db, user):
        p = PostFactory(author=user, content="x" * 200)
        assert "…" in str(p)

    def test_default_visibility_is_followers_only(self, db, user):
        p = PostFactory(author=user, followers_only=True)
        assert p.visibility == PostVisibility.FOLLOWERS_ONLY

    def test_default_status_is_published(self, post):
        assert post.status == PostStatus.PUBLISHED

    def test_soft_delete_hides_post(self, post):
        post.soft_delete()
        assert not Post.objects.filter(pk=post.pk).exists()
        assert Post.all_objects.filter(pk=post.pk).exists()

    def test_restore_makes_post_visible(self, post):
        post.soft_delete()
        post.restore()
        assert Post.objects.filter(pk=post.pk).exists()

    def test_is_anonymous_flag(self, db, user):
        p = PostFactory(author=user, anonymous=True)
        assert p.is_anonymous is True

    def test_allow_comments_default_true(self, post):
        assert post.allow_comments is True

    def test_no_comments_trait(self, db, user):
        p = PostFactory(author=user, no_comments=True)
        assert p.allow_comments is False


class TestHashtagModel:
    def test_str_includes_hash(self, hashtag):
        assert str(hashtag).startswith("#")

    def test_name_is_unique(self, db):
        HashtagFactory(name="unique")
        with pytest.raises(IntegrityError):
            HashtagFactory(name="unique")

    def test_name_is_case_sensitive_in_db(self, db):
        # DB stores lowercase — our service normalises before insert
        HashtagFactory(name="rainbow")
        # different case is a different row at DB level
        h2 = HashtagFactory(name="Rainbow")
        assert h2.pk is not None


class TestMediaModel:
    def test_pk_is_uuid(self, ready_media):
        assert isinstance(ready_media.pk, uuid.UUID)

    def test_is_ready_property(self, ready_media):
        assert ready_media.is_ready is True

    def test_is_ready_false_when_pending(self, pending_media):
        assert pending_media.is_ready is False

    def test_display_url_returns_processed_url(self, ready_media):
        assert ready_media.display_url == ready_media.processed_url

    def test_display_url_falls_back_to_original(self, db, user):
        m = MediaFactory(owner=user, processed_url="")
        assert m.display_url == m.original_url

    def test_display_url_empty_when_no_urls(self, db, user):
        m = MediaFactory(owner=user, processed_url="", original_url="")
        assert m.display_url == ""

    def test_soft_delete(self, ready_media):
        ready_media.soft_delete()
        assert not Media.objects.filter(pk=ready_media.pk).exists()


class TestPostHashtagModel:
    def test_unique_together(self, db, user):
        post = PostFactory(author=user)
        tag  = HashtagFactory()
        PostHashtag.objects.create(post=post, hashtag=tag)
        with pytest.raises(IntegrityError):
            PostHashtag.objects.create(post=post, hashtag=tag)


class TestPostMediaModel:
    def test_ordered_by_position(self, db, user):
        post = PostFactory(author=user)
        m1 = MediaFactory(owner=user)
        m2 = MediaFactory(owner=user)
        PostMedia.objects.create(post=post, media=m1, position=1)
        PostMedia.objects.create(post=post, media=m2, position=0)
        positions = list(PostMedia.objects.filter(post=post).values_list("position", flat=True))
        assert positions == sorted(positions)