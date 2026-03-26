"""
Custom DRF exception handler.

Produces a consistent JSON envelope for every error response:

    {
        "error": {
            "code":    "VALIDATION_ERROR",
            "message": "Invalid input.",
            "detail":  { ... }          # optional – field-level errors
        }
    }
"""

from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler

from core.exceptions.base import AppException

logger = logging.getLogger(__name__)


def custom_exception_handler(
    exc: Exception, context: dict[str, Any]
) -> Response | None:
    """
    Entry-point configured in REST_FRAMEWORK["EXCEPTION_HANDLER"].

    Converts *every* exception into a standardised error envelope.
    Unknown / unexpected exceptions are logged with a full traceback.
    """

    # ── 1. Translate Django / stdlib exceptions into DRF equivalents ──────────
    if isinstance(exc, Http404):
        from rest_framework.exceptions import NotFound

        exc = NotFound()
    elif isinstance(exc, PermissionDenied):
        from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied

        exc = DRFPermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        from rest_framework.exceptions import ValidationError

        exc = ValidationError(
            detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        )

    # ── 2. Handle our own domain exceptions ───────────────────────────────────
    if isinstance(exc, AppException):
        return Response(
            {"error": {"code": exc.code, "message": exc.message, "detail": exc.detail}},
            status=exc.status_code,
        )

    # ── 3. Let DRF handle its own exceptions, then reshape the response ───────
    response = drf_default_handler(exc, context)
    if response is not None:
        error_code = _get_error_code(exc)
        message = _get_message(exc)
        detail = response.data if not isinstance(response.data, str) else None

        response.data = {
            "error": {
                "code": error_code,
                "message": message,
                "detail": detail,
            }
        }
        return response

    # ── 4. Unexpected server error ────────────────────────────────────────────
    logger.exception(
        "Unhandled exception in %s",
        context.get("view", "unknown view"),
        exc_info=exc,
    )
    return Response(
        {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "detail": None,
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_error_code(exc: APIException) -> str:
    """Map DRF exception class to a stable error code string."""
    from rest_framework import exceptions as drf_exc

    mapping: dict[type, str] = {
        drf_exc.ValidationError: "VALIDATION_ERROR",
        drf_exc.AuthenticationFailed: "AUTHENTICATION_FAILED",
        drf_exc.NotAuthenticated: "NOT_AUTHENTICATED",
        drf_exc.PermissionDenied: "PERMISSION_DENIED",
        drf_exc.NotFound: "NOT_FOUND",
        drf_exc.MethodNotAllowed: "METHOD_NOT_ALLOWED",
        drf_exc.Throttled: "THROTTLED",
    }
    return mapping.get(type(exc), "API_ERROR")


def _get_message(exc: APIException) -> str:
    detail = exc.detail
    if isinstance(detail, list) and detail:
        return str(detail[0])
    if isinstance(detail, dict):
        # Return the first field-level message
        first_val = next(iter(detail.values()), "")
        if isinstance(first_val, list) and first_val:
            return str(first_val[0])
        return str(first_val)
    return str(detail)
