"""
apps/notifications/events.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Kafka event handlers for the notification consumer.

Each handler receives a parsed dict from the Kafka message value and calls
notification services.  All handlers are sync and safe to call from the
management command's polling loop.

Kafka Topics consumed
─────────────────────
  like.created        → LIKE_POST notification for post author
  like.removed        → Delete the matching LIKE_POST notification
  comment.created     → COMMENT / COMMENT_REPLY notifications
  user.followed       → FOLLOW notification for the followed user
"""
from __future__ import annotations

import json
import logging
import uuid

from apps.notifications.constants import NotificationType
from apps.notifications.services import create_notification

logger = logging.getLogger(__name__)

# ── Public entry point ────────────────────────────────────────────────────────

def handle_kafka_event(topic: str, value: bytes | str) -> None:
    """
    Called by the management command for every Kafka message.
    Parses JSON, dispatches to the correct handler.
    """
    try:
        data = json.loads(value) if isinstance(value, (bytes, str)) else value
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error(
            "kafka.notification.parse_failed",
            extra={"topic": topic, "error": str(exc)},
        )
        return

    _HANDLERS = {
        "like.created":  _handle_like_created,
        "like.removed":  _handle_like_removed,
        "comment.created": _handle_comment_created,
        "user.followed": _handle_user_followed,
    }

    handler = _HANDLERS.get(topic)
    if not handler:
        logger.debug("kafka.notification.no_handler", extra={"topic": topic})
        return

    try:
        handler(data)
    except Exception as exc:
        logger.error(
            "kafka.notification.handler_failed",
            extra={"topic": topic, "error": str(exc), "data": data},
        )


# ── Private handlers ──────────────────────────────────────────────────────────

def _handle_like_created(data: dict) -> None:
    """
    Expected payload (from apps.likes.events):
        {liker_id, post_id, post_author_id, comment_id?, comment_author_id?}
    """
    liker_id        = data.get("liker_id")
    post_author_id  = data.get("post_author_id")
    post_id         = data.get("post_id")

    if not all([liker_id, post_author_id, post_id]):
        logger.warning("_handle_like_created.missing_fields", extra={"data": data})
        return

    # Skip self-likes
    if liker_id == post_author_id:
        return

    create_notification(
        recipient_id=uuid.UUID(post_author_id),
        actor_id=uuid.UUID(liker_id),
        notification_type=NotificationType.LIKE_POST,
        target_id=uuid.UUID(post_id),
        target_content_type_label="posts.Post",
    )


def _handle_like_removed(data: dict) -> None:
    """Remove the like notification when a post is unliked."""
    from apps.notifications.models import Notification

    liker_id = data.get("liker_id")
    post_id  = data.get("post_id")

    if not all([liker_id, post_id]):
        return

    Notification.objects.filter(
        actor_id=liker_id,
        notification_type=NotificationType.LIKE_POST,
        object_id=post_id,
    ).delete()


def _handle_comment_created(data: dict) -> None:
    """
    Expected payload:
        {
          comment_id, commenter_id,
          post_id, post_author_id,
          parent_comment_id?,       ← present only for replies
          parent_comment_author_id? ← present only for replies
        }
    """
    commenter_id   = data.get("commenter_id")
    post_author_id = data.get("post_author_id")
    comment_id     = data.get("comment_id")
    parent_comment_author_id = data.get("parent_comment_author_id")

    if not all([commenter_id, post_author_id, comment_id]):
        return

    # Notify post author about new comment (not if they're the commenter)
    if commenter_id != post_author_id:
        create_notification(
            recipient_id=uuid.UUID(post_author_id),
            actor_id=uuid.UUID(commenter_id),
            notification_type=NotificationType.COMMENT,
            target_id=uuid.UUID(comment_id),
            target_content_type_label="comments.Comment",
        )

    # Notify parent comment author about a reply
    if (
        parent_comment_author_id
        and parent_comment_author_id != commenter_id
        and parent_comment_author_id != post_author_id   # avoid double-notify
    ):
        create_notification(
            recipient_id=uuid.UUID(parent_comment_author_id),
            actor_id=uuid.UUID(commenter_id),
            notification_type=NotificationType.COMMENT_REPLY,
            target_id=uuid.UUID(comment_id),
            target_content_type_label="comments.Comment",
        )


def _handle_user_followed(data: dict) -> None:
    """
    Expected payload (from apps.users.events):
        {follower_id, following_id}
    """
    follower_id  = data.get("follower_id")
    following_id = data.get("following_id")

    if not all([follower_id, following_id]):
        return

    create_notification(
        recipient_id=uuid.UUID(following_id),
        actor_id=uuid.UUID(follower_id),
        notification_type=NotificationType.FOLLOW,
        target_id=None,
        target_content_type_label=None,
    )