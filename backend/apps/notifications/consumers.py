"""
apps/notifications/consumers.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
NotificationConsumer — AsyncJsonWebsocketConsumer

Lifecycle
─────────
  connect()      Validate JWT user, join group, send unread count.
  disconnect()   Leave group.
  receive_json() Handle client-initiated actions (mark_read, mark_all_read).
  notification_message()  Channel-layer handler — broadcast to client.

Channel Group
─────────────
  notifications__{user_id}

  The dispatcher calls channel_layer.group_send() on this group whenever
  a new notification is created.  All connected tabs/devices for that
  user receive it simultaneously.
"""

from __future__ import annotations

import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.notifications.constants import get_notification_group

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def connect(self):
        user = self.scope.get("user")

        if not user or user.is_anonymous:
            # 4001 = policy violation / unauthorized
            await self.close(code=4001)
            return

        self.user_id = str(user.id)
        self.user = user
        self.group_name = get_notification_group(user.id)

        # Join per-user channel group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send handshake with current unread count
        unread = await self._get_unread_count()
        await self.send_json(
            {
                "type": "connected",
                "unread_count": unread,
            }
        )
        logger.info(
            "ws.connected",
            extra={"user_id": self.user_id, "channel": self.channel_name},
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(
            "ws.disconnected",
            extra={
                "user_id": getattr(self, "user_id", "unknown"),
                "code": close_code,
            },
        )

    # ── Client → Server messages ──────────────────────────────────────────────

    async def receive_json(self, content, **kwargs):
        """
        Supported client actions:
          {"action": "mark_read",     "notification_id": "<uuid>"}
          {"action": "mark_all_read"}
        """
        action = content.get("action")

        if action == "mark_read":
            notification_id = content.get("notification_id")
            if notification_id:
                updated = await self._mark_read(notification_id)
                if updated:
                    unread = await self._get_unread_count()
                    await self.send_json(
                        {
                            "type": "notification_updated",
                            "notification_id": notification_id,
                            "is_read": True,
                            "unread_count": unread,
                        }
                    )

        elif action == "mark_all_read":
            count = await self._mark_all_read()
            await self.send_json(
                {
                    "type": "all_notifications_read",
                    "marked_count": count,
                    "unread_count": 0,
                }
            )

        elif action == "ping":
            await self.send_json({"type": "pong"})

    # ── Channel Layer → Consumer handlers ────────────────────────────────────

    async def notification_message(self, event):
        """
        Handler called by channel_layer.group_send().
        The 'type' key maps to this method name (dots become underscores).
        """
        await self.send_json(event["data"])

    # ── Private DB helpers ────────────────────────────────────────────────────

    @database_sync_to_async
    def _get_unread_count(self) -> int:
        import uuid

        from apps.notifications.selectors import get_unread_notification_count

        return get_unread_notification_count(uuid.UUID(self.user_id))

    @database_sync_to_async
    def _mark_read(self, notification_id_str: str) -> bool:
        import uuid

        from apps.notifications.exceptions import (
            NotificationNotFoundError,
            UnauthorizedNotificationError,
        )
        from apps.notifications.services import mark_notification_read

        try:
            mark_notification_read(
                notification_id=uuid.UUID(notification_id_str),
                user_id=uuid.UUID(self.user_id),
            )
            return True
        except (NotificationNotFoundError, UnauthorizedNotificationError, ValueError):
            return False

    @database_sync_to_async
    def _mark_all_read(self) -> int:
        import uuid

        from apps.notifications.services import mark_all_notifications_read

        return mark_all_notifications_read(user_id=uuid.UUID(self.user_id))
