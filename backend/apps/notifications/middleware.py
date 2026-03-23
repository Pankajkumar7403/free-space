"""
apps/notifications/middleware.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
JWT authentication middleware for Django Channels WebSocket connections.

The browser WebSocket API does NOT support custom headers, so we accept the
JWT access token as a URL query parameter:

    ws://api.qommunity.app/ws/notifications/?token=<access_token>

The middleware validates the token, resolves the User, and populates
scope["user"] before the consumer's connect() is called.
If the token is absent or invalid, scope["user"] is set to AnonymousUser.
The consumer is responsible for rejecting anonymous users with close(4001).
"""
from __future__ import annotations

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseMiddleware):
    """Populate scope['user'] from ?token= query-string JWT."""

    async def __call__(self, scope, receive, send):
        scope["user"] = await self._authenticate(scope)
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def _authenticate(self, scope):
        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        token_list = params.get("token", [])

        if not token_list:
            return AnonymousUser()

        token = token_list[0]

        try:
            # Uses the shared JWT utility from core/security/jwt.py.
            from core.security.jwt import decode_access_token

            payload = decode_access_token(token)

            user_id = payload.get("user_id")
            if not user_id:
                return AnonymousUser()

            from apps.users.models import User

            return User.objects.get(id=user_id)

        except Exception as exc:
            logger.debug(
                "ws.auth.failed",
                extra={"reason": str(exc)},
            )
            return AnonymousUser()


def JWTAuthMiddlewareStack(inner):
    """
    Convenience wrapper - mirrors Django's AuthMiddlewareStack pattern.
    Usage in asgi.py:  JWTAuthMiddlewareStack(URLRouter(...))
    """
    return JWTAuthMiddleware(inner)
