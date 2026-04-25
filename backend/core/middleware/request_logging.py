"""
core/middleware/request_logging.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Structured JSON request/response logging middleware.

Logs every request with:
  - request_id (UUID, also injected into response headers)
  - method, path, status_code
  - duration_ms
  - user_id (if authenticated)
  - ip address

These fields make logs filterable/searchable in any log aggregator
(Datadog, CloudWatch, Loki, etc.).
"""

from __future__ import annotations

import logging
import time
import uuid

logger = logging.getLogger("qommunity.requests")

_NOISE_PATH_SUFFIXES = (
    "/favicon.ico",
    "/favicon-16.png/",
    "/favicon-32.png/",
)


class RequestLoggingMiddleware:
    """
    WSGI/ASGI-compatible middleware.
    Attaches request_id to the request object so other layers can reference it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ── Assign request ID ─────────────────────────────────────────────────
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.request_id = request_id

        start = time.monotonic()

        response = self.get_response(request)

        duration_ms = round((time.monotonic() - start) * 1000, 2)

        # ── Inject request ID into response headers ───────────────────────────
        response["X-Request-ID"] = request_id

        # ── Structured log ────────────────────────────────────────────────────
        user_id = (
            str(request.user.pk)
            if hasattr(request, "user") and request.user.is_authenticated
            else None
        )

        if any(request.path.endswith(suffix) for suffix in _NOISE_PATH_SUFFIXES):
            return response

        logger.info(
            "%(method)s %(path)s %(status)s %(duration_ms)sms",
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
                "ip": _get_client_ip(request),
            },
        )

        return response


def _get_client_ip(request) -> str:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
