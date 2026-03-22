# 📁 Location: backend/apps/feed/services.py

from __future__ import annotations

import logging

from django.db import transaction

from apps.feed.cache import explore_push
from apps.feed.constants import FeedSource
from apps.feed.models import FeedItem, HashtagSubscription
from apps.feed.ranking import recency_score
from apps.posts.models import Hashtag, Post
from apps.users.models import User
from apps.users.selectors import get_user_by_id

logger = logging.getLogger(__name__)


@transaction.atomic
def subscribe_to_hashtag(*, user_id, hashtag_name: str) -> HashtagSubscription:
    """
    Subscribe a user to a hashtag so their feed includes posts with that tag.
    """
    user    = get_user_by_id(user_id)
    hashtag, _ = Hashtag.objects.get_or_create(name=hashtag_name.lower())
    sub, _  = HashtagSubscription.objects.get_or_create(user=user, hashtag=hashtag)
    return sub


@transaction.atomic
def unsubscribe_from_hashtag(*, user_id, hashtag_name: str) -> None:
    """Unsubscribe from a hashtag."""
    user = get_user_by_id(user_id)
    HashtagSubscription.objects.filter(
        user=user, hashtag__name=hashtag_name.lower()
    ).delete()


def push_post_to_explore(*, post: Post) -> None:
    """
    Add a public post to the global explore feed with a recency score.
    Called after post creation if visibility=PUBLIC.
    """
    if post.visibility != "public":
        return
    score = recency_score(post.created_at)
    explore_push(str(post.id), score)
    logger.debug("push_post_to_explore: post=%s score=%s", post.id, score)


def on_user_login(*, user_id: str) -> None:
    """
    Hook called when a user logs in.
    Triggers feed warm-up if their Redis feed is cold.
    """
    from apps.feed.cache import is_feed_warm
    from apps.feed.tasks import warm_user_feed_task

    if not is_feed_warm(user_id):
        warm_user_feed_task.delay(user_id=user_id)
        logger.debug("on_user_login: triggered feed warm-up for user=%s", user_id)


def on_user_unfollow(*, follower_id: str) -> None:
    """
    Hook called when a user unfollows someone.
    Invalidates their Redis feed so stale posts are removed.
    """
    from apps.feed.fanout import invalidate_user_feed
    invalidate_user_feed(user_id=follower_id)