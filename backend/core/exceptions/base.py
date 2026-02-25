"""
Application exception hierarchy.

All domain exceptions inherit from AppException so the handler
can catch them in one place and serialise them consistently.

Usage:
    raise UserNotFoundError(user_id=42)
    raise ValidationError("Email already in use.", code="EMAIL_TAKEN")
"""
from __future__ import annotations

from rest_framework import status


class AppException(Exception):
    """
    Base for every domain exception.

    Attributes
    ----------
    status_code : int
        HTTP status that should be returned to the client.
    code : str
        Machine-readable error code (e.g. "USER_NOT_FOUND").
    message : str
        Human-readable summary.
    detail : dict | None
        Optional extra payload (field errors, metadata, …).
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        detail: dict | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.code = code or self.__class__.code
        self.detail = detail
        super().__init__(self.message)

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


# ── 4xx Client errors ─────────────────────────────────────────────────────────

class BadRequestError(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "BAD_REQUEST"
    message = "Bad request."


class ValidationError(AppException):
    """Use for *domain* validation failures; use DRF's for serialiser errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    code = "VALIDATION_ERROR"
    message = "Validation failed."


class AuthenticationError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "AUTHENTICATION_FAILED"
    message = "Authentication credentials were invalid."


class PermissionError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    code = "PERMISSION_DENIED"
    message = "You do not have permission to perform this action."


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"
    message = "Resource not found."


class ConflictError(AppException):
    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"
    message = "Resource already exists."


class RateLimitError(AppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please slow down."


# ── 5xx Server errors ─────────────────────────────────────────────────────────

class ServiceUnavailableError(AppException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "SERVICE_UNAVAILABLE"
    message = "The service is temporarily unavailable."


# ── Domain-specific exceptions (apps extend these) ────────────────────────────
# Convention: each app defines its own in apps/<app>/exceptions.py
# Example:
#
#   from core.exceptions.base import NotFoundError
#
#   class UserNotFoundError(NotFoundError):
#       code = "USER_NOT_FOUND"
#       message = "User not found."