"""
core/security/jwt.py
~~~~~~~~~~~~~~~~~~~~
JWT helpers that wrap Simple JWT (djangorestframework-simplejwt).

Centralises token creation/validation so app code never touches
the JWT library directly — easy to swap implementations later.

Usage
-----
    from core.security.jwt import create_token_pair, decode_access_token

    tokens = create_token_pair(user)
    # → {"access": "eyJ...", "refresh": "eyJ..."}

    payload = decode_access_token(access_token_string)
    # → {"user_id": "...", "exp": ..., "jti": "..."}
"""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


def create_token_pair(user) -> dict[str, str]:
    """
    Create a new access + refresh token pair for *user*.

    Returns
    -------
    {"access": str, "refresh": str}
    """
    from rest_framework_simplejwt.tokens import RefreshToken  # type: ignore[import]

    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate an access token.

    Returns the payload dict on success.

    Raises
    ------
    core.exceptions.base.AuthenticationError  on invalid / expired token
    """
    from rest_framework_simplejwt.exceptions import TokenError  # type: ignore[import]
    from rest_framework_simplejwt.tokens import AccessToken  # type: ignore[import]

    from core.exceptions.base import AuthenticationError

    try:
        token_obj = AccessToken(token)
        return dict(token_obj.payload)
    except TokenError as exc:
        raise AuthenticationError(message=str(exc)) from exc


def blacklist_refresh_token(refresh_token_str: str) -> None:
    """
    Add a refresh token to the blacklist (called on logout).
    Uses our Redis blacklist for instant revocation.
    """
    from rest_framework_simplejwt.tokens import RefreshToken  # type: ignore[import]
    from rest_framework_simplejwt.exceptions import TokenError  # type: ignore[import]

    from core.exceptions.base import AuthenticationError

    try:
        token = RefreshToken(refresh_token_str)
        jti = token.payload.get("jti")
        if jti:
            from core.redis.cache import blacklist_token
            remaining_ttl = int(
                token.payload.get("exp", 0) - token.payload.get("iat", 0)
            )
            blacklist_token(jti, ttl=max(remaining_ttl, 1))
    except TokenError as exc:
        raise AuthenticationError(message=str(exc)) from exc


def get_jwt_settings() -> dict:
    """Return the current Simple JWT settings dict."""
    from rest_framework_simplejwt.settings import api_settings  # type: ignore[import]
    return {
        "ACCESS_TOKEN_LIFETIME": str(api_settings.ACCESS_TOKEN_LIFETIME),
        "REFRESH_TOKEN_LIFETIME": str(api_settings.REFRESH_TOKEN_LIFETIME),
        "ALGORITHM": api_settings.ALGORITHM,
    }