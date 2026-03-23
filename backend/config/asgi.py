"""
config/asgi.py
~~~~~~~~~~~~~~
ASGI entry point for Qommunity.

Handles both HTTP (Django) and WebSocket (Django Channels) traffic.

WebSocket URL patterns are defined in config/routing.py.
JWT auth is applied to all WebSocket connections via JWTAuthMiddleware.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Initialize Django BEFORE importing anything that touches the app registry
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from apps.notifications.middleware import JWTAuthMiddlewareStack  # noqa: E402
from config.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        # Standard Django request/response over HTTP
        "http": django_asgi_app,
        # WebSocket connections — JWT-authenticated, host-validated
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
