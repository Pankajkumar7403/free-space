"""
apps/notifications/dispatchers.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Routes a saved Notification to each enabled delivery channel.

Delivery channels
─────────────────
1. WebSocket (in-app, real-time)  — synchronous async_to_sync call to
                                    channel layer group_send.
2. FCM push notification          — delegated to Celery task (async).
3. Email                          — delegated to Celery task (async).

Each channel is gated by the user's NotificationPreference row.
"""

from __future__ import annotations

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.notifications.constants import NotificationType, get_notification_group
from apps.notifications.models import Notification, NotificationPreference

logger = logging.getLogger(__name__)

# ── Preference field names per notification type ──────────────────────────────
_PREF_MAP: dict[str, tuple[str, str, str]] = {
    str(NotificationType.LIKE_POST): ("likes_in_app", "likes_push", "likes_email"),
    str(NotificationType.LIKE_COMMENT): ("likes_in_app", "likes_push", "likes_email"),
    str(NotificationType.COMMENT): (
        "comments_in_app",
        "comments_push",
        "comments_email",
    ),
    str(NotificationType.COMMENT_REPLY): (
        "comments_in_app",
        "comments_push",
        "comments_email",
    ),
    str(NotificationType.FOLLOW): ("follows_in_app", "follows_push", "follows_email"),
    str(NotificationType.MENTION): (
        "mentions_in_app",
        "mentions_push",
        "mentions_email",
    ),
}

_DEFAULT_PREF = ("likes_in_app", "likes_push", "likes_email")


def dispatch_notification(notification: Notification) -> None:
    """
    Main dispatch entry point.
    Called from services.create_notification() after the DB row is saved.

    1. Load / create NotificationPreference (never raises).
    2. Dispatch WebSocket synchronously.
    3. Dispatch FCM + Email as async Celery tasks.
    """
    prefs = _get_or_create_prefs(notification.recipient_id)
    in_app_field, push_field, email_field = _PREF_MAP.get(
        notification.notification_type, _DEFAULT_PREF
    )

    if getattr(prefs, in_app_field, True):
        _dispatch_websocket(notification)

    if getattr(prefs, push_field, True):
        _dispatch_fcm_push(notification)

    if getattr(prefs, email_field, False):
        _dispatch_email(notification)


# ── Private dispatch helpers ──────────────────────────────────────────────────


def _dispatch_websocket(notification: Notification) -> None:
    """
    Send the notification to the user's open WebSocket connections via the
    channel layer.  Uses async_to_sync so this can be called from sync code
    (Celery worker, management command, view, etc.).
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning("dispatch.websocket.no_channel_layer")
            return

        async_to_sync(channel_layer.group_send)(
            get_notification_group(notification.recipient_id),
            {
                "type": "notification_message",  # maps to consumer method
                "data": _build_ws_payload(notification),
            },
        )
    except Exception as exc:
        # WebSocket dispatch failure must never break the main flow
        logger.error(
            "dispatch.websocket.failed",
            extra={
                "notification_id": str(notification.id),
                "error": str(exc),
            },
        )


def _dispatch_fcm_push(notification: Notification) -> None:
    from apps.notifications.tasks import send_fcm_push_notification

    send_fcm_push_notification.delay(str(notification.id))


def _dispatch_email(notification: Notification) -> None:
    from apps.notifications.tasks import send_email_notification

    send_email_notification.delay(str(notification.id))


def _build_ws_payload(notification: Notification) -> dict:
    """Build the JSON payload sent over the WebSocket to the client."""
    return {
        "type": "notification",
        "id": str(notification.id),
        "notification_type": notification.notification_type,
        "actor_id": str(notification.actor_id) if notification.actor_id else None,
        "actor_username": (notification.actor.username if notification.actor else None),
        "message": notification.message,
        "is_read": notification.is_read,
        "target_id": str(notification.object_id) if notification.object_id else None,
        "created_at": notification.created_at.isoformat(),
    }


def _get_or_create_prefs(user_id) -> NotificationPreference:
    prefs, _ = NotificationPreference.objects.get_or_create(user_id=user_id)
    return prefs
