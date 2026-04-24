"""
Health check endpoint for Docker/K8s probes.
GET /api/v1/health/  ->  200 if database healthy, 503 if not.
"""
from __future__ import annotations

import logging
import time

from rest_framework import status as http_status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request):
        db = _check_database()
        healthy = db["status"] == "ok"
        return Response(
            {"status": "healthy" if healthy else "degraded", "checks": {"database": db}},
            status=200 if healthy else 503,
        )


def _check_database() -> dict:
    start = time.perf_counter()
    try:
        from django.db import connection
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "ok", "latency_ms": round((time.perf_counter() - start) * 1000, 2)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
