"""
users/selectors.py
~~~~~~~~~~~~~~~~~~
Read-only queries.  No writes happen here.

Every function returns a queryset or a model instance.
Raise domain exceptions (not Http404) so the caller decides how to respond.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from apps.users.exceptions import UserNotFoundError

User = get_user_model()


def get_user_by_id(user_id: int) -> User:
    """
    Fetch a single active user by primary key.

    Raises
    ------
    UserNotFoundError
        If no active user with *user_id* exists.
    """
    try:
        return User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        raise UserNotFoundError(detail={"user_id": user_id})


def get_user_by_email(email: str) -> User:
    """
    Fetch a single active user by email (case-insensitive).

    Raises
    ------
    UserNotFoundError
    """
    try:
        return User.objects.get(email__iexact=email, is_active=True)
    except User.DoesNotExist:
        raise UserNotFoundError(detail={"email": email})


def get_active_users() -> QuerySet:
    """Return all active users ordered by join date (newest first)."""
    return User.objects.filter(is_active=True).order_by("-date_joined")


def get_user_by_username(username: str) -> User:
    """
    Fetch a single active user by username (case-insensitive).

    Raises
    ------
    UserNotFoundError
    """
    try:
        return User.objects.get(username__iexact=username, is_active=True)
    except User.DoesNotExist:
        raise UserNotFoundError(detail={"username": username})


def email_exists(email: str) -> bool:
    return User.objects.filter(email__iexact=email).exists()


def username_exists(username: str) -> bool:
    return User.objects.filter(username__iexact=username).exists()