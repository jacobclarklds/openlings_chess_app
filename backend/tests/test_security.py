"""
Tests for security functions
"""
import pytest
from datetime import timedelta
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_password_hash_creates_different_hash(self):
        """Test that hashing the same password twice produces different hashes"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2  # bcrypt uses salt, so hashes differ
        assert hash1 != password  # Hash should not equal plain password

    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password("testpassword123", hashed) is False
        assert verify_password("TestPassword123", hashed) is True

    def test_hash_empty_password(self):
        """Test hashing empty password"""
        hashed = get_password_hash("")
        assert hashed != ""
        assert verify_password("", hashed) is True

    def test_hash_long_password(self):
        """Test hashing very long password"""
        long_password = "a" * 1000
        hashed = get_password_hash(long_password)
        assert verify_password(long_password, hashed) is True

    def test_hash_special_characters(self):
        """Test hashing password with special characters"""
        password = "!@#$%^&*()_+-=[]{}|;:',.<>?/`~"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_hash_unicode_password(self):
        """Test hashing password with unicode characters"""
        password = "пароль密码🔐"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test JWT token creation and decoding"""

    def test_create_token_basic(self):
        """Test creating a basic JWT token"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token_basic(self):
        """Test decoding a JWT token"""
        email = "test@example.com"
        data = {"sub": email}
        token = create_access_token(data)

        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == email

    def test_token_includes_expiration(self):
        """Test that token includes expiration time"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)

        decoded = decode_access_token(token)
        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)

    def test_token_with_custom_expiration(self):
        """Test creating token with custom expiration"""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta=expires_delta)

        decoded = decode_access_token(token)
        assert decoded is not None
        assert "exp" in decoded

    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None"""
        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)
        assert decoded is None

    def test_decode_expired_token(self):
        """Test decoding expired token returns None"""
        data = {"sub": "test@example.com"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires_delta)

        decoded = decode_access_token(token)
        assert decoded is None

    def test_decode_tampered_token(self):
        """Test decoding tampered token returns None"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)

        # Tamper with token
        parts = token.split('.')
        if len(parts) == 3:
            tampered_token = parts[0] + '.tampered.' + parts[2]
            decoded = decode_access_token(tampered_token)
            assert decoded is None

    def test_token_with_additional_data(self):
        """Test creating token with additional data"""
        data = {
            "sub": "test@example.com",
            "role": "admin",
            "user_id": 123,
        }
        token = create_access_token(data)

        decoded = decode_access_token(token)
        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "admin"
        assert decoded["user_id"] == 123

    def test_token_with_empty_data(self):
        """Test creating token with minimal data"""
        data = {}
        token = create_access_token(data)

        decoded = decode_access_token(token)
        assert decoded is not None
        assert "exp" in decoded  # Should still have expiration

    def test_multiple_tokens_different(self):
        """Test that multiple tokens for same user are different"""
        data = {"sub": "test@example.com"}
        token1 = create_access_token(data)
        token2 = create_access_token(data)

        # Tokens should be different due to different exp times
        assert token1 != token2

        # But both should decode to same email
        decoded1 = decode_access_token(token1)
        decoded2 = decode_access_token(token2)
        assert decoded1["sub"] == decoded2["sub"]


class TestSecurityEdgeCases:
    """Test edge cases in security functions"""

    def test_verify_password_with_none(self):
        """Test that verify_password handles None gracefully"""
        password = "test123"
        hashed = get_password_hash(password)

        # This should not crash
        try:
            result = verify_password(None, hashed)
            # If it doesn't crash, it should return False
            assert result is False
        except (TypeError, AttributeError):
            # It's okay if it raises an exception for None
            pass

    def test_decode_none_token(self):
        """Test decoding None token"""
        # Should handle None gracefully
        try:
            decoded = decode_access_token(None)
            assert decoded is None
        except (TypeError, AttributeError):
            # It's okay if it raises an exception
            pass

    def test_decode_empty_string_token(self):
        """Test decoding empty string token"""
        decoded = decode_access_token("")
        assert decoded is None

    def test_token_roundtrip(self):
        """Test creating and decoding token multiple times"""
        for i in range(10):
            data = {"sub": f"test{i}@example.com", "iteration": i}
            token = create_access_token(data)
            decoded = decode_access_token(token)

            assert decoded is not None
            assert decoded["sub"] == f"test{i}@example.com"
            assert decoded["iteration"] == i


class TestPasswordStrength:
    """Test password strength requirements"""

    def test_short_password_can_be_hashed(self):
        """Test that short passwords can be hashed (validation is in endpoint)"""
        # Note: Password validation happens in the endpoint, not in security.py
        short_password = "123"
        hashed = get_password_hash(short_password)
        assert verify_password(short_password, hashed) is True

    def test_common_passwords_can_be_hashed(self):
        """Test that common passwords can be hashed"""
        common_passwords = ["password", "123456", "qwerty", "admin"]
        for password in common_passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
