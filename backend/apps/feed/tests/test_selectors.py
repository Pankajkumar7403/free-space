import pytest
from apps.feed.selectors import get_user_feed, get_explore_feed
from apps.posts.constants import PostVisibility, PostStatus


@pytest.mark.django_db
def test_feed_includes_own_posts(user_factory, post_factory):
    user = user_factory()
    own_public = post_factory(author=user, visibility=PostVisibility.PUBLIC, status=PostStatus.PUBLISHED)
    own_private = post_factory(author=user, visibility=PostVisibility.PRIVATE, status=PostStatus.PUBLISHED)
    qs = get_user_feed(user=user)
    ids = list(qs.values_list("pk", flat=True))
    assert own_public.pk in ids
    assert own_private.pk in ids


@pytest.mark.django_db
def test_feed_includes_followed_public_and_followers_only(user_factory, post_factory, follow_factory):
    user = user_factory()
    followed = user_factory()
    follow_factory(follower=user, following=followed, status="accepted")
    pub = post_factory(author=followed, visibility=PostVisibility.PUBLIC, status=PostStatus.PUBLISHED)
    fol = post_factory(author=followed, visibility=PostVisibility.FOLLOWERS_ONLY, status=PostStatus.PUBLISHED)
    prv = post_factory(author=followed, visibility=PostVisibility.PRIVATE, status=PostStatus.PUBLISHED)
    qs = get_user_feed(user=user)
    ids = list(qs.values_list("pk", flat=True))
    assert pub.pk in ids
    assert fol.pk in ids
    assert prv.pk not in ids


@pytest.mark.django_db
def test_feed_excludes_non_followed_posts(user_factory, post_factory):
    user = user_factory()
    stranger = user_factory()
    stranger_post = post_factory(author=stranger, visibility=PostVisibility.PUBLIC, status=PostStatus.PUBLISHED)
    qs = get_user_feed(user=user)
    ids = list(qs.values_list("pk", flat=True))
    assert stranger_post.pk not in ids


@pytest.mark.django_db
def test_feed_excludes_blocked_user_posts(user_factory, post_factory, follow_factory, block_factory):
    user = user_factory()
    blocked = user_factory()
    follow_factory(follower=user, following=blocked, status="accepted")
    block_factory(blocker=user, blocked=blocked)
    post = post_factory(author=blocked, visibility=PostVisibility.PUBLIC, status=PostStatus.PUBLISHED)
    qs = get_user_feed(user=user)
    ids = list(qs.values_list("pk", flat=True))
    assert post.pk not in ids


@pytest.mark.django_db
def test_feed_ordered_newest_first(user_factory, post_factory):
    user = user_factory()
    older = post_factory(author=user, visibility=PostVisibility.PUBLIC, status=PostStatus.PUBLISHED)
    newer = post_factory(author=user, visibility=PostVisibility.PUBLIC, status=PostStatus.PUBLISHED)
    qs = get_user_feed(user=user)
    pks = list(qs.values_list("pk", flat=True))
    assert pks.index(newer.pk) < pks.index(older.pk)


@pytest.mark.django_db
def test_explore_excludes_own_and_followed(user_factory, post_factory, follow_factory):
    user = user_factory()
    followed = user_factory()
    stranger = user_factory()
    follow_factory(follower=user, following=followed, status="accepted")
    own_post = post_factory(author=user, visibility=PostVisibility.PUBLIC, status=PostStatus.PUBLISHED)
    followed_post = post_factory(author=followed, visibility=PostVisibility.PUBLIC, status=PostStatus.PUBLISHED)
    discover_post = post_factory(author=stranger, visibility=PostVisibility.PUBLIC, status=PostStatus.PUBLISHED)
    qs = get_explore_feed(user=user)
    ids = list(qs.values_list("pk", flat=True))
    assert own_post.pk not in ids
    assert followed_post.pk not in ids
    assert discover_post.pk in ids
