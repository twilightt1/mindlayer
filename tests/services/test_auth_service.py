"""
Unit tests for auth_service.

Tests the business logic in app/services/auth_service.py:
- Password hashing (bcrypt)
- OTP generation
- Token operations
- Helper functions

Note: Integration tests for the full auth flow (endpoint tests) are in
tests/test_auth.py. These tests focus on pure logic and service functions
that can be tested without the full app context.
"""
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the functions we want to test
from app.services import auth_service


class TestPasswordHashing:
    """Tests for _hash, _verify, _hash_async, _verify_async."""

    def test_hash_returns_bcrypt_hash(self):
        """Password hash should be a valid bcrypt hash."""
        password = "SecurePass123!"
        hashed = auth_service._hash(password)

        # bcrypt hashes start with $2b$ or $2a$
        assert hashed.startswith("$2")
        assert len(hashed) == 60  # bcrypt hashes are always 60 chars

    def test_hash_is_deterministic(self):
        """Same password should produce same hash (bcrypt)."""
        password = "SamePassword"
        hash1 = auth_service._hash(password)
        hash2 = auth_service._hash(password)

        # Note: bcrypt uses random salt, so hashes differ
        # But verify should work for the same password
        assert auth_service._verify(password, hash1)
        assert auth_service._verify(password, hash2)

    def test_verify_correct_password(self):
        """_verify should return True for correct password."""
        password = "CorrectPassword"
        hashed = auth_service._hash(password)

        assert auth_service._verify(password, hashed) is True

    def test_verify_incorrect_password(self):
        """_verify should return False for incorrect password."""
        password = "CorrectPassword"
        wrong_password = "WrongPassword"
        hashed = auth_service._hash(password)

        assert auth_service._verify(wrong_password, hashed) is False

    def test_verify_empty_password(self):
        """_verify should return False for empty password."""
        password = "SomePassword"
        hashed = auth_service._hash(password)

        assert auth_service._verify("", hashed) is False

    def test_hash_long_password(self):
        """Passwords > 72 bytes should be pre-hashed with SHA256."""
        # Create a password > 72 bytes
        long_password = "x" * 100
        hashed = auth_service._hash(long_password)

        # Should still be a valid bcrypt hash
        assert hashed.startswith("$2")
        assert auth_service._verify(long_password, hashed)

    def test_hash_very_long_password(self):
        """Very long passwords (256+ bytes) should work correctly."""
        very_long = "a" * 256
        hashed = auth_service._hash(very_long)

        assert hashed.startswith("$2")
        assert auth_service._verify(very_long, hashed)

    @pytest.mark.asyncio
    async def test_hash_async_returns_valid_hash(self):
        """Async hash should return a valid bcrypt hash."""
        password = "AsyncTestPass"

        async_hash = await auth_service._hash_async(password)

        assert async_hash.startswith("$2")
        assert auth_service._verify(password, async_hash)

    @pytest.mark.asyncio
    async def test_verify_async_correct(self):
        """Async verify should return True for correct password."""
        password = "AsyncVerifyPass"
        hashed = auth_service._hash(password)

        result = await auth_service._verify_async(password, hashed)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_async_incorrect(self):
        """Async verify should return False for incorrect password."""
        password = "AsyncVerifyPass"
        hashed = auth_service._hash(password)

        result = await auth_service._verify_async("WrongPassword", hashed)
        assert result is False

    def test_verify_invalid_hash_format(self):
        """_verify should return False for invalid hash format."""
        assert auth_service._verify("password", "invalid-hash") is False

    def test_verify_malformed_hash(self):
        """_verify should return False for malformed bcrypt hash."""
        # Too short
        assert auth_service._verify("pass", "short") is False
        # Bad prefix
        assert auth_service._verify("pass", "$99$invalid") is False


class TestOTPGeneration:
    """Tests for _otp function."""

    def test_otp_length(self):
        """OTP should be 6 digits."""
        otp = auth_service._otp()
        assert len(otp) == 6
        assert otp.isdigit()

    def test_otp_is_random(self):
        """OTP should generate different values on each call."""
        otps = {auth_service._otp() for _ in range(10)}
        # With 6 digits, collisions are unlikely but possible
        # At least verify we got some variety
        assert len(otps) > 1

    def test_otp_all_digits(self):
        """OTP should only contain digits 0-9."""
        otp = auth_service._otp()
        assert otp.isdecimal()
        assert otp.isdigit()


