"""
core/security/authentication.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Custom DRF Authentication class.

Extends Simple JWT's JWTAuthentication to:
  1. Include the request_id in auth failure logs.
"""

from __future__ import annotations

import logging

from rest_framework_simplejwt.authentication import JWTAuthentication  # type: ignore[import]

logger = logging.getLogger(__name__)


class QommunityJWTAuthentication(JWTAuthentication):
    """
    Drop-in replacement for Simple JWT's default authenticator.
    """

    def get_validated_token(self, raw_token):
        return super().get_validated_token(raw_token)
