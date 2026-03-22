# 📁 Location: backend/apps/feed/fanout.py

from __future__ import annotations

import logging

from apps.feed.constants import (
    CELEBRITY_FOLLOWER_THRESHOLD,
    FANOUT_BATCH_SIZE,
    FeedSource,
)
from apps.feed.ranking import compute_score, recency_score
from apps.feed.cache import feed_remove_post, feed_delete

logger = logging.getLogger(__name__)


def fanout_post_to_followers(
    *,
    post_id: str,
    author_id: str,
    post_created_at,
    visibility: str,
) -> None:
    """
    Fan-out a newly created post to all followers' Redis feeds.

    Strategy
    --------
    Regular users  (≤ CELEBRITY_FOLLOWER_THRESHOLD followers):
        Fan-out-on-WRITE — push to every follower's feed immediately.
        Celery tasks do the push in batches of FANOUT_BATCH_SIZE.

    Celebrity users (> CELEBRITY_FOLLOWER_THRESHOLD followers):
        Fan-out-on-READ — do NOT push to Redis now.
        When any follower loads their feed, their selector merges
        the celebrity's recent posts in at read time.
        This prevents a single Kanye-style post from writing to
        100 million Redis keys simultaneously.

    Called by
    ---------
    apps.feed.tasks.fanout_post_task  (Celery task)
    Which is triggered by the Kafka post.created consumer.
    """
    from apps.users.models import User

    try:
        author = User.objects.get(pk=author_id)
    except User.DoesNotExist:
        logger.warning("fanout_post_to_followers: author %s not found", author_id)
        return

    follower_count = author.follower_set.filter(status="accepted").count()

    if follower_count > CELEBRITY_FOLLOWER_THRESHOLD:
        logger.info(
            "fanout: celebrity mode for author=%s followers=%d — skipping write fanout",
            author_id, follower_count,
        )
        return

    # ── Regular fan-out-on-write ──────────────────────────────────────────────
    from apps.users.models import Follow
    follower_ids = list(
        Follow.objects.filter(
            following_id=author_id,
            status="accepted",
        ).values_list("follower_id", flat=True)
    )

    logger.info(
        "fanout: writing to %d follower feeds for post=%s",
        len(follower_ids), post_id,
    )

    score = compute_score(post_created_at=post_created_at)

    # Push in batches via Celery to avoid blocking the consumer
    from apps.feed.tasks import push_to_feeds_task  # deferred to break circular import
    for i in range(0, len(follower_ids), FANOUT_BATCH_SIZE):
        batch = [str(uid) for uid in follower_ids[i : i + FANOUT_BATCH_SIZE]]
        push_to_feeds_task.delay(
            post_id=post_id,
            user_ids=batch,
            score=score,
        )


def remove_post_from_feeds(*, post_id: str, author_id: str) -> None:
    """
    Remove a deleted post from all followers' Redis feeds.
    Called when a post is soft-deleted.
    """
    from apps.users.models import Follow

    follower_ids = Follow.objects.filter(
        following_id=author_id,
        status="accepted",
    ).values_list("follower_id", flat=True)

    for uid in follower_ids:
        feed_remove_post(str(uid), post_id)

    logger.info("fanout: removed post=%s from %d feeds", post_id, len(follower_ids))


def invalidate_user_feed(*, user_id: str) -> None:
    """
    Delete a user's entire Redis feed.
    Called when they unfollow someone — their feed is now stale.
    On next load the selector rebuilds it from DB.
    """
    feed_delete(str(user_id))
    logger.info("fanout: invalidated feed for user=%s", user_id)