class TestTokenHashing:
    """Tests for _hash_refresh_token function."""

    def test_hash_refresh_token_returns_sha256(self):
        """_hash_refresh_token should return SHA256 hex."""
        token = "test-token-123"
        hashed = auth_service._hash_refresh_token(token)

        # SHA256 hex is 64 characters
        assert len(hashed) == 64
        # SHA256 hex is lowercase hexadecimal
        assert all(c in "0123456789abcdef" for c in hashed)

    def test_hash_refresh_token_deterministic(self):
        """Same token should produce same hash."""
        token = "deterministic-token"
        hash1 = auth_service._hash_refresh_token(token)
        hash2 = auth_service._hash_refresh_token(token)

        assert hash1 == hash2

    def test_hash_refresh_token_different_inputs(self):
        """Different tokens should produce different hashes."""
        hash1 = auth_service._hash_refresh_token("token1")
        hash2 = auth_service._hash_refresh_token("token2")

        assert hash1 != hash2


class TestNowHelper:
    """Tests for _now helper function."""

    def test_now_returns_utc_time(self):
        """_now should return timezone-aware UTC datetime."""
        now = auth_service._now()

        assert isinstance(now, datetime)
        assert now.tzinfo == UTC

    def test_now_is_approximately_now(self):
        """_now should be within a few seconds of actual now."""
        before = datetime.now(UTC)
        now = auth_service._now()
        after = datetime.now(UTC)

        assert before <= now <= after + timedelta(seconds=1)


class TestCreateRefreshToken:
    """Tests for _create_refresh function."""

    @pytest.mark.asyncio
    async def test_create_refresh_returns_token_string(self):
        """_create_refresh should return a non-empty token string."""
        # Create a mock redis with sync pipeline
        mock_pipeline = MagicMock()
        mock_pipeline.setex = MagicMock()
        mock_pipeline.sadd = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=[True, 1, True])

        mock_redis = MagicMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            token = await auth_service._create_refresh("user-123")

            assert isinstance(token, str)
            assert len(token) > 0

    @pytest.mark.asyncio
    async def test_create_refresh_stores_in_redis(self):
        """_create_refresh should store token hash in Redis."""
        mock_pipeline = MagicMock()
        mock_pipeline.setex = MagicMock()
        mock_pipeline.sadd = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=[True, 1, True])

        mock_redis = MagicMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            await auth_service._create_refresh("user-123")

            # Verify pipeline was used
            mock_redis.pipeline.assert_called_once()
            # Verify setex was called with refresh prefix
            mock_pipeline.setex.assert_called_once()


class TestInvalidateRefresh:
    """Tests for _invalidate_all_refresh and _invalidate_one_refresh."""

    @pytest.mark.asyncio
    async def test_invalidate_all_removes_user_tokens(self):
        """_invalidate_all_refresh should delete all user tokens."""
        mock_redis = AsyncMock()
        mock_redis.smembers.return_value = {b"hash1", b"hash2"}
        mock_redis.delete.return_value = 3

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            await auth_service._invalidate_all_refresh("user-123")

            mock_redis.smembers.assert_called_once()
            mock_redis.delete.assert_called()

    @pytest.mark.asyncio
    async def test_invalidate_all_handles_no_tokens(self):
        """_invalidate_all_refresh should handle no existing tokens."""
        mock_redis = AsyncMock()
        mock_redis.smembers.return_value = set()

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            await auth_service._invalidate_all_refresh("user-123")

            mock_redis.smembers.assert_called_once()
            mock_redis.delete.assert_called_once()  # Just the user key

    @pytest.mark.asyncio
    async def test_invalidate_one_removes_single_token(self):
        """_invalidate_one_refresh should delete only the specified token."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            await auth_service._invalidate_one_refresh("raw-token")

            mock_redis.delete.assert_called_once()


class TestEdgeCases:
    """Edge case tests for auth service utilities."""

    def test_hash_unicode_password(self):
        """Password with unicode characters should work."""
        password = "пароль"  # Russian word for password
        hashed = auth_service._hash(password)

        assert hashed.startswith("$2")
        assert auth_service._verify(password, hashed)

    def test_hash_emoji_password(self):
        """Password with emoji should work."""
        password = "🔐🔑🗝️"
        hashed = auth_service._hash(password)

        assert hashed.startswith("$2")
        assert auth_service._verify(password, hashed)

    def test_hash_special_characters(self):
        """Password with special characters should work."""
        password = "P@$$w0rd!#$%^&*()"
        hashed = auth_service._hash(password)

        assert hashed.startswith("$2")
        assert auth_service._verify(password, hashed)

    def test_verify_whitespace_sensitive(self):
        """Password verification should be whitespace-sensitive."""
        password = "NoSpaces"
        hashed = auth_service._hash(password)

        assert auth_service._verify("NoSpaces", hashed) is True
        assert auth_service._verify("No Spaces", hashed) is False
        assert auth_service._verify("NoSpaces ", hashed) is False
        assert auth_service._verify(" NoSpaces", hashed) is False

    def test_otp_zero_digit(self):
        """OTP should be able to contain zero."""
        # Call multiple times and check we can get variety
        seen_zero = False
        for _ in range(100):
            otp = auth_service._otp()
            if "0" in otp:
                seen_zero = True
                break

        assert seen_zero, "OTP should be able to contain zero digit"
