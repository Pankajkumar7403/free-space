"""
core.security
~~~~~~~~~~~~~
    from core.security.jwt import create_token_pair, decode_access_token
    from core.security.hashing import generate_token, generate_otp, hash_token
    from core.security.authentication import QommunityJWTAuthentication
"""

# Ensure drf-spectacular extensions are registered at import time.
from core.security import openapi as _openapi  # noqa: F401
