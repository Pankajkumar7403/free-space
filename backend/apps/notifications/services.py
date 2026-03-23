"""
apps/notifications/services.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
All notification mutations.
Views and Kafka handlers call these services — never the models directly.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.notifications.constants import NotificationType
from apps.notifications.exceptions import (
    NotificationNotFoundError,
    UnauthorizedNotificationError,
)
from apps.notifications.models import (
    DeviceToken,
    Notification,
    NotificationPreference,
)
from apps.notifications.selectors import get_notification_by_id

logger = logging.getLogger(__name__)

# ── Message templates (rendered at creation so no join needed at read time) ──

_TEMPLATES: dict[str, str] = {
    NotificationType.LIKE_POST:     "{actor} liked your post",
    NotificationType.LIKE_COMMENT:  "{actor} liked your comment",
    NotificationType.COMMENT:       "{actor} commented on your post",
    NotificationType.COMMENT_REPLY: "{actor} replied to your comment",
    NotificationType.FOLLOW:        "{actor} started following you",
    NotificationType.MENTION:       "{actor} mentioned you",
}

# Maps target_content_type_label → (app_label, model)
_CONTENT_TYPE_MAP: dict[str, tuple[str, str]] = {
    "posts.Post":       ("posts",    "post"),
    "comments.Comment": ("comments", "comment"),
}


def create_notification(
    *,
    recipient_id: uuid.UUID,
    actor_id: Optional[uuid.UUID],
    notification_type: str,
    target_id: Optional[uuid.UUID] = None,
    target_content_type_label: Optional[str] = None,
) -> Optional[Notification]:
    """
    Create and dispatch a notification.

    Steps
    -----
    1. Resolve actor username for the message text.
    2. Resolve ContentType for target_content_type_label (if provided).
    3. Persist Notification row.
    4. dispatch_notification() → WebSocket (sync) + FCM/Email (Celery tasks).
    5. Invalidate Redis unread count cache.

    Returns None if any required field is missing or the actor == recipient.
    """
    # Never notify users about their own actions
    if actor_id and str(actor_id) == str(recipient_id):
        return None

    from apps.notifications.dispatchers import dispatch_notification

    actor_username = _resolve_actor_username(actor_id)
    message = _TEMPLATES.get(
        notification_type, "You have a new notification"
    ).format(actor=actor_username or "Someone")

    content_type = None
    if target_content_type_label and target_content_type_label in _CONTENT_TYPE_MAP:
        from django.contrib.contenttypes.models import ContentType
        app_label, model = _CONTENT_TYPE_MAP[target_content_type_label]
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            pass

    with transaction.atomic():
        notification = Notification.objects.create(
            recipient_id=recipient_id,
            actor_id=actor_id,
            notification_type=notification_type,
            content_type=content_type,
            object_id=target_id,
            message=message,
        )
        # Invalidate cached count after commit
        transaction.on_commit(lambda: _invalidate_unread_cache(recipient_id))

    dispatch_notification(notification)

    logger.info(
        "notification.created",
        extra={
            "notification_id": str(notification.id),
            "recipient_id":    str(recipient_id),
            "type":            notification_type,
        },
    )
    return notification


def mark_notification_read(
    *, notification_id: uuid.UUID, user_id: uuid.UUID
) -> Notification:
    notification = get_notification_by_id(notification_id)

    if notification.recipient_id != user_id:
        raise UnauthorizedNotificationError()

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
        _invalidate_unread_cache(user_id)

    return notification


def mark_all_notifications_read(*, user_id: uuid.UUID) -> int:
    """Mark all unread as read. Returns count of updated rows."""
    count = Notification.objects.filter(
        recipient_id=user_id,
        is_read=False,
    ).update(is_read=True, read_at=timezone.now())

    if count > 0:
        _invalidate_unread_cache(user_id)

    return count


def delete_notification(
    *, notification_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    notification = get_notification_by_id(notification_id)
    if notification.recipient_id != user_id:
        raise UnauthorizedNotificationError()
    notification.delete()


def register_device_token(
    *, user_id: uuid.UUID, token: str, platform: str
) -> DeviceToken:
    """Upsert a device token — idempotent on (user, token)."""
    device_token, _ = DeviceToken.objects.update_or_create(
        user_id=user_id,
        token=token,
        defaults={"platform": platform, "is_active": True},
    )
    return device_token


def deregister_device_token(*, user_id: uuid.UUID, token: str) -> None:
    DeviceToken.objects.filter(user_id=user_id, token=token).update(is_active=False)


def update_notification_preferences(
    *, user_id: uuid.UUID, preferences: dict
) -> NotificationPreference:
    """Patch the user's preference row with only the provided keys."""
    prefs, _ = NotificationPreference.objects.get_or_create(user_id=user_id)

    # Whitelist — only boolean preference fields accepted
    allowed = {
        f.name
        for f in NotificationPreference._meta.get_fields()
        if f.name not in ("id", "user", "created_at", "updated_at", "deleted_at")
        and hasattr(f, "default")
    }

    updated_fields = []
    for key, value in preferences.items():
        if key in allowed and isinstance(value, bool):
            setattr(prefs, key, value)
            updated_fields.append(key)

    if updated_fields:
        prefs.save(update_fields=updated_fields)

    return prefs


# ── Private helpers ───────────────────────────────────────────────────────────

def _resolve_actor_username(actor_id: Optional[uuid.UUID]) -> Optional[str]:
    if not actor_id:
        return None
    try:
        from apps.users.models import User
        return User.objects.only("username").get(id=actor_id).username
    except Exception:
        return None


def _invalidate_unread_cache(user_id: uuid.UUID) -> None:
    from core.redis.client import RedisClient
    from apps.notifications.constants import UNREAD_COUNT_REDIS_KEY
    try:
        RedisClient.get_instance().delete(
            UNREAD_COUNT_REDIS_KEY.format(user_id=user_id)
        )
    except Exception as exc:
        logger.warning(
            "notification.cache_invalidation_failed",
            extra={"user_id": str(user_id), "error": str(exc)},
        )