"""
Health check endpoint for Docker/K8s probes.
GET /api/v1/health/  ->  200 if all services healthy, 503 if degraded.
"""
from __future__ import annotations

import logging
import time

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        checks = {
            "database": _check_database(),
            "redis":    _check_redis(),
        }
        all_healthy = all(v["status"] == "ok" for v in checks.values())

        from django.conf import settings
        response_data = {
            "status":  "healthy" if all_healthy else "degraded",
            "version": getattr(settings, "APP_VERSION", "unknown"),
            "checks":  checks,
        }
        status_code = 200 if all_healthy else 503
        return Response(response_data, status=status_code)


def _check_database() -> dict:
    start = time.perf_counter()
    try:
        from django.db import connection
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        latency = (time.perf_counter() - start) * 1000
        return {"status": "ok", "latency_ms": round(latency, 2)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _check_redis() -> dict:
    start = time.perf_counter()
    try:
        from core.redis.client import RedisClient
        RedisClient.get_instance().ping()
        latency = (time.perf_counter() - start) * 1000
        return {"status": "ok", "latency_ms": round(latency, 2)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
