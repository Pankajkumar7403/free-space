# 📁 Location: backend/apps/feed/tasks.py

from __future__ import annotations

import logging

from celery import shared_task

from apps.feed.cache import feed_push_post, feed_push_batch, is_feed_warm, mark_feed_warm
from apps.feed.ranking import compute_score
from apps.posts.models import Post
from apps.posts.constants import PostStatus, PostVisibility
from apps.users.models import Follow
from apps.feed.fanout import fanout_post_to_followers

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="feed.push_to_feeds",
)
def push_to_feeds_task(
    self,
    *,
    post_id: str,
    user_ids: list[str],
    score: float,
) -> None:
    """
    Celery task: push a single post into a batch of users' Redis feeds.

    Called by fanout_post_to_followers() in batches of FANOUT_BATCH_SIZE.
    Each task handles one batch — failures retry independently.
    """
    for user_id in user_ids:
        try:
            feed_push_post(user_id, post_id, score)
        except Exception as exc:
            logger.exception(
                "push_to_feeds_task: failed for user=%s post=%s",
                user_id, post_id,
            )
            raise self.retry(exc=exc)

    logger.debug(
        "push_to_feeds_task: pushed post=%s to %d feeds",
        post_id, len(user_ids),
    )


@shared_task(
    bind=True,
    max_retries=2,
    name="feed.warm_user_feed",
)
def warm_user_feed_task(self, *, user_id: str) -> None:
    """
    Celery task: warm up a user's feed from DB on first login.

    Triggered when a user logs in and their Redis feed is cold (expired).
    Fetches recent posts from followed users and pushes them to Redis.
    """
    if is_feed_warm(user_id):
        logger.debug("warm_user_feed_task: feed already warm for user=%s", user_id)
        return

    # Get the IDs of users this person follows
    following_ids = Follow.objects.filter(
        follower_id=user_id,
        status="accepted",
    ).values_list("following_id", flat=True)

    # Fetch their 50 most recent posts
    recent_posts = Post.objects.filter(
        author_id__in=following_ids,
        status=PostStatus.PUBLISHED,
        is_deleted=False,
        visibility__in=[PostVisibility.PUBLIC, PostVisibility.FOLLOWERS_ONLY],
    ).order_by("-created_at")[:50]

    post_scores: dict[str, float] = {}
    for post in recent_posts:
        score = compute_score(post_created_at=post.created_at)
        post_scores[str(post.id)] = score

    if post_scores:
        feed_push_batch(user_id, post_scores)

    mark_feed_warm(user_id)
    logger.info(
        "warm_user_feed_task: warmed feed for user=%s with %d posts",
        user_id, len(post_scores),
    )


@shared_task(name="feed.fanout_post")
def fanout_post_task(
    *,
    post_id: str,
    author_id: str,
    post_created_at: str,
    visibility: str,
) -> None:
    """
    Celery task: entry point for post fanout.
    Parses the created_at string and delegates to fanout_post_to_followers().
    Called from the Kafka consumer.
    """
    from datetime import datetime, timezone

    created_at = datetime.fromisoformat(post_created_at)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    fanout_post_to_followers(
        post_id=post_id,
        author_id=author_id,
        post_created_at=created_at,
        visibility=visibility,
    )