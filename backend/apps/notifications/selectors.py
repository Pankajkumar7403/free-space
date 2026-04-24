from __future__ import annotations

import uuid

from django.db.models import QuerySet

from apps.notifications.exceptions import NotificationNotFoundError
from apps.notifications.models import DeviceToken, Notification, NotificationPreference


def get_notification_by_id(notification_id: uuid.UUID) -> Notification:
    try:
        return Notification.objects.select_related("actor", "recipient").get(
            id=notification_id
        )
    except Notification.DoesNotExist:
        raise NotificationNotFoundError(notification_id)


def get_notifications_for_user(
    user_id: uuid.UUID,
    *,
    include_read: bool = True,
) -> QuerySet[Notification]:
    qs = (
        Notification.objects.filter(recipient_id=user_id)
        .select_related("actor")
        .order_by("-created_at")
    )
    if not include_read:
        qs = qs.filter(is_read=False)
    return qs


def get_unread_notification_count(user_id: uuid.UUID) -> int:
    """Return unread notification count direct from DB."""
    return Notification.objects.filter(recipient_id=user_id, is_read=False).count()


def get_notification_preferences(user_id: uuid.UUID) -> NotificationPreference:
    prefs, _ = NotificationPreference.objects.get_or_create(user_id=user_id)
    return prefs


def get_active_device_tokens(user_id: uuid.UUID) -> QuerySet[DeviceToken]:
    return DeviceToken.objects.filter(user_id=user_id, is_active=True)
