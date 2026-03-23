"""
config/routing.py
~~~~~~~~~~~~~~~~~
WebSocket URL patterns.
Imported by config/asgi.py ProtocolTypeRouter.
"""
from django.urls import re_path

from apps.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    # ws://api.qommunity.app/ws/notifications/?token=<jwt>
    re_path(r"^ws/notifications/$", NotificationConsumer.as_asgi()),
]
