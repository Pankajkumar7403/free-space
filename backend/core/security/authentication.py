"""
core/security/authentication.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Custom DRF Authentication class.

Extends Simple JWT's JWTAuthentication to:
  1. Check our Redis blacklist on every request (instant token revocation).
  2. Include the request_id in auth failure logs.
"""
from __future__ import annotations

import logging

from rest_framework_simplejwt.authentication import JWTAuthentication  # type: ignore[import]
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError  # type: ignore[import]

from core.redis.cache import is_token_blacklisted

logger = logging.getLogger(__name__)


class QommunityJWTAuthentication(JWTAuthentication):
    """
    Drop-in replacement for Simple JWT's default authenticator.

    Extra behaviour
    ---------------
    - Checks Redis blacklist before accepting a token.
      This enables instant logout even before the token naturally expires.
    """

    def get_validated_token(self, raw_token):
        validated = super().get_validated_token(raw_token)

        jti = validated.get("jti")
        if jti and is_token_blacklisted(jti):
            raise InvalidToken(
                {"detail": "Token has been revoked. Please log in again."}
            )

        return validated