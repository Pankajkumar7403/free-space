# 📁 Location: backend/core/tests/test_exception_handler.py
# ▶  Run:      pytest core/tests/test_exception_handler.py -v
"""
test_exception_handler.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for core/exceptions/handler.py and core/exceptions/base.py

Verifies that every exception type is converted to our
standard { "error": { "code", "message", "detail" } } envelope.
"""
from __future__ import annotations

import pytest
from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.exceptions.base import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ValidationError,
)
from core.exceptions.handler import custom_exception_handler

pytestmark = pytest.mark.unit


def make_context():
    factory = APIRequestFactory()
    request = factory.get("/")
    return {"request": request, "view": None}


class TestAppExceptions:
    def test_not_found_returns_404(self):
        exc = NotFoundError()
        response = custom_exception_handler(exc, make_context())
        assert response.status_code == 404
        assert response.data["error"]["code"] == "NOT_FOUND"

    def test_conflict_returns_409(self):
        exc = ConflictError()
        response = custom_exception_handler(exc, make_context())
        assert response.status_code == 409
        assert response.data["error"]["code"] == "CONFLICT"

    def test_authentication_error_returns_401(self):
        exc = AuthenticationError()
        response = custom_exception_handler(exc, make_context())
        assert response.status_code == 401
        assert response.data["error"]["code"] == "AUTHENTICATION_FAILED"

    def test_permission_error_returns_403(self):
        exc = PermissionError()
        response = custom_exception_handler(exc, make_context())
        assert response.status_code == 403

    def test_rate_limit_returns_429(self):
        exc = RateLimitError()
        response = custom_exception_handler(exc, make_context())
        assert response.status_code == 429
        assert response.data["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    def test_custom_message_is_included(self):
        exc = NotFoundError("User with id 42 not found")
        response = custom_exception_handler(exc, make_context())
        assert "42" in response.data["error"]["message"]

    def test_detail_payload_is_forwarded(self):
        exc = ValidationError(detail={"field": "email", "reason": "already taken"})
        response = custom_exception_handler(exc, make_context())
        assert response.data["error"]["detail"]["field"] == "email"

    def test_subclass_uses_class_code(self):
        from core.exceptions.base import NotFoundError

        class UserNotFoundError(NotFoundError):
            code = "USER_NOT_FOUND"

        exc = UserNotFoundError()
        response = custom_exception_handler(exc, make_context())
        assert response.data["error"]["code"] == "USER_NOT_FOUND"


class TestDRFExceptions:
    def test_drf_validation_error_is_shaped(self):
        from rest_framework.exceptions import ValidationError as DRFValidationError

        exc = DRFValidationError({"email": ["This field is required."]})
        response = custom_exception_handler(exc, make_context())
        assert response.data["error"]["code"] == "VALIDATION_ERROR"
        assert "error" in response.data

    def test_drf_not_found_is_shaped(self):
        from django.http import Http404

        response = custom_exception_handler(Http404(), make_context())
        assert response.status_code == 404
        assert response.data["error"]["code"] == "NOT_FOUND"

    def test_drf_permission_denied_is_shaped(self):
        from django.core.exceptions import PermissionDenied

        response = custom_exception_handler(PermissionDenied(), make_context())
        assert response.status_code == 403

    def test_unknown_exception_returns_500(self):
        exc = RuntimeError("Something blew up")
        response = custom_exception_handler(exc, make_context())
        assert response.status_code == 500
        assert response.data["error"]["code"] == "INTERNAL_SERVER_ERROR"


class TestErrorEnvelopeShape:
    """Assert the envelope always has the exact same shape."""

    @pytest.mark.parametrize("exc,expected_status", [
        (NotFoundError(), 404),
        (ConflictError(), 409),
        (ValidationError(), 400),
        (RateLimitError(), 429),
    ])
    def test_envelope_always_has_required_keys(self, exc, expected_status):
        response = custom_exception_handler(exc, make_context())
        error = response.data["error"]
        assert "code" in error
        assert "message" in error
        assert "detail" in error
        assert response.status_code == expected_status