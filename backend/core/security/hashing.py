"""
core/security/hashing.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Secure hashing utilities.

Django handles password hashing automatically via its auth backend,
but we need stand-alone hashing for:
  - OTP / verification tokens
  - API key generation and verification
  - Sensitive data at rest (phone numbers, etc.)
"""

from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_token(nbytes: int = 32) -> str:
    """
    Generate a cryptographically secure URL-safe random token.

    Default 32 bytes → 43-character base64url string.
    Use for: email verification links, password reset tokens, API keys.
    """
    return secrets.token_urlsafe(nbytes)


def generate_otp(length: int = 6) -> str:
    """
    Generate a numeric OTP (one-time password) of *length* digits.
    Uses secrets.randbelow for cryptographic randomness.
    """
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_token(token: str) -> str:
    """
    Hash a token for safe storage (store the hash, not the raw token).

    Uses SHA-256 — fast enough for one-off verification, doesn't need bcrypt.
    Compare with verify_token() — never compare raw strings.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(raw_token: str, stored_hash: str) -> bool:
    """
    Constant-time comparison of a raw token against its stored hash.
    Prevents timing attacks.
    """
    expected = hash_token(raw_token)
    return hmac.compare_digest(expected, stored_hash)


def make_api_key() -> tuple[str, str]:
    """
    Generate an API key + its hash for storage.

    Returns (raw_key, hashed_key).
    Store only the hashed_key in the database.
    Return raw_key to the user exactly once.

    Example
    -------
        raw, hashed = make_api_key()
        ApiKey.objects.create(user=user, key_hash=hashed)
        # Send raw to client — never store it
    """
    raw = generate_token(40)
    hashed = hash_token(raw)
    return raw, hashed
