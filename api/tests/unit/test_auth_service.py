"""
Unit tests for AuthService
Tests authentication service methods in isolation
"""
import pytest
import uuid
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.auth_service import AuthService
from schemas.pydantic_schemas import UserLogin, UserSignup, UserAuthResponse
from models.db_models import User


class TestAuthServiceAuthentication:
    """Test AuthService authentication methods"""
    
    @patch('services.auth_service.verify_password')
    @patch('services.auth_service.create_access_token')
    def test_authenticate_user_success(self, mock_create_token, mock_verify_password):
        """Test successful user authentication"""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.id = uuid.uuid4()
        mock_user.email = "test@example.com"
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"
        mock_user.city = "Test City"
        mock_user.country = "Test Country"
        mock_user.password = "hashed_password"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_verify_password.return_value = True
        mock_create_token.return_value = "jwt_token_123"
        
        user_credentials = UserLogin(
            email="test@example.com",
            password="correct_password"
        )
        
        # Call method
        result = AuthService.authenticate_user(mock_db, user_credentials)
        
        # Assertions
        assert isinstance(result, UserAuthResponse)
        assert result.access_token == "jwt_token_123"
        assert result.token_type == "bearer"
        assert result.user.email == "test@example.com"
        
        # Verify mocks were called correctly
        mock_db.query.assert_called_once()
        mock_verify_password.assert_called_once_with("correct_password", "hashed_password")
        mock_create_token.assert_called_once()
    
    def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        user_credentials = UserLogin(
            email="nonexistent@example.com",
            password="any_password"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.authenticate_user(mock_db, user_credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in exc_info.value.detail
    
    @patch('services.auth_service.verify_password')
    def test_authenticate_user_wrong_password(self, mock_verify_password):
        """Test authentication with wrong password"""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.email = "test@example.com"
        mock_user.password = "hashed_password"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_verify_password.return_value = False
        
        user_credentials = UserLogin(
            email="test@example.com",
            password="wrong_password"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.authenticate_user(mock_db, user_credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in exc_info.value.detail
        mock_verify_password.assert_called_once_with("wrong_password", "hashed_password")


class TestAuthServiceRegistration:
    """Test AuthService registration methods"""
    
    @patch('services.auth_service.get_password_hash')
    @patch('services.auth_service.create_access_token')
    def test_register_user_success(self, mock_create_token, mock_get_hash):
        """Test successful user registration"""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None  # User doesn't exist
        
        # Mock the created user that gets added to database
        mock_created_user = MagicMock(spec=User)
        mock_created_user.id = uuid.uuid4()
        mock_created_user.email = "newuser@example.com"
        mock_created_user.first_name = "Jane"
        mock_created_user.last_name = "Smith"
        mock_created_user.city = "New York"
        mock_created_user.country = "USA"
        
        # Mock db.refresh to set the user attributes
        def mock_refresh(user):
            for attr, value in vars(mock_created_user).items():
                setattr(user, attr, value)
        
        mock_db.refresh.side_effect = mock_refresh
        
        mock_get_hash.return_value = "hashed_password"
        mock_create_token.return_value = "jwt_token_456"
        
        user_data = UserSignup(
            email="newuser@example.com",
            first_name="Jane",
            last_name="Smith",
            password1="SecurePass123",
            password2="SecurePass123",
            city="New York",
            country="USA"
        )
        
        # Call method
        result = AuthService.register_user(mock_db, user_data)
        
        # Assertions
        assert isinstance(result, UserAuthResponse)
        assert result.access_token == "jwt_token_456"
        assert result.token_type == "bearer"
        assert result.user.email == "newuser@example.com"
        assert result.user.first_name == "Jane"
        assert result.user.last_name == "Smith"
        assert result.user.city == "New York"
        assert result.user.country == "USA"
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verify password hashing
        mock_get_hash.assert_called_once_with("SecurePass123")
    
    def test_register_user_email_already_exists(self):
        """Test registration with existing email"""
        mock_db = MagicMock(spec=Session)
        mock_existing_user = MagicMock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_user
        
        user_data = UserSignup(
            email="existing@example.com",
            first_name="John",
            last_name="Doe",
            password1="SecurePass123",
            password2="SecurePass123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.register_user(mock_db, user_data)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail
    
    @patch('services.auth_service.get_password_hash')
    def test_register_user_minimal_data(self, mock_get_hash):
        """Test registration with minimal required data"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock the created user
        mock_created_user = MagicMock(spec=User)
        mock_created_user.id = uuid.uuid4()
        mock_created_user.email = "minimal@example.com"
        mock_created_user.first_name = "Min"
        mock_created_user.last_name = "User"
        mock_created_user.city = None
        mock_created_user.country = None
        
        def mock_refresh(user):
            for attr, value in vars(mock_created_user).items():
                setattr(user, attr, value)
        
        mock_db.refresh.side_effect = mock_refresh
        mock_get_hash.return_value = "hashed_password"
        
        user_data = UserSignup(
            email="minimal@example.com",
            first_name="Min",
            last_name="User",
            password1="SecurePass123",
            password2="SecurePass123"
            # No city or country
        )
        
        with patch('services.auth_service.create_access_token') as mock_create_token:
            mock_create_token.return_value = "jwt_token_789"
            
            result = AuthService.register_user(mock_db, user_data)
            
            assert result.user.email == "minimal@example.com"
            assert result.user.city is None
            assert result.user.country is None
    
    @patch('services.auth_service.get_password_hash')
    def test_register_user_database_error(self, mock_get_hash):
        """Test registration with database error"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit.side_effect = Exception("Database error")
        mock_get_hash.return_value = "hashed_password"
        
        user_data = UserSignup(
            email="error@example.com",
            first_name="Error",
            last_name="User",
            password1="SecurePass123",
            password2="SecurePass123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.register_user(mock_db, user_data)
        
        assert exc_info.value.status_code == 500
        assert "Registration service error" in exc_info.value.detail


class TestAuthServiceUserLookup:
    """Test AuthService user lookup methods"""
    
    def test_get_user_by_email_success(self):
        """Test successful user lookup by email"""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.email = "found@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = AuthService.get_user_by_email(mock_db, "found@example.com")
        
        assert result == mock_user
        mock_db.query.assert_called_once()
    
    def test_get_user_by_email_not_found(self):
        """Test user lookup when user doesn't exist"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = AuthService.get_user_by_email(mock_db, "notfound@example.com")
        
        assert result is None
        mock_db.query.assert_called_once()
    
    def test_get_user_by_id_success(self):
        """Test successful user lookup by ID"""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        user_id = str(uuid.uuid4())
        mock_user.id = user_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = AuthService.get_user_by_id(mock_db, user_id)
        
        assert result == mock_user
        mock_db.query.assert_called_once()


class TestAuthServiceCredentialValidation:
    """Test AuthService credential validation methods"""
    
    def test_validate_user_credentials_valid_email(self):
        """Test credential validation with valid email"""
        result = AuthService.validate_user_credentials("valid@example.com", "SecurePass123")
        
        assert isinstance(result, dict)
        assert "email_valid" in result
        assert "password_valid" in result
        assert result["email_valid"] is True
    
    def test_validate_user_credentials_invalid_email(self):
        """Test credential validation with invalid email"""
        result = AuthService.validate_user_credentials("invalid-email", "SecurePass123")
        
        assert isinstance(result, dict)
        assert "email_valid" in result
        assert "password_valid" in result
        assert result["email_valid"] is False
    
    def test_validate_user_credentials_weak_password(self):
        """Test credential validation with weak password"""
        result = AuthService.validate_user_credentials("valid@example.com", "weak")
        
        assert isinstance(result, dict)
        assert "email_valid" in result
        assert "password_valid" in result
        assert result["password_valid"] is False
    
    def test_validate_user_credentials_empty_credentials(self):
        """Test credential validation with empty credentials"""
        result = AuthService.validate_user_credentials("", "")
        
        assert isinstance(result, dict)
        assert result["email_valid"] is False
        assert result["password_valid"] is False


class TestAuthServiceIntegration:
    """Test AuthService integration scenarios"""
    
    @patch('services.auth_service.verify_password')
    @patch('services.auth_service.get_password_hash')
    @patch('services.auth_service.create_access_token')
    def test_register_then_authenticate_flow(self, mock_create_token, mock_get_hash, mock_verify_password):
        """Test complete register then authenticate flow"""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        mock_get_hash.return_value = "hashed_password"
        mock_verify_password.return_value = True
        mock_create_token.return_value = "flow_token_123"
        
        # Mock the created user
        mock_created_user = MagicMock(spec=User)
        mock_created_user.id = uuid.uuid4()
        mock_created_user.email = "flow@example.com"
        mock_created_user.first_name = "Flow"
        mock_created_user.last_name = "User"
        mock_created_user.city = None
        mock_created_user.country = None
        mock_created_user.password = "hashed_password"
        
        def mock_refresh(user):
            for attr, value in vars(mock_created_user).items():
                setattr(user, attr, value)
        
        mock_db.refresh.side_effect = mock_refresh
        
        # Registration
        mock_db.query.return_value.filter.return_value.first.return_value = None  # User doesn't exist
        
        signup_data = UserSignup(
            email="flow@example.com",
            first_name="Flow",
            last_name="User",
            password1="FlowPass123",
            password2="FlowPass123"
        )
        
        register_result = AuthService.register_user(mock_db, signup_data)
        
        # Simulate user now exists in database for authentication
        mock_db.query.return_value.filter.return_value.first.return_value = mock_created_user
        
        # Authentication
        login_data = UserLogin(
            email="flow@example.com",
            password="FlowPass123"
        )
        
        auth_result = AuthService.authenticate_user(mock_db, login_data)
        
        # Assertions
        assert register_result.user.email == "flow@example.com"
        assert auth_result.user.email == "flow@example.com"
        assert register_result.access_token == "flow_token_123"
        assert auth_result.access_token == "flow_token_123"
    
    @patch('services.auth_service.logger')
    def test_logging_behavior(self, mock_logger):
        """Test that service methods log appropriately"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        user_credentials = UserLogin(
            email="logging@example.com",
            password="any_password"
        )
        
        with pytest.raises(HTTPException):
            AuthService.authenticate_user(mock_db, user_credentials)
        
        # Verify warning was logged for non-existent user
        mock_logger.warning.assert_called_once()
        assert "non-existent email" in mock_logger.warning.call_args[0][0]
    
    def test_error_handling_consistency(self):
        """Test that all authentication errors return consistent format"""
        mock_db = MagicMock(spec=Session)
        
        # Test cases that should all return 401 with "Invalid credentials"
        test_cases = [
            # Non-existent user
            (None, "any_password"),
            # Wrong password (mocked)
        ]
        
        for user_mock, password in test_cases:
            mock_db.query.return_value.filter.return_value.first.return_value = user_mock
            
            user_credentials = UserLogin(
                email="test@example.com",
                password=password
            )
            
            with pytest.raises(HTTPException) as exc_info:
                AuthService.authenticate_user(mock_db, user_credentials)
            
            assert exc_info.value.status_code == 401
            assert "Invalid credentials" in exc_info.value.detail
