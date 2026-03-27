"""
core/middleware/metrics.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Prometheus metrics middleware.
Records HTTP request duration, total count, and in-progress gauge
for every request that passes through Django.

Uses the shared metrics registry in core/monitoring/prometheus.py.

Registration in settings.py MIDDLEWARE:
    "core.middleware.metrics.PrometheusMetricsMiddleware",
    # must be FIRST middleware to capture total latency
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)

_SKIP_PATHS = frozenset({"/metrics", "/health/", "/favicon.ico"})


class PrometheusMetricsMiddleware:
    """
    WSGI/ASGI-compatible metrics middleware.
    Wraps every request with latency histogram + request counter.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        try:
            from core.monitoring.prometheus import (
                HTTP_REQUEST_DURATION,
                HTTP_REQUEST_IN_PROGRESS,
                HTTP_REQUEST_TOTAL,
            )

            self._duration = HTTP_REQUEST_DURATION
            self._in_prog = HTTP_REQUEST_IN_PROGRESS
            self._total = HTTP_REQUEST_TOTAL
            self._enabled = True
        except Exception:
            self._enabled = False

    def __call__(self, request):
        if not self._enabled or request.path in _SKIP_PATHS:
            return self.get_response(request)

        endpoint = self._get_endpoint(request)
        method = request.method

        self._in_prog.labels(method=method, endpoint=endpoint).inc()
        start = time.perf_counter()

        try:
            response = self.get_response(request)
            status = str(response.status_code)
        except Exception:
            status = "500"
            raise
        finally:
            duration = time.perf_counter() - start
            self._in_prog.labels(method=method, endpoint=endpoint).dec()
            self._duration.labels(
                method=method, endpoint=endpoint, status_code=status
            ).observe(duration)
            self._total.labels(
                method=method, endpoint=endpoint, status_code=status
            ).inc()

        return response

    @staticmethod
    def _get_endpoint(request) -> str:
        """
        Return the URL pattern name (e.g. /api/v1/posts/) instead of the
        raw path - prevents high-cardinality from UUIDs in paths.
        """
        try:
            from django.urls import resolve

            match = resolve(request.path_info)
            # Build pattern string from namespace + route
            ns = f"{match.namespace}:" if match.namespace else ""
            return f"/{ns}{match.url_name}/"
        except Exception:
            # Fallback: strip trailing UUID/int segments
            parts = request.path.split("/")
            cleaned = [p for p in parts if not _looks_like_id(p)]
            return "/".join(cleaned) or "/"


def _looks_like_id(segment: str) -> bool:
    if len(segment) == 36 and segment.count("-") == 4:
        return True  # UUID
    return segment.isdigit()
