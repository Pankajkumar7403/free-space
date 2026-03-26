# 📁 Location: backend/apps/users/validators.py

from __future__ import annotations

import re

from core.exceptions.base import ValidationError

# ── Username ──────────────────────────────────────────────────────────────────

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_\.]{3,30}$")
_RESERVED_USERNAMES = frozenset(
    {
        "admin",
        "support",
        "help",
        "qommunity",
        "staff",
        "mod",
        "moderator",
        "root",
        "api",
        "system",
        "bot",
    }
)


def validate_username(username: str) -> None:
    """
    Username rules:
      - 3–30 characters
      - Letters, numbers, underscores, dots only
      - Cannot be a reserved word
    """
    if not username:
        raise ValidationError("Username is required.", code="USERNAME_REQUIRED")

    if not _USERNAME_RE.match(username):
        raise ValidationError(
            "Username must be 3–30 characters and contain only letters, "
            "numbers, underscores, or dots.",
            code="USERNAME_INVALID_FORMAT",
        )

    if username.lower() in _RESERVED_USERNAMES:
        raise ValidationError(
            f"'{username}' is a reserved username.",
            code="USERNAME_RESERVED",
        )


# ── Password ──────────────────────────────────────────────────────────────────


def validate_password_strength(password: str) -> None:
    """
    Password must be at least 8 characters.
    We intentionally keep this simple — complexity rules hurt accessibility.
    Django's built-in validators handle common/dictionary passwords.
    """
    if len(password) < 8:
        raise ValidationError(
            "Password must be at least 8 characters long.",
            code="PASSWORD_TOO_SHORT",
        )

    if password.isdigit():
        raise ValidationError(
            "Password cannot be entirely numeric.",
            code="PASSWORD_ENTIRELY_NUMERIC",
        )


# ── Email ─────────────────────────────────────────────────────────────────────


def validate_email_format(email: str) -> None:
    """Basic email format check (DRF/Django also validates this, belt-and-suspenders)."""
    if not email or "@" not in email:
        raise ValidationError("Enter a valid email address.", code="EMAIL_INVALID")


# ── Bio ───────────────────────────────────────────────────────────────────────


def validate_bio(bio: str) -> None:
    if len(bio) > 500:
        raise ValidationError(
            "Bio cannot exceed 500 characters.",
            code="BIO_TOO_LONG",
        )
