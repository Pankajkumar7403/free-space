from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.posts.constants import PostStatus, PostVisibility
from apps.posts.models import Post
from apps.users.models import Follow
from apps.users.selectors import get_blocked_users


def get_user_feed(*, user) -> QuerySet:
    """
    Home feed: own posts + followed users' posts, newest first.
    Own posts: all visibility levels (including PRIVATE).
    Others' posts: PUBLIC, FOLLOWERS_ONLY, CLOSE_FRIENDS (never PRIVATE).
    """
    blocked_ids = get_blocked_users(user).values_list("pk", flat=True)
    following_qs = Follow.objects.filter(follower=user, status="accepted").values("following_id")

    own_posts = Q(author=user)
    followed_posts = Q(
        author_id__in=following_qs,
        visibility__in=[
            PostVisibility.PUBLIC,
            PostVisibility.FOLLOWERS_ONLY,
            PostVisibility.CLOSE_FRIENDS,
        ],
    )

    return (
        Post.objects.filter(
            (own_posts | followed_posts),
            status=PostStatus.PUBLISHED,
            is_deleted=False,
        )
        .exclude(author_id__in=blocked_ids)
        .select_related("author")
        .prefetch_related("media", "hashtags")
        .order_by("-created_at")
    )


def get_explore_feed(*, user) -> QuerySet:
    """Public posts from users the requester doesn't follow. Excludes own posts and blocked users."""
    blocked_ids = get_blocked_users(user).values_list("pk", flat=True)
    following_qs = Follow.objects.filter(follower=user, status="accepted").values("following_id")

    return (
        Post.objects.filter(
            status=PostStatus.PUBLISHED,
            is_deleted=False,
            visibility=PostVisibility.PUBLIC,
        )
        .exclude(author=user)
        .exclude(author_id__in=following_qs)
        .exclude(author_id__in=blocked_ids)
        .select_related("author")
        .prefetch_related("media", "hashtags")
        .order_by("-created_at")
    )


def get_hashtag_feed(*, user, hashtag_name: str) -> QuerySet:
    """Public published posts with a given hashtag, excluding blocked users."""
    blocked_ids = get_blocked_users(user).values_list("pk", flat=True)

    return (
        Post.objects.filter(
            hashtags__name__iexact=hashtag_name,
            status=PostStatus.PUBLISHED,
            is_deleted=False,
            visibility=PostVisibility.PUBLIC,
        )
        .exclude(author_id__in=blocked_ids)
        .select_related("author")
        .prefetch_related("media", "hashtags")
        .order_by("-created_at")
        .distinct()
    )
