"""
Base test classes.

Inherit from these instead of Django's TestCase directly so that
all tests automatically get:
  - Consistent DB transaction handling
  - A pre-authenticated API client
  - Helper assertions for our error envelope shape
"""

from __future__ import annotations

from typing import Any

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class BaseTestCase(TestCase):
    """
    Unit test base.  No network, uses DB transactions that roll back
    after each test method.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    def assertNoException(self, callable_: Any, *args: Any, **kwargs: Any) -> Any:
        """Assert that a callable does NOT raise any exception."""
        try:
            return callable_(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(
                f"Expected no exception, but got {type(exc).__name__}: {exc}"
            ) from exc


class BaseAPITestCase(APITestCase):
    """
    Integration / E2E test base for DRF views.

    Provides:
        self.client        – unauthenticated APIClient
        self.auth_client   – authenticated APIClient (set up in subclass)
        helper assertions  – assert_ok, assert_error, etc.
    """

    client: APIClient

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    # ── Auth helpers ──────────────────────────────────────────────────────────

    def authenticate(self, user: Any) -> None:
        """Force-authenticate the default client as *user*."""
        self.client.force_authenticate(user=user)

    def logout(self) -> None:
        self.client.force_authenticate(user=None)

    # ── Response assertions ───────────────────────────────────────────────────

    def assert_status(self, response: Any, expected: int) -> None:
        body = getattr(response, "data", None)
        if body is None:
            try:
                body = response.content.decode("utf-8")
            except Exception:
                body = "<no body>"
        self.assertEqual(
            response.status_code,
            expected,
            msg=f"Expected HTTP {expected}, got {response.status_code}. Body: {body}",
        )

    def assert_ok(self, response: Any) -> None:
        self.assert_status(response, status.HTTP_200_OK)

    def assert_created(self, response: Any) -> None:
        self.assert_status(response, status.HTTP_201_CREATED)

    def assert_no_content(self, response: Any) -> None:
        self.assert_status(response, status.HTTP_204_NO_CONTENT)

    def assert_bad_request(self, response: Any) -> None:
        self.assert_status(response, status.HTTP_400_BAD_REQUEST)

    def assert_unauthorized(self, response: Any) -> None:
        self.assert_status(response, status.HTTP_401_UNAUTHORIZED)

    def assert_forbidden(self, response: Any) -> None:
        self.assert_status(response, status.HTTP_403_FORBIDDEN)

    def assert_not_found(self, response: Any) -> None:
        self.assert_status(response, status.HTTP_404_NOT_FOUND)

    def assert_error_code(self, response: Any, code: str) -> None:
        """Assert the response contains our standard error envelope with *code*."""
        self.assertIn("error", response.data, msg="Response missing 'error' key")
        actual_code = response.data["error"].get("code")
        self.assertEqual(
            actual_code,
            code,
            msg=f"Expected error code {code!r}, got {actual_code!r}",
        )

    def assert_field_error(self, response: Any, field: str) -> None:
        """Assert that *field* appears in the validation error detail."""
        self.assertIn("error", response.data)
        detail = response.data["error"].get("detail", {}) or {}
        self.assertIn(
            field,
            detail,
            msg=f"Expected field error for {field!r}, got keys: {list(detail.keys())}",
        )
