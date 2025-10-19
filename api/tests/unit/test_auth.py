"""
Unit tests for authentication utilities
Tests password hashing, JWT token creation/validation, and authentication functions
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from jose import JWTError

import auth
from auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    get_user_from_token
)


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_get_password_hash_returns_string(self):
        """Test that password hashing returns a string"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Should be different from original
    
    def test_get_password_hash_different_for_same_password(self):
        """Test that same password produces different hashes (due to salt)"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
    
    def test_verify_password_correct_password(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        result = verify_password(password, hashed)
        assert result is True
    
    def test_verify_password_incorrect_password(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        result = verify_password(wrong_password, hashed)
        assert result is False
    
    def test_verify_password_empty_password(self):
        """Test password verification with empty password"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        result = verify_password("", hashed)
        assert result is False
    
    def test_verify_password_empty_hash(self):
        """Test password verification with empty hash"""
        password = "test_password_123"
        
        # Empty hash should raise an exception or return False
        try:
            result = verify_password(password, "")
            assert result is False
        except Exception:
            # passlib raises exception for invalid hash format
            pass
    
    def test_password_hashing_special_characters(self):
        """Test password hashing with special characters"""
        password = "p@ssw0rd!#$%^&*()"
        hashed = get_password_hash(password)
        
        result = verify_password(password, hashed)
        assert result is True
    
    def test_password_hashing_unicode_characters(self):
        """Test password hashing with unicode characters"""
        password = "contraseña_ñáéíóú"
        hashed = get_password_hash(password)
        
        result = verify_password(password, hashed)
        assert result is True


class TestJWTTokenCreation:
    """Test JWT token creation"""
    
    def test_create_access_token_basic(self):
        """Test basic JWT token creation"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT tokens have dots
    
    def test_create_access_token_with_expiration(self):
        """Test JWT token creation with custom expiration"""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        
        token = create_access_token(data, expires_delta)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_different_data_different_tokens(self):
        """Test that different data produces different tokens"""
        data1 = {"sub": "user1@example.com"}
        data2 = {"sub": "user2@example.com"}
        
        token1 = create_access_token(data1)
        token2 = create_access_token(data2)
        
        assert token1 != token2
    
    def test_create_access_token_with_additional_claims(self):
        """Test JWT token creation with additional claims"""
        data = {
            "sub": "test@example.com",
            "role": "admin",
            "permissions": ["read", "write"]
        }
        
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    @patch('auth.datetime')
    def test_create_access_token_expiration_time(self, mock_datetime):
        """Test that token includes correct expiration time"""
        # Mock current time
        mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=30)
        
        with patch('auth.jwt.encode') as mock_encode:
            create_access_token(data, expires_delta)
            
            # Check that jwt.encode was called with correct expiration
            call_args = mock_encode.call_args[0][0]  # First argument to encode
            expected_exp = mock_now + expires_delta
            assert call_args["exp"] == expected_exp


class TestJWTTokenVerification:
    """Test JWT token verification"""
    
    @patch('auth.jwt.decode')
    def test_verify_token_valid_token(self, mock_decode):
        """Test verification of valid token with mocked decode"""
        mock_decode.return_value = {"sub": "test@example.com", "exp": 1234567890}
        
        # Create mock credentials
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"
        
        from auth import verify_token
        result = verify_token(mock_credentials)
        
        assert result == "test@example.com"
        mock_decode.assert_called_once()
    
    @patch('auth.jwt.decode', side_effect=JWTError("Invalid token"))
    def test_verify_token_invalid_token(self, mock_decode):
        """Test verification of invalid token"""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token"
        
        from auth import verify_token
        with pytest.raises(HTTPException) as exc_info:
            verify_token(mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail
    
    @patch('auth.jwt.decode')
    def test_verify_token_no_sub_claim(self, mock_decode):
        """Test verification when token has no sub claim"""
        mock_decode.return_value = {"user_id": "123", "exp": 1234567890}  # No 'sub'
        
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token_without_sub"
        
        from auth import verify_token
        with pytest.raises(HTTPException) as exc_info:
            verify_token(mock_credentials)
        
        assert exc_info.value.status_code == 401


class TestGetUserFromToken:
    """Test getting user from token"""
    
    def test_get_user_from_token_success(self):
        """Test successful user retrieval from token"""
        # Setup mocks
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Create valid token
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        # Test
        result = get_user_from_token(token, mock_db)
        
        assert result == mock_user
        mock_db.query.assert_called_once()
    
    def test_get_user_from_token_user_not_found(self):
        """Test user retrieval when user doesn't exist"""
        # Setup mocks
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Create valid token
        data = {"sub": "nonexistent@example.com"}
        token = create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            get_user_from_token(token, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail
    
    @patch('auth.jwt.decode', side_effect=JWTError("Invalid token"))
    def test_get_user_from_token_invalid_token(self, mock_decode):
        """Test user retrieval with invalid token"""
        mock_db = MagicMock()
        invalid_token = "invalid.jwt.token"
        
        with pytest.raises(HTTPException) as exc_info:
            get_user_from_token(invalid_token, mock_db)
        
        assert exc_info.value.status_code == 401
    
    @patch('auth.jwt.decode')
    def test_get_user_from_token_no_sub_claim(self, mock_decode):
        """Test user retrieval when token has no 'sub' claim"""
        mock_decode.return_value = {"user_id": "123", "role": "admin"}  # No 'sub' claim
        mock_db = MagicMock()
        
        with pytest.raises(HTTPException) as exc_info:
            get_user_from_token("token", mock_db)
        
        assert exc_info.value.status_code == 401


class TestAuthenticationIntegration:
    """Test authentication integration scenarios"""
    
    def test_full_authentication_flow(self):
        """Test complete authentication flow"""
        # 1. Hash password
        password = "secure_password_123"
        hashed_password = get_password_hash(password)
        
        # 2. Verify password
        assert verify_password(password, hashed_password) is True
        
        # 3. Create token
        user_data = {"sub": "user@example.com"}
        token = create_access_token(user_data)
        
        # 4. Verify token (using direct JWT decode since verify_token needs credentials)
        from jose import jwt
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        assert payload["sub"] == "user@example.com"
    
    def test_authentication_with_wrong_password(self):
        """Test authentication flow with wrong password"""
        # Hash correct password
        correct_password = "correct_password"
        hashed_password = get_password_hash(correct_password)
        
        # Try to verify with wrong password
        wrong_password = "wrong_password"
        assert verify_password(wrong_password, hashed_password) is False
    
    def test_token_lifecycle(self):
        """Test token creation and verification lifecycle"""
        user_email = "lifecycle@example.com"
        
        # Create token
        token = create_access_token({"sub": user_email})
        
        # Verify token multiple times (should work)
        from jose import jwt
        for _ in range(3):
            payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
            assert payload["sub"] == user_email
    
    @patch('auth.SECRET_KEY', 'test-secret-key')
    def test_token_with_different_secret_fails(self):
        """Test that token created with different secret fails verification"""
        # Create token with one secret
        with patch('auth.SECRET_KEY', 'secret1'):
            token = create_access_token({"sub": "test@example.com"})
        
        # Try to verify with different secret
        with patch('auth.SECRET_KEY', 'secret2'):
            from jose import jwt, JWTError
            with pytest.raises(JWTError):
                jwt.decode(token, 'secret2', algorithms=[auth.ALGORITHM])
