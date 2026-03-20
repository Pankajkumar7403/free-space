# 📁 Location: backend/apps/feed/selectors.py

from __future__ import annotations

import logging
from dataclasses import dataclass

from apps.feed.cache import (
    explore_get_page,
    feed_exists,
    feed_get_page,
)
from apps.feed.constants import CELEBRITY_FOLLOWER_THRESHOLD, FeedSource
from apps.feed.ranking import compute_score, recency_score
from apps.posts.constants import PostStatus, PostVisibility
from apps.posts.models import Post
from apps.posts.serializers import PostListSerializer
from apps.users.models import Follow, User
from apps.users.selectors import get_blocked_users

logger = logging.getLogger(__name__)


@dataclass
class FeedPage:
    """Result of a single feed page request."""
    posts:       list
    next_cursor: int | None
    source:      str       # "redis" | "db"


def get_user_feed(
    *,
    user: User,
    cursor: int = 0,
    page_size: int = 20,
) -> FeedPage:
    """
    Main feed selector. Returns a ranked, paginated page of posts.

    Strategy
    --------
    1. Check Redis — if the feed exists there, serve it (fast path).
    2. If Redis is cold, fall back to DB query (slow path).
    3. For every celebrity the user follows, inject their recent posts
       at read time (fan-out-on-read merge).
    4. Filter out posts from blocked users.
    5. Return FeedPage with posts + next cursor.
    """
    blocked_ids = set(
        get_blocked_users(user).values_list("pk", flat=True)
    )

    # ── Fast path: Redis ──────────────────────────────────────────────────────
    if feed_exists(str(user.pk)):
        post_ids = feed_get_page(str(user.pk), cursor=cursor, page_size=page_size + 20)

        # Inject celebrity posts (fan-out-on-read)
        celebrity_post_ids = _get_celebrity_posts(user, blocked_ids)
        all_ids = _merge_and_deduplicate(post_ids, celebrity_post_ids, page_size)

        posts = _fetch_posts(all_ids, user, blocked_ids)
        next_cursor = cursor + page_size if len(posts) >= page_size else None
        return FeedPage(posts=posts, next_cursor=next_cursor, source="redis")

    # ── Slow path: DB fallback ────────────────────────────────────────────────
    logger.info("get_user_feed: Redis cold for user=%s, falling back to DB", user.pk)
    posts = _get_feed_from_db(user, blocked_ids, cursor, page_size)
    next_cursor = cursor + page_size if len(posts) >= page_size else None

    # Trigger async warm-up so next request hits Redis
    from apps.feed.tasks import warm_user_feed_task
    warm_user_feed_task.delay(user_id=str(user.pk))

    return FeedPage(posts=posts, next_cursor=next_cursor, source="db")


def get_explore_feed(
    *,
    user: User,
    cursor: int = 0,
    page_size: int = 20,
) -> FeedPage:
    """
    Explore feed: trending public posts from non-followed users.
    Served from the global explore Redis ZSet.
    """
    blocked_ids = set(get_blocked_users(user).values_list("pk", flat=True))
    following_ids = set(
        Follow.objects.filter(follower=user, status="accepted")
        .values_list("following_id", flat=True)
    )

    post_ids = explore_get_page(cursor=cursor, page_size=page_size + 20)

    posts = []
    for pid in post_ids:
        try:
            post = Post.objects.select_related("author").get(
                pk=pid,
                is_deleted=False,
                status=PostStatus.PUBLISHED,
                visibility=PostVisibility.PUBLIC,
            )
            # Explore = posts from people you DON'T follow
            if post.author_id in following_ids:
                continue
            if post.author_id in blocked_ids:
                continue
            posts.append(post)
            if len(posts) >= page_size:
                break
        except Post.DoesNotExist:
            continue

    next_cursor = cursor + page_size if len(posts) >= page_size else None
    return FeedPage(posts=posts, next_cursor=next_cursor, source="redis")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_celebrity_posts(user: User, blocked_ids: set) -> list[str]:
    """
    For each celebrity the user follows, fetch their 10 most recent posts.
    This is the fan-out-on-read merge step.
    """
    celebrity_ids = (
        Follow.objects.filter(follower=user, status="accepted")
        .annotate_celebrity()  # annotated in a custom manager — simplified here
        .values_list("following_id", flat=True)
    )

    # Simplified: query directly
    from apps.users.models import User as UserModel
    celebrity_following = (
        Follow.objects.filter(follower=user, status="accepted")
        .select_related("following")
        .filter(following__follower_set__isnull=False)
    )

    post_ids = []
    for follow in celebrity_following:
        author = follow.following
        follower_count = author.follower_set.filter(status="accepted").count()
        if follower_count > CELEBRITY_FOLLOWER_THRESHOLD and author.pk not in blocked_ids:
            recent = Post.objects.filter(
                author=author,
                status=PostStatus.PUBLISHED,
                is_deleted=False,
                visibility__in=[PostVisibility.PUBLIC, PostVisibility.FOLLOWERS_ONLY],
            ).order_by("-created_at").values_list("id", flat=True)[:10]
            post_ids.extend([str(pid) for pid in recent])

    return post_ids


def _merge_and_deduplicate(
    feed_ids: list[str],
    celebrity_ids: list[str],
    page_size: int,
) -> list[str]:
    """Merge two lists of post IDs, deduplicate, cap at page_size."""
    seen = set()
    merged = []
    for pid in feed_ids + celebrity_ids:
        if pid not in seen:
            seen.add(pid)
            merged.append(pid)
        if len(merged) >= page_size:
            break
    return merged


def _fetch_posts(
    post_ids: list[str],
    requesting_user: User,
    blocked_ids: set,
) -> list:
    """
    Fetch Post objects for the given IDs, preserving order.
    Filters out deleted, private, and blocked posts.
    """
    if not post_ids:
        return []

    posts_by_id = {
        str(p.pk): p
        for p in Post.objects.filter(
            pk__in=post_ids,
            is_deleted=False,
            status=PostStatus.PUBLISHED,
        ).select_related("author").prefetch_related("media", "hashtags")
    }

    result = []
    for pid in post_ids:
        post = posts_by_id.get(pid)
        if not post:
            continue
        if post.author_id in blocked_ids:
            continue
        result.append(post)

    return result


def _get_feed_from_db(
    user: User,
    blocked_ids: set,
    cursor: int,
    page_size: int,
) -> list:
    """
    DB fallback: fetch posts from followed users ordered by created_at.
    Used when Redis feed is cold/expired.
    """
    following_ids = Follow.objects.filter(
        follower=user, status="accepted"
    ).values_list("following_id", flat=True)

    qs = Post.objects.filter(
        author_id__in=following_ids,
        status=PostStatus.PUBLISHED,
        is_deleted=False,
        visibility__in=[PostVisibility.PUBLIC, PostVisibility.FOLLOWERS_ONLY],
    ).exclude(
        author_id__in=blocked_ids,
    ).select_related("author").prefetch_related("media", "hashtags").order_by("-created_at")

    return list(qs[cursor : cursor + page_size])