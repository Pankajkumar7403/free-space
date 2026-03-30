"""
config/routing.py
~~~~~~~~~~~~~~~~~
WebSocket URL patterns.
Imported by config/asgi.py ProtocolTypeRouter.
"""

from django.urls import re_path

from apps.messaging.consumers import MessageConsumer
from apps.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    # ws://api.qommunity.app/ws/notifications/?token=<jwt>
    re_path(r"^ws/notifications/$", NotificationConsumer.as_asgi()),
    # ws://api.qommunity.app/ws/messages/<conversation_id>/?token=<jwt>
    re_path(
        r"^ws/messages/(?P<conversation_id>[0-9a-f\-]{36})/$", MessageConsumer.as_asgi()
    ),
]
