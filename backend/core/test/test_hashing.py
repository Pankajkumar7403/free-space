# 📁 Location: backend/core/tests/test_hashing.py
# ▶  Run:      pytest core/tests/test_hashing.py -v
"""
test_hashing.py
~~~~~~~~~~~~~~~
Tests for core/security/hashing.py
"""

import pytest

from core.security.hashing import (
    generate_otp,
    generate_token,
    hash_token,
    make_api_key,
    verify_token,
)

pytestmark = pytest.mark.unit


class TestGenerateToken:
    def test_returns_string(self):
        assert isinstance(generate_token(), str)

    def test_length_is_reasonable(self):
        token = generate_token(32)
        assert len(token) >= 40  # base64url of 32 bytes

    def test_tokens_are_unique(self):
        assert generate_token() != generate_token()


class TestGenerateOtp:
    def test_default_length_is_6(self):
        otp = generate_otp()
        assert len(otp) == 6

    def test_custom_length(self):
        otp = generate_otp(8)
        assert len(otp) == 8

    def test_contains_only_digits(self):
        for _ in range(20):
            otp = generate_otp()
            assert otp.isdigit()

    def test_otps_are_unique(self):
        otps = {generate_otp() for _ in range(100)}
        # With 6 digits, 100 unique values is trivially expected
        assert len(otps) > 50


class TestHashToken:
    def test_produces_hex_string(self):
        h = hash_token("my-token")
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_input_produces_same_hash(self):
        assert hash_token("abc") == hash_token("abc")

    def test_different_inputs_produce_different_hashes(self):
        assert hash_token("abc") != hash_token("xyz")


class TestVerifyToken:
    def test_correct_token_passes(self):
        token = generate_token()
        stored = hash_token(token)
        assert verify_token(token, stored) is True

    def test_wrong_token_fails(self):
        stored = hash_token("real-token")
        assert verify_token("wrong-token", stored) is False


class TestMakeApiKey:
    def test_returns_two_strings(self):
        raw, hashed = make_api_key()
        assert isinstance(raw, str)
        assert isinstance(hashed, str)

    def test_raw_verifies_against_hash(self):
        raw, hashed = make_api_key()
        assert verify_token(raw, hashed) is True

    def test_raw_and_hash_are_different(self):
        raw, hashed = make_api_key()
        assert raw != hashed
