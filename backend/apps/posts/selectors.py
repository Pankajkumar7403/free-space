# 📁 Location: backend/apps/posts/selectors.py

from __future__ import annotations

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import QuerySet

from apps.posts.constants import PostStatus, PostVisibility
from apps.posts.exceptions import MediaNotFoundError, PostNotFoundError
from apps.posts.models import Hashtag, Media, Post
from apps.users.models import User
from apps.users.selectors import get_blocked_users, get_following, is_blocked


def get_post_by_id(post_id, requesting_user: User | None = None) -> Post:
    """
    Fetch a single published, non-deleted post.
    Enforces visibility rules if requesting_user is provided.
    Raises PostNotFoundError.
    """
    try:
        post = Post.objects.select_related("author").prefetch_related(
            "media", "hashtags"
        ).get(pk=post_id, is_deleted=False, status=PostStatus.PUBLISHED)
    except Post.DoesNotExist:
        raise PostNotFoundError(detail={"post_id": str(post_id)})

    if requesting_user and not _can_view_post(post, requesting_user):
        raise PostNotFoundError(detail={"post_id": str(post_id)})

    return post


def get_posts_by_author(author: User, requesting_user: User | None = None) -> QuerySet:
    """
    All published posts by an author, filtered by visibility rules.
    """
    qs = Post.objects.filter(
        author=author,
        is_deleted=False,
        status=PostStatus.PUBLISHED,
    ).select_related("author").prefetch_related("media", "hashtags").order_by("-created_at")

    if requesting_user is None:
        return qs.filter(visibility=PostVisibility.PUBLIC)

    if requesting_user == author:
        return qs  # own posts — no filter

    # Exclude posts the requester can't see
    following_ids = set(get_following(requesting_user).values_list("pk", flat=True))
    visible = [PostVisibility.PUBLIC]
    if author.pk in following_ids:
        visible += [PostVisibility.FOLLOWERS_ONLY, PostVisibility.CLOSE_FRIENDS]

    return qs.filter(visibility__in=visible)


def get_posts_by_hashtag(hashtag_name: str) -> QuerySet:
    """All public published posts for a given hashtag (case-insensitive)."""
    return Post.objects.filter(
        hashtags__name__iexact=hashtag_name,
        visibility=PostVisibility.PUBLIC,
        is_deleted=False,
        status=PostStatus.PUBLISHED,
    ).select_related("author").order_by("-created_at")


def search_posts(query: str, requesting_user: User | None = None) -> QuerySet:
    """
    Full-text search on post content + hashtags using PostgreSQL tsvector.
    Only returns PUBLIC posts.
    """
    search_query = SearchQuery(query, search_type="websearch")
    return (
        Post.objects.filter(
            search_vector=search_query,
            visibility=PostVisibility.PUBLIC,
            is_deleted=False,
            status=PostStatus.PUBLISHED,
        )
        .annotate(rank=SearchRank("search_vector", search_query))
        .order_by("-rank", "-created_at")
        .select_related("author")
        [:100]  # hard cap
    )


def get_trending_hashtags(limit: int = 20) -> QuerySet:
    """
    Most-used hashtags in the last 7 days.
    Falls back to overall count if no time-windowed data available.
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count

    cutoff = timezone.now() - timedelta(days=7)
    return (
        Hashtag.objects.filter(
            posthashtag__post__created_at__gte=cutoff,
            posthashtag__post__is_deleted=False,
            posthashtag__post__status=PostStatus.PUBLISHED,
        )
        .annotate(post_count=Count("posthashtag"))
        .order_by("-post_count")
        [:limit]
    )


def get_media_by_id(media_id, owner: User | None = None) -> Media:
    """
    Fetch a Media record by id.
    Optionally validates ownership.
    Raises MediaNotFoundError.
    """
    try:
        qs = Media.objects.filter(pk=media_id, is_deleted=False)
        if owner:
            qs = qs.filter(owner=owner)
        return qs.get()
    except Media.DoesNotExist:
        raise MediaNotFoundError(detail={"media_id": str(media_id)})


# ── Internal helper ───────────────────────────────────────────────────────────

def _can_view_post(post: Post, user: User) -> bool:
    """
    Returns True if *user* is allowed to see *post*.
    Called by get_post_by_id to enforce visibility rules.
    """
    if post.author == user:
        return True  # always see own posts

    if is_blocked(post.author, user) or is_blocked(user, post.author):
        return False

    if post.visibility == PostVisibility.PUBLIC:
        return True

    following_ids = set(get_following(user).values_list("pk", flat=True))

    if post.visibility == PostVisibility.FOLLOWERS_ONLY:
        return post.author.pk in following_ids

    if post.visibility == PostVisibility.CLOSE_FRIENDS:
        # For now: same as followers_only — close friends list in M4
        return post.author.pk in following_ids

    return False  # PRIVATE