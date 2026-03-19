# 📁 Location: backend/apps/posts/tests/test_services.py
# ▶  Run:      pytest apps/posts/tests/test_services.py -v

import pytest
from unittest.mock import patch, MagicMock

from apps.posts.constants import PostStatus, PostVisibility
from apps.posts.exceptions import PostEditForbiddenError, PostNotFoundError
from apps.posts.models import Hashtag, Post, PostHashtag
from apps.posts.services import (
    CreatePostInput,
    UpdatePostInput,
    create_post,
    delete_post,
    extract_hashtags,
    update_post,
)
from apps.posts.tests.factories import MediaFactory, PostFactory
from apps.users.tests.factories import UserFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestExtractHashtags:
    """Pure unit tests — no DB needed."""

    def test_extracts_single_tag(self):
        assert extract_hashtags("Hello #world") == ["world"]

    def test_extracts_multiple_tags(self):
        tags = extract_hashtags("I love #pride and #queer community")
        # "community" has no # prefix so it is NOT a hashtag
        assert set(tags) == {"pride", "queer"}

    def test_deduplicates_tags(self):
        tags = extract_hashtags("#rainbow #rainbow")
        assert tags.count("rainbow") == 1

    def test_lowercases_tags(self):
        tags = extract_hashtags("#LGBTQ #Pride")
        assert "lgbtq" in tags
        assert "pride" in tags

    def test_no_tags_returns_empty(self):
        assert extract_hashtags("no hashtags here") == []

    def test_ignores_hash_only(self):
        assert extract_hashtags("# alone") == []

    def test_handles_empty_string(self):
        assert extract_hashtags("") == []

    def test_max_tag_length_100(self):
        long_tag = "a" * 100
        tags = extract_hashtags(f"#{long_tag}")
        assert long_tag in tags

    def test_tag_over_100_chars_truncated(self):
        long_tag = "a" * 101
        tags = extract_hashtags(f"#{long_tag}")
        # regex only captures up to 100 chars
        assert len(tags[0]) <= 100


class TestCreatePost:
    @patch("apps.posts.services.emit_post_created")
    def test_creates_post_successfully(self, mock_emit, db, user):
        post = create_post(CreatePostInput(
            author_id=user.pk,
            content="Hello #world this is my first post",
        ))
        assert post.pk is not None
        assert post.author == user
        assert post.status == PostStatus.PUBLISHED

    @patch("apps.posts.services.emit_post_created")
    def test_extracts_and_saves_hashtags(self, mock_emit, db, user):
        post = create_post(CreatePostInput(
            author_id=user.pk,
            content="Celebrating #pride and #lgbtq community",
        ))
        tag_names = list(post.hashtags.values_list("name", flat=True))
        assert "pride" in tag_names
        assert "lgbtq" in tag_names

    @patch("apps.posts.services.emit_post_created")
    def test_upserts_existing_hashtags(self, mock_emit, db, user):
        """Creating two posts with the same tag reuses the same Hashtag row."""
        create_post(CreatePostInput(author_id=user.pk, content="#rainbow post 1"))
        create_post(CreatePostInput(author_id=user.pk, content="#rainbow post 2"))
        assert Hashtag.objects.filter(name="rainbow").count() == 1

    @patch("apps.posts.services.emit_post_created")
    def test_default_visibility_is_followers_only(self, mock_emit, db, user):
        post = create_post(CreatePostInput(author_id=user.pk, content="test"))
        assert post.visibility == PostVisibility.FOLLOWERS_ONLY

    @patch("apps.posts.services.emit_post_created")
    def test_respects_explicit_visibility(self, mock_emit, db, user):
        post = create_post(CreatePostInput(
            author_id=user.pk,
            content="public post",
            visibility=PostVisibility.PUBLIC,
        ))
        assert post.visibility == PostVisibility.PUBLIC

    @patch("apps.posts.services.emit_post_created")
    def test_anonymous_post(self, mock_emit, db, user):
        post = create_post(CreatePostInput(
            author_id=user.pk,
            content="anonymous post",
            is_anonymous=True,
        ))
        assert post.is_anonymous is True

    @patch("apps.posts.services.emit_post_created")
    def test_attaches_media(self, mock_emit, db, user):
        media = MediaFactory(owner=user)
        post  = create_post(CreatePostInput(
            author_id=user.pk,
            content="post with media",
            media_ids=[media.pk],
        ))
        assert post.media.filter(pk=media.pk).exists()

    @patch("apps.posts.services.emit_post_created")
    def test_emits_kafka_event(self, mock_emit, db, user):
        create_post(CreatePostInput(author_id=user.pk, content="test"))
        # on_commit fires synchronously in tests with CELERY_TASK_ALWAYS_EAGER
        mock_emit.assert_called_once()

    def test_raises_on_empty_content(self, db, user):
        from core.exceptions.base import ValidationError
        with pytest.raises(ValidationError):
            create_post(CreatePostInput(author_id=user.pk, content=""))

    def test_raises_on_content_too_long(self, db, user):
        from core.exceptions.base import ValidationError
        with pytest.raises(ValidationError):
            create_post(CreatePostInput(author_id=user.pk, content="x" * 2201))


