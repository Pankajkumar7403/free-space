"""
WebSocket consumer tests.

These are async tests using channels.testing.WebsocketCommunicator.
pytest-asyncio runs them. Django DB access uses @pytest.mark.django_db(transaction=True).

The CHANNEL_LAYERS setting is patched to InMemoryChannelLayer in testing.py,
so no Redis is required.
"""

import pytest
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator

from apps.notifications.constants import get_notification_group
from config.asgi import application


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestNotificationConsumerConnect:
    async def test_authenticated_user_connects(self, user_factory, jwt_token_factory):
        user = await sync_to_async(user_factory)()
        token = await sync_to_async(jwt_token_factory)(user)

        comm = WebsocketCommunicator(
            application,
            f"/ws/notifications/?token={token}",
        )
        connected, _ = await comm.connect()
        assert connected, "Valid JWT should allow WebSocket connection"

        msg = await comm.receive_json_from(timeout=5)
        assert msg["type"] == "connected"
        assert "unread_count" in msg

        await comm.disconnect()

    async def test_unauthenticated_rejected(self):
        comm = WebsocketCommunicator(application, "/ws/notifications/")
        connected, code = await comm.connect()
        # Either not connected at all, or closed with 4001
        assert not connected or code == 4001
        await comm.disconnect()

    async def test_invalid_token_rejected(self):
        comm = WebsocketCommunicator(
            application, "/ws/notifications/?token=bad.jwt.token"
        )
        connected, code = await comm.connect()
        assert not connected or code == 4001
        await comm.disconnect()

    async def test_unread_count_in_handshake(
        self, user_factory, jwt_token_factory, notification_factory
    ):
        user = await sync_to_async(user_factory)()
        await sync_to_async(notification_factory)(recipient=user, is_read=False)
        await sync_to_async(notification_factory)(recipient=user, is_read=False)

        token = await sync_to_async(jwt_token_factory)(user)
        comm = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
        await comm.connect()
        msg = await comm.receive_json_from(timeout=5)

        assert msg["type"] == "connected"
        assert msg["unread_count"] == 2

        await comm.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestNotificationConsumerReceive:
    async def test_receives_notification_from_channel_layer(
        self, user_factory, jwt_token_factory
    ):
        user = await sync_to_async(user_factory)()
        token = await sync_to_async(jwt_token_factory)(user)

        comm = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
        await comm.connect()
        await comm.receive_json_from(timeout=5)  # consume "connected" handshake

        # Simulate dispatcher sending a notification via channel layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            get_notification_group(user.id),
            {
                "type": "notification_message",
                "data": {
                    "type": "notification",
                    "id": "test-uuid",
                    "notification_type": "follow",
                    "message": "testuser started following you",
                    "is_read": False,
                    "created_at": "2026-03-23T12:00:00Z",
                },
            },
        )

        msg = await comm.receive_json_from(timeout=5)
        assert msg["type"] == "notification"
        assert msg["message"] == "testuser started following you"

        await comm.disconnect()

    async def test_ping_pong(self, user_factory, jwt_token_factory):
        user = await sync_to_async(user_factory)()
        token = await sync_to_async(jwt_token_factory)(user)

        comm = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
        await comm.connect()
        await comm.receive_json_from(timeout=5)  # connected

        await comm.send_json_to({"action": "ping"})
        response = await comm.receive_json_from(timeout=5)
        assert response["type"] == "pong"

        await comm.disconnect()

    async def test_mark_read_via_websocket(
        self, user_factory, jwt_token_factory, notification_factory
    ):
        user = await sync_to_async(user_factory)()
        notif = await sync_to_async(notification_factory)(recipient=user, is_read=False)
        token = await sync_to_async(jwt_token_factory)(user)

        comm = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
        await comm.connect()
        await comm.receive_json_from(timeout=5)  # connected

        await comm.send_json_to(
            {
                "action": "mark_read",
                "notification_id": str(notif.id),
            }
        )

        msg = await comm.receive_json_from(timeout=5)
        assert msg["type"] == "notification_updated"
        assert msg["is_read"] is True

        # Verify DB was updated
        await sync_to_async(notif.refresh_from_db)()
        assert notif.is_read is True

        await comm.disconnect()

    async def test_mark_all_read_via_websocket(
        self, user_factory, jwt_token_factory, notification_factory
    ):
        user = await sync_to_async(user_factory)()
        await sync_to_async(notification_factory)(recipient=user, is_read=False)
        await sync_to_async(notification_factory)(recipient=user, is_read=False)
        token = await sync_to_async(jwt_token_factory)(user)

        comm = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
        await comm.connect()
        await comm.receive_json_from(timeout=5)  # connected

        await comm.send_json_to({"action": "mark_all_read"})
        msg = await comm.receive_json_from(timeout=5)

        assert msg["type"] == "all_notifications_read"
        assert msg["marked_count"] == 2
        assert msg["unread_count"] == 0

        await comm.disconnect()
