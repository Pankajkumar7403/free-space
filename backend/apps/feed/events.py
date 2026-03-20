# 📁 Location: backend/apps/feed/events.py

from __future__ import annotations

import logging

from core.kafka.consumer import BaseKafkaConsumer
from core.kafka.topics import Topics

logger = logging.getLogger(__name__)


class FeedKafkaConsumer(BaseKafkaConsumer):
    """
    Kafka consumer that drives feed updates.

    Listens to
    ----------
    post.created   → trigger fan-out to follower feeds
    post.deleted   → remove post from all follower feeds
    user.followed  → warm-up new follower's feed

    Run this as a long-running process:
        python manage.py run_feed_consumer
    """

    topics = [
        Topics.POST_CREATED,
        Topics.POST_DELETED,
        Topics.USER_FOLLOWED,
    ]

    def handle_message(self, topic: str, event_data: dict) -> None:
        if topic == Topics.POST_CREATED:
            self._handle_post_created(event_data)
        elif topic == Topics.POST_DELETED:
            self._handle_post_deleted(event_data)
        elif topic == Topics.USER_FOLLOWED:
            self._handle_user_followed(event_data)
        else:
            logger.warning("FeedKafkaConsumer: unknown topic %s", topic)

    def _handle_post_created(self, data: dict) -> None:
        from apps.feed.tasks import fanout_post_task
        fanout_post_task.delay(
            post_id=data["post_id"],
            author_id=data["author_id"],
            post_created_at=data["timestamp"],
            visibility=data.get("visibility", "followers_only"),
        )
        logger.debug("FeedKafkaConsumer: queued fanout for post=%s", data["post_id"])

    def _handle_post_deleted(self, data: dict) -> None:
        from apps.feed.fanout import remove_post_from_feeds
        remove_post_from_feeds(
            post_id=data["post_id"],
            author_id=data["author_id"],
        )

    def _handle_user_followed(self, data: dict) -> None:
        from apps.feed.tasks import warm_user_feed_task
        # When someone follows a new person, warm their feed
        warm_user_feed_task.delay(user_id=data.get("follower_id", ""))