class TestUpdatePost:
    @patch("apps.posts.services.emit_post_created")
    def test_updates_content(self, mock_emit, db, user):
        post    = create_post(CreatePostInput(author_id=user.pk, content="original"))
        updated = update_post(
            post_id=post.pk,
            requesting_user_id=user.pk,
            data=UpdatePostInput(content="updated content"),
        )
        assert updated.content == "updated content"

    @patch("apps.posts.services.emit_post_created")
    def test_re_extracts_hashtags_on_content_update(self, mock_emit, db, user):
        post = create_post(CreatePostInput(author_id=user.pk, content="#old tag"))
        update_post(
            post_id=post.pk,
            requesting_user_id=user.pk,
            data=UpdatePostInput(content="#new tag"),
        )
        tag_names = list(post.hashtags.values_list("name", flat=True))
        assert "new" in tag_names
        assert "old" not in tag_names

    @patch("apps.posts.services.emit_post_created")
    def test_updates_visibility(self, mock_emit, db, user):
        post    = create_post(CreatePostInput(author_id=user.pk, content="test"))
        updated = update_post(
            post_id=post.pk,
            requesting_user_id=user.pk,
            data=UpdatePostInput(visibility=PostVisibility.PUBLIC),
        )
        assert updated.visibility == PostVisibility.PUBLIC

    @patch("apps.posts.services.emit_post_created")
    def test_raises_if_not_author(self, mock_emit, db, user):
        other = UserFactory()
        post  = create_post(CreatePostInput(author_id=user.pk, content="test"))
        with pytest.raises(PostEditForbiddenError):
            update_post(
                post_id=post.pk,
                requesting_user_id=other.pk,
                data=UpdatePostInput(content="hacked"),
            )


class TestDeletePost:
    @patch("apps.posts.services.emit_post_created")
    @patch("apps.posts.services.emit_post_deleted")
    def test_soft_deletes_post(self, mock_del, mock_create, db, user):
        post = create_post(CreatePostInput(author_id=user.pk, content="bye"))
        delete_post(post_id=post.pk, requesting_user_id=user.pk)
        assert not Post.objects.filter(pk=post.pk).exists()
        assert Post.all_objects.filter(pk=post.pk).exists()

    @patch("apps.posts.services.emit_post_created")
    @patch("apps.posts.services.emit_post_deleted")
    def test_raises_if_not_author(self, mock_del, mock_create, db, user):
        other = UserFactory()
        post  = create_post(CreatePostInput(author_id=user.pk, content="mine"))
        with pytest.raises(PostEditForbiddenError):
            delete_post(post_id=post.pk, requesting_user_id=other.pk)

    @patch("apps.posts.services.emit_post_created")
    @patch("apps.posts.services.emit_post_deleted")
    def test_emits_deleted_event(self, mock_del, mock_create, db, user):
        post = create_post(CreatePostInput(author_id=user.pk, content="gone"))
        delete_post(post_id=post.pk, requesting_user_id=user.pk)
        mock_del.assert_called_once()