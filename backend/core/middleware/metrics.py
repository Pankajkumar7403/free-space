"""
core/middleware/metrics.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Lightweight metrics middleware.

In production, this feeds into Prometheus via django-prometheus.
In dev/test, it's a no-op so no external service is needed.

Tracks:
  - http_requests_total (counter, by method/path/status)
  - http_request_duration_seconds (histogram)
"""
from __future__ import annotations

import logging
import time

from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import prometheus_client; gracefully skip if not installed
try:
    from prometheus_client import Counter, Histogram  # type: ignore[import]

    REQUEST_COUNT = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )
    REQUEST_LATENCY = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "endpoint"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class MetricsMiddleware:
    """
    Record per-request latency and count metrics.
    No-ops cleanly when prometheus_client is not installed.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        if not PROMETHEUS_AVAILABLE:
            logger.debug("MetricsMiddleware: prometheus_client not installed, metrics disabled")

    def __call__(self, request):
        if not PROMETHEUS_AVAILABLE:
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        duration = time.monotonic() - start

        # Normalise path to avoid high-cardinality labels
        endpoint = _normalise_path(request.path)

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)

        return response


def _normalise_path(path: str) -> str:
    """
    Replace UUIDs and numeric IDs in paths to reduce label cardinality.

    /api/v1/users/550e8400-e29b-41d4-a716-446655440000/  →  /api/v1/users/{id}/
    /api/v1/posts/42/comments/                           →  /api/v1/posts/{id}/comments/
    """
    import re
    # Replace UUIDs
    path = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "{id}",
        path,
    )
    # Replace numeric IDs
    path = re.sub(r"/\d+(/|$)", r"/{id}\1", path)
    return path