"""
Tests for utility functions.

Run with: pytest tests/
"""
import pytest
from app.utils.fx import ngn_equivalent
from app.utils.security import verify_hmac_sha512
from app.utils.ratelimit import RateLimiter, _BUCKETS
from app.utils.encryption import encrypt_secret, decrypt_secret, mask_last4


class TestCurrencyConversion:
    """Test currency conversion utilities."""

    def test_ngn_to_ngn(self):
        """Test NGN to NGN conversion (no-op)."""
        result = ngn_equivalent(100000.0, "NGN")
        assert result == 100000

    def test_usd_to_ngn_with_rate(self, monkeypatch):
        """Test USD to NGN conversion with static rate."""
        monkeypatch.setenv("USE_LIVE_FX_RATES", "false")
        monkeypatch.setenv("FX_NGN_RATE", "1650")
        result = ngn_equivalent(100.0, "USD")
        assert result == 165000

    def test_none_amount(self):
        """Test conversion with None amount returns None."""
        result = ngn_equivalent(None, "USD")
        assert result is None

    def test_none_currency(self):
        """Test conversion with None currency returns None."""
        result = ngn_equivalent(100.0, None)
        assert result is None

    def test_zero_rate(self, monkeypatch):
        """Test conversion with zero rate returns None."""
        monkeypatch.setenv("USE_LIVE_FX_RATES", "false")
        monkeypatch.setenv("FX_NGN_RATE", "0")
        result = ngn_equivalent(100.0, "XYZ", fallback_rate=0.0)
        assert result is None
class TestHMACSignature:
    """Test HMAC signature verification."""

    def test_valid_signature(self):
        """Test valid HMAC signature verification."""
        secret = "test_secret_key"
        payload = b'{"event":"test","data":{"amount":100}}'

        import hmac
        import hashlib

        # Generate valid signature
        signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()

        # Verify it
        assert verify_hmac_sha512(secret, payload, signature) is True

    def test_invalid_signature(self):
        """Test invalid HMAC signature verification."""
        secret = "test_secret_key"
        payload = b'{"event":"test","data":{"amount":100}}'
        invalid_signature = "invalid_signature_12345"

        assert verify_hmac_sha512(secret, payload, invalid_signature) is False

    def test_tampered_payload(self):
        """Test HMAC verification with tampered payload."""
        secret = "test_secret_key"
        original_payload = b'{"event":"test","data":{"amount":100}}'

        import hmac
        import hashlib

        # Generate signature for original
        signature = hmac.new(
            secret.encode('utf-8'),
            original_payload,
            hashlib.sha512
        ).hexdigest()

        # Try to verify with modified payload
        tampered_payload = b'{"event":"test","data":{"amount":999}}'
        assert verify_hmac_sha512(secret, tampered_payload, signature) is False


class TestRateLimiter:
    """Test rate limiting functionality."""

    def test_rate_limiter_allows_initial_requests(self):
        """Test rate limiter allows requests within limit."""
        _BUCKETS.clear()
        limiter = RateLimiter(rate=5 / 60.0, capacity=5)
        client_id = "test_client_1"

        for _ in range(5):
            assert limiter.allow(client_id) is True

    def test_rate_limiter_blocks_excess_requests(self):
        """Test rate limiter blocks requests over limit."""
        _BUCKETS.clear()
        limiter = RateLimiter(rate=3 / 60.0, capacity=3)
        client_id = "test_client_2"

        for _ in range(3):
            assert limiter.allow(client_id) is True

        assert limiter.allow(client_id) is False

    def test_rate_limiter_different_clients(self):
        """Test rate limiter tracks clients independently."""
        _BUCKETS.clear()
        limiter = RateLimiter(rate=2 / 60.0, capacity=2)

        assert limiter.allow("client_a") is True
        assert limiter.allow("client_a") is True
        assert limiter.allow("client_a") is False  # Exceeded

        assert limiter.allow("client_b") is True
        assert limiter.allow("client_b") is True
class TestEncryption:
    """Test loyalty encryption utilities."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypting then decrypting should restore the original value."""
        secret = "EW123456"
        token = encrypt_secret(secret)
        assert token != secret
        assert decrypt_secret(token) == secret

    def test_mask_last4(self):
        """Last four masking should handle short inputs."""
        assert mask_last4("1234567") == "4567"
        assert mask_last4("99") == "99"
        assert mask_last4("") == ""

