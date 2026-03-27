"""
core/security/app_version.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
App version header middleware.

Mobile clients send:  X-App-Version: 2.1.0
If the version is below the minimum supported version,
we return a 426 Upgrade Required response.

This lets us force-update clients without a server-side feature flag system.

Configuration (settings.py)
----------------------------
    APP_MIN_VERSION = "1.0.0"   # clients older than this are rejected
    APP_VERSION_HEADER = "X-App-Version"   # default
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse "1.2.3" → (1, 2, 3). Returns (0,) on parse failure."""
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except (ValueError, AttributeError):
        return (0,)


class AppVersionMiddleware:
    """
    Enforce a minimum client app version.

    Only applies to requests that include the X-App-Version header.
    Web clients (no header) are never blocked.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.header = getattr(settings, "APP_VERSION_HEADER", "HTTP_X_APP_VERSION")
        self.min_version_str = getattr(settings, "APP_MIN_VERSION", "0.0.0")
        self.min_version = _parse_version(self.min_version_str)

    def __call__(self, request):
        client_version_str = request.META.get(self.header)

        if client_version_str:
            client_version = _parse_version(client_version_str)
            if client_version < self.min_version:
                logger.info(
                    "AppVersionMiddleware: rejected client version=%s min=%s",
                    client_version_str,
                    self.min_version_str,
                )
                return JsonResponse(
                    {
                        "error": {
                            "code": "APP_UPDATE_REQUIRED",
                            "message": f"Please update the app to version {self.min_version_str} or later.",
                            "detail": {
                                "minimum_version": self.min_version_str,
                                "your_version": client_version_str,
                            },
                        }
                    },
                    status=426,
                )

        return self.get_response(request)
