"""
All notification-domain constants, enums, and Redis key patterns.
Single source of truth - import from here everywhere.
"""

from django.db import models


class NotificationType(models.TextChoices):
    LIKE_POST = "like_post", "Liked your post"
    LIKE_COMMENT = "like_comment", "Liked your comment"
    COMMENT = "comment", "Commented on your post"
    COMMENT_REPLY = "comment_reply", "Replied to your comment"
    FOLLOW = "follow", "Started following you"
    MENTION = "mention", "Mentioned you"


class DevicePlatform(models.TextChoices):
    IOS = "ios", "iOS"
    ANDROID = "android", "Android"
    WEB = "web", "Web (PWA)"


# -- WebSocket channel groups --------------------------------------------------
NOTIFICATION_GROUP_PREFIX = "notifications__"


def get_notification_group(user_id) -> str:
    """Return the channel group name for a user's notification stream."""
    return f"{NOTIFICATION_GROUP_PREFIX}{user_id}"


# -- Redis keys ----------------------------------------------------------------
UNREAD_COUNT_REDIS_KEY = "notifications:unread:{user_id}"
UNREAD_COUNT_TTL_SECONDS = 3_600  # 1 hour

# -- Kafka consumer ------------------------------------------------------------
NOTIFICATION_CONSUMER_GROUP_ID = "notification-consumer-group"
NOTIFICATION_CONSUMER_POLL_TIMEOUT = 1.0  # seconds
NOTIFICATION_CONSUMER_TOPICS = [
    "like.created",
    "like.removed",
    "comment.created",
    "user.followed",
]

# -- Pagination ----------------------------------------------------------------
NOTIFICATIONS_PAGE_SIZE = 20
