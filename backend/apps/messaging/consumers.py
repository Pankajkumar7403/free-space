"""
MessageConsumer — AsyncJsonWebsocketConsumer

WebSocket URL:
    ws://api.qommunity.app/ws/messages/<conversation_id>/?token=<jwt>
"""

from __future__ import annotations

import logging
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.messaging.constants import TYPING_KEY, TYPING_TTL_SECONDS, get_conversation_group

logger = logging.getLogger(__name__)


class MessageConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        if not user or user.is_anonymous:
            await self.close(code=4001)
            return

        self.user_id = str(user.id)
        self.user = user
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = get_conversation_group(self.conversation_id)

        is_participant = await self._verify_participant()
        if not is_participant:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self._mark_all_read()

        await self.send_json(
            {
                "type": "connected",
                "conversation_id": self.conversation_id,
            }
        )

        logger.info(
            "ws.messages.connected",
            extra={"user_id": self.user_id, "conversation_id": self.conversation_id},
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self._clear_typing()
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(
            "ws.messages.disconnected",
            extra={"user_id": getattr(self, "user_id", "unknown"), "code": close_code},
        )

    async def receive_json(self, content, **kwargs):
        action = content.get("action")

        handlers = {
            "send_message": self._handle_send_message,
            "delete_message": self._handle_delete_message,
            "typing_start": self._handle_typing_start,
            "typing_stop": self._handle_typing_stop,
            "mark_read": self._handle_mark_read,
            "ping": self._handle_ping,
        }

        handler = handlers.get(action)
        if handler:
            await handler(content)
            return

        await self.send_json({"type": "error", "message": f"Unknown action: {action}"})

    async def _handle_send_message(self, content: dict):
        text = (content.get("content") or "").strip()
        reply_to_id = content.get("reply_to_id")

        if not text:
            await self.send_json({"type": "error", "message": "Message content is required."})
            return

        message = await self._create_message(text, reply_to_id)
        if not message:
            return

        payload = await self._build_message_payload(message)

        await self.channel_layer.group_send(self.group_name, {"type": "message_new", "data": payload})
        await self._clear_typing()

    async def _handle_delete_message(self, content: dict):
        message_id = content.get("message_id")
        if not message_id:
            return

        success = await self._delete_message(message_id)
        if success:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "message_deleted",
                    "data": {
                        "type": "message_deleted",
                        "message_id": message_id,
                        "deleted_by": self.user_id,
                    },
                },
            )

    async def _handle_typing_start(self, content: dict):
        await self._set_typing(True)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_event",
                "data": {
                    "type": "typing",
                    "user_id": self.user_id,
                    "username": await self._get_username(),
                    "is_typing": True,
                    "conversation_id": self.conversation_id,
                },
            },
        )

    async def _handle_typing_stop(self, content: dict):
        await self._clear_typing()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_event",
                "data": {
                    "type": "typing",
                    "user_id": self.user_id,
                    "is_typing": False,
                    "conversation_id": self.conversation_id,
                },
            },
        )

    async def _handle_mark_read(self, content: dict):
        count = await self._mark_all_read()
        await self.send_json(
            {
                "type": "all_messages_read",
                "conversation_id": self.conversation_id,
                "marked_count": count,
            }
        )

    async def _handle_ping(self, content: dict):
        await self.send_json({"type": "pong"})

    async def message_new(self, event):
        await self.send_json(event["data"])

    async def message_deleted(self, event):
        await self.send_json(event["data"])

    async def message_reaction(self, event):
        await self.send_json(event["data"])

    async def typing_event(self, event):
        data = event["data"]
        if data.get("user_id") != self.user_id:
            await self.send_json(data)

    @database_sync_to_async
    def _verify_participant(self) -> bool:
        from apps.messaging.models import ConversationParticipant

        return ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
        ).exists()

    @database_sync_to_async
    def _create_message(self, content: str, reply_to_id=None):
        from apps.messaging.exceptions import NotAParticipantError
        from apps.messaging.services import send_message

        try:
            return send_message(
                conversation_id=uuid.UUID(self.conversation_id),
                sender_id=uuid.UUID(self.user_id),
                content=content,
                reply_to_id=uuid.UUID(reply_to_id) if reply_to_id else None,
            )
        except (NotAParticipantError, ValueError) as exc:
            logger.warning("ws.send_message.failed", extra={"error": str(exc)})
            return None

    @database_sync_to_async
    def _delete_message(self, message_id_str: str) -> bool:
        from apps.messaging.exceptions import MessageDeleteForbiddenError, MessageNotFoundError
        from apps.messaging.services import delete_message

        try:
            delete_message(message_id=uuid.UUID(message_id_str), user_id=uuid.UUID(self.user_id))
            return True
        except (MessageDeleteForbiddenError, MessageNotFoundError, ValueError):
            return False

    @database_sync_to_async
    def _mark_all_read(self) -> int:
        from apps.messaging.services import mark_conversation_read

        return mark_conversation_read(
            conversation_id=uuid.UUID(self.conversation_id),
            user_id=uuid.UUID(self.user_id),
        )

    @database_sync_to_async
    def _build_message_payload(self, message) -> dict:
        from apps.messaging.serializers import MessageSerializer

        return MessageSerializer(message).data

    @database_sync_to_async
    def _get_username(self) -> str:
        return getattr(self.user, "username", "")

    async def _set_typing(self, is_typing: bool) -> None:
        try:
            from core.redis.client import RedisClient

            redis = RedisClient.get_instance()
            key = TYPING_KEY.format(conversation_id=self.conversation_id, user_id=self.user_id)
            if is_typing:
                redis.setex(key, TYPING_TTL_SECONDS, "1")
            else:
                redis.delete(key)
        except Exception:
            pass

    async def _clear_typing(self) -> None:
        await self._set_typing(False)

