"""
Three models:

Notification
    Core event record. Uses GenericForeignKey so it can point at any model
    (Post, Comment, etc.) without importing them here — avoids circular deps.

NotificationPreference
    Per-user toggles for in-app / push / email delivery, one row per user.
    Auto-created on first access via get_or_create.

DeviceToken
    FCM registration tokens for iOS / Android / Web push.
    unique_together prevents duplicate token rows.
"""
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from core.database.base_model import BaseModel
from apps.notifications.constants import NotificationType, DevicePlatform


class Notification(BaseModel):
    recipient = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )
    actor = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actor_notifications",
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        db_index=True,
    )

    # ── Generic FK — target object (Post, Comment, …) ────────────────────────
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.UUIDField(null=True, blank=True)
    target = GenericForeignKey("content_type", "object_id")

    # ── Read state ────────────────────────────────────────────────────────────
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # ── Pre-rendered message ──────────────────────────────────────────────────
    # Cached at creation time so we never need to re-join actor.username later.
    message = models.CharField(max_length=255, default="")

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "-created_at"],
                name="notif_recipient_created_idx",
            ),
            models.Index(
                fields=["recipient", "is_read"],
                name="notif_recipient_read_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Notification({self.id}) "
            f"→ {self.recipient_id} [{self.notification_type}]"
        )


class NotificationPreference(BaseModel):
    """
    One row per user.  Created with defaults on first access (get_or_create).
    Defaults are deliberately conservative — only enable push & in-app by default.
    Email is opt-in (False) except for follows, where email is expected.
    """
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )

    # Likes
    likes_in_app = models.BooleanField(default=True)
    likes_push   = models.BooleanField(default=True)
    likes_email  = models.BooleanField(default=False)

    # Comments
    comments_in_app = models.BooleanField(default=True)
    comments_push   = models.BooleanField(default=True)
    comments_email  = models.BooleanField(default=False)

    # Follows
    follows_in_app = models.BooleanField(default=True)
    follows_push   = models.BooleanField(default=True)
    follows_email  = models.BooleanField(default=True)

    # Mentions
    mentions_in_app = models.BooleanField(default=True)
    mentions_push   = models.BooleanField(default=True)
    mentions_email  = models.BooleanField(default=True)

    class Meta:
        db_table = "notification_preferences"

    def __str__(self) -> str:
        return f"NotificationPreference(user={self.user_id})"


class DeviceToken(BaseModel):
    """FCM push registration token per device."""
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="device_tokens",
        db_index=True,
    )
    token    = models.CharField(max_length=512, db_index=True)
    platform = models.CharField(
        max_length=10,
        choices=DevicePlatform.choices,
        default=DevicePlatform.IOS,
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "device_tokens"
        unique_together = [("user", "token")]
        indexes = [
            models.Index(
                fields=["user", "is_active"],
                name="device_token_user_active_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"DeviceToken({self.user_id} / {self.platform})"