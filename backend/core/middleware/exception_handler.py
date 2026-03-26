"""
core/middleware/exception_handler.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Django middleware that catches any exception not already handled by DRF
and returns a consistent JSON error envelope.

This is the LAST safety net.  DRF's exception handler handles API errors;
this handles Django-level 500s (database errors, programming mistakes, etc.)
that would otherwise return an ugly HTML page.
"""

from __future__ import annotations

import logging

from django.http import JsonResponse

logger = logging.getLogger("qommunity.exceptions")


class ExceptionHandlerMiddleware:
    """
    Wrap every request in a try/except.

    If an unhandled exception escapes both DRF and Django's own error
    handling, catch it here and return a clean JSON 500.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception: Exception):
        request_id = getattr(request, "request_id", "unknown")

        logger.exception(
            "Unhandled exception: request_id=%s path=%s",
            request_id,
            request.path,
            exc_info=exception,
        )

        return JsonResponse(
            {
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                    "detail": None,
                    "request_id": request_id,
                }
            },
            status=500,
        )
