"""
users/services.py
~~~~~~~~~~~~~~~~~
Write operations (create, update, delete).

Rules:
  - Services call selectors for reads, never raw ORM queries.
  - Services raise domain exceptions, never DRF exceptions.
  - Services are transaction-aware (use atomic blocks for multi-step writes).
  - No HTTP/request/response logic here — that lives in views.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.users.exceptions import (
    AccountInactiveError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from apps.users.selectors import email_exists, get_user_by_id, username_exists

User = get_user_model()


# ── Input dataclasses (avoids positional-arg mistakes) ────────────────────────

@dataclass
class CreateUserInput:
    email: str
    username: str
    password: str
    first_name: str = ""
    last_name: str = ""


@dataclass
class UpdateUserInput:
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


# ── Service functions ─────────────────────────────────────────────────────────

@transaction.atomic
def create_user(data: CreateUserInput) -> User:
    """
    Register a new user.

    Raises
    ------
    EmailAlreadyExistsError
    UsernameAlreadyExistsError
    """
    if email_exists(data.email):
        raise EmailAlreadyExistsError()

    if username_exists(data.username):
        raise UsernameAlreadyExistsError()

    user = User.objects.create_user(
        email=data.email,
        username=data.username,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    return user


@transaction.atomic
def update_user(*, user_id: int, data: UpdateUserInput) -> User:
    """
    Update mutable profile fields on an existing user.

    Raises
    ------
    UserNotFoundError
    UsernameAlreadyExistsError
    """
    user = get_user_by_id(user_id)

    if data.username is not None and data.username != user.username:
        if username_exists(data.username):
            raise UsernameAlreadyExistsError()
        user.username = data.username

    if data.first_name is not None:
        user.first_name = data.first_name

    if data.last_name is not None:
        user.last_name = data.last_name

    user.save(update_fields=["username", "first_name", "last_name"])
    return user


@transaction.atomic
def deactivate_user(*, user_id: int) -> None:
    """
    Soft-delete a user by marking them inactive.

    Raises
    ------
    UserNotFoundError
    """
    user = get_user_by_id(user_id)
    user.is_active = False
    user.save(update_fields=["is_active"])


def authenticate_user(*, email: str, password: str) -> User:
    """
    Verify credentials and return the user.

    Raises
    ------
    InvalidCredentialsError
    AccountInactiveError
    """
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # Constant-time rejection (don't leak whether email exists)
        User().check_password(password)
        raise InvalidCredentialsError()

    if not user.check_password(password):
        raise InvalidCredentialsError()

    if not user.is_active:
        raise AccountInactiveError()

    return user