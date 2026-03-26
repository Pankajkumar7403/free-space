# 📁 Location: backend/apps/posts/tests/test_selectors.py
# ▶  Run:      pytest apps/posts/tests/test_selectors.py -v

import pytest

from apps.posts.constants import PostVisibility
from apps.posts.exceptions import PostNotFoundError
from apps.posts.selectors import (
    get_post_by_id,
    get_posts_by_author,
    get_posts_by_hashtag,
    get_trending_hashtags,
)
from apps.posts.tests.factories import HashtagFactory, PostFactory
from apps.users.models import BlockedUser, Follow
from apps.users.tests.factories import UserFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestGetPostById:
    def test_returns_published_post(self, post, user):
        result = get_post_by_id(post.pk, requesting_user=user)
        assert result.pk == post.pk

    def test_raises_for_deleted_post(self, post, user):
        post.soft_delete()
        with pytest.raises(PostNotFoundError):
            get_post_by_id(post.pk, requesting_user=user)

    def test_raises_for_missing_id(self, user):
        import uuid

        with pytest.raises(PostNotFoundError):
            get_post_by_id(uuid.uuid4(), requesting_user=user)

    def test_public_post_visible_to_anyone(self, db):
        author = UserFactory(public=True)
        reader = UserFactory()
        post = PostFactory(author=author, visibility=PostVisibility.PUBLIC)
        result = get_post_by_id(post.pk, requesting_user=reader)
        assert result.pk == post.pk

    def test_private_post_hidden_from_non_author(self, db):
        author = UserFactory()
        reader = UserFactory()
        post = PostFactory(author=author, private=True)
        with pytest.raises(PostNotFoundError):
            get_post_by_id(post.pk, requesting_user=reader)

    def test_followers_only_visible_to_follower(self, db):
        author = UserFactory()
        follower = UserFactory()
        Follow.objects.create(follower=follower, following=author, status="accepted")
        post = PostFactory(author=author, followers_only=True)
        result = get_post_by_id(post.pk, requesting_user=follower)
        assert result.pk == post.pk

    def test_followers_only_hidden_from_non_follower(self, db):
        author = UserFactory()
        reader = UserFactory()
        post = PostFactory(author=author, followers_only=True)
        with pytest.raises(PostNotFoundError):
            get_post_by_id(post.pk, requesting_user=reader)

    def test_blocked_user_cannot_see_post(self, db):
        author = UserFactory()
        reader = UserFactory()
        BlockedUser.objects.create(blocker=author, blocked=reader)
        post = PostFactory(author=author, visibility=PostVisibility.PUBLIC)
        with pytest.raises(PostNotFoundError):
            get_post_by_id(post.pk, requesting_user=reader)

    def test_author_can_always_see_own_post(self, db):
        author = UserFactory()
        post = PostFactory(author=author, private=True)
        result = get_post_by_id(post.pk, requesting_user=author)
        assert result.pk == post.pk


class TestGetPostsByAuthor:
    def test_returns_own_posts(self, db, user):
        PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        qs = get_posts_by_author(user, requesting_user=user)
        assert qs.count() >= 2

    def test_excludes_deleted_posts(self, db, user):
        p = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        p.soft_delete()
        qs = get_posts_by_author(user, requesting_user=user)
        pks = list(qs.values_list("pk", flat=True))
        assert p.pk not in pks

    def test_non_follower_sees_only_public(self, db):
        author = UserFactory()
        reader = UserFactory()
        pub = PostFactory(author=author, visibility=PostVisibility.PUBLIC)
        priv = PostFactory(author=author, followers_only=True)
        qs = get_posts_by_author(author, requesting_user=reader)
        pks = list(qs.values_list("pk", flat=True))
        assert pub.pk in pks
        assert priv.pk not in pks


class TestGetPostsByHashtag:
    def test_returns_posts_with_hashtag(self, db, user):
        tag = HashtagFactory(name="pride")
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        post.hashtags.add(tag)
        qs = get_posts_by_hashtag("pride")
        assert post.pk in qs.values_list("pk", flat=True)

    def test_case_insensitive(self, db, user):
        tag = HashtagFactory(name="rainbow")
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        post.hashtags.add(tag)
        qs = get_posts_by_hashtag("RAINBOW")
        assert post.pk in qs.values_list("pk", flat=True)

    def test_only_returns_public_posts(self, db, user):
        tag = HashtagFactory(name="quiet")
        post = PostFactory(author=user, private=True)
        post.hashtags.add(tag)
        qs = get_posts_by_hashtag("quiet")
        assert post.pk not in qs.values_list("pk", flat=True)


class TestGetTrendingHashtags:
    def test_returns_hashtags(self, db, user):
        tag1 = HashtagFactory(name="lgbtq")
        tag2 = HashtagFactory(name="pride")
        p1 = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        p2 = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        p1.hashtags.add(tag1)
        p2.hashtags.add(tag1)
        p2.hashtags.add(tag2)
        results = get_trending_hashtags(limit=10)
        names = [h.name for h in results]
        assert "lgbtq" in names
        assert "pride" in names
