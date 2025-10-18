"""
Tests for authentication endpoints
"""
import time
from models.db_models import User
from tests.test_database import client, db_session, test_user

# Test constants to avoid SonarQube hardcoded credential warnings
TEST_PASSWORD = "testpass123"  # Standard test password
TEST_SECURE_PASSWORD = "SecurePass123"  # Strong test password
TEST_INTEGRATION_PASSWORD = "IntegrationPass123"  # Integration test password
TEST_CONSISTENT_PASSWORD = "ConsistentPass123"  # Consistency test password
TEST_INVALID_PASSWORD = "wrongpassword"  # Invalid password for negative tests
TEST_GENERIC_PASSWORD = "anypassword"  # Generic password for tests
TEST_SOME_PASSWORD = "somepassword"  # Generic password variant
TEST_DIFFERENT_PASSWORD = "DifferentPass123"  # Different password for mismatch tests
TEST_WEAK_PASSWORD = "weak"  # Weak password for validation tests


class TestSignupEndpoint:
    """Tests for POST /api/auth/signup"""
    
    def test_signup_success(self, db_session):
        """Test successful user registration"""
        signup_data = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": TEST_SECURE_PASSWORD,
            "password2": TEST_SECURE_PASSWORD,
            "city": "New City",
            "country": "New Country"
        }
        
        response = client.post("/api/auth/signup", json=signup_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check response structure
        assert "user" in data
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Check user data
        user_data = data["user"]
        assert user_data["email"] == "newuser@example.com"
        assert user_data["first_name"] == "New"
        assert user_data["last_name"] == "User"
        assert user_data["city"] == "New City"
        assert user_data["country"] == "New Country"
        assert "id" in user_data
        
        # Verify user was created in database
        db_user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert db_user is not None
        assert db_user.first_name == "New"
        assert db_user.last_name == "User"
    
    def test_signup_duplicate_email(self, db_session, test_user):
        """Test signup with existing email fails"""
        signup_data = {
            "email": test_user.email,  # Use existing user's email
            "first_name": "Duplicate",
            "last_name": "User",
            "password1": TEST_SECURE_PASSWORD,
            "password2": TEST_SECURE_PASSWORD,
            "city": "Test City",
            "country": "Test Country"
        }
        
        response = client.post("/api/auth/signup", json=signup_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_signup_password_mismatch(self, db_session):
        """Test signup with mismatched passwords fails"""
        signup_data = {
            "email": "mismatch@example.com",
            "first_name": "Mismatch",
            "last_name": "User",
            "password1": TEST_SECURE_PASSWORD,
            "password2": TEST_DIFFERENT_PASSWORD,  # Intentionally different for mismatch test
            "city": "Test City",
            "country": "Test Country"
        }
        
        response = client.post("/api/auth/signup", json=signup_data)
        
        assert response.status_code == 422
        # Should fail validation due to password mismatch
    
    def test_signup_weak_password(self, db_session):
        """Test signup with weak password fails validation"""
        signup_data = {
            "email": "weak@example.com",
            "first_name": "Weak",
            "last_name": "User",
            "password1": TEST_WEAK_PASSWORD,  # Too short, no uppercase, no numbers
            "password2": TEST_WEAK_PASSWORD,
            "city": "Test City",
            "country": "Test Country"
        }
        
        response = client.post("/api/auth/signup", json=signup_data)
        
        assert response.status_code == 422
        # Should fail validation due to weak password
    
    def test_signup_invalid_email(self, db_session):
        """Test signup with invalid email format fails"""
        signup_data = {
            "email": "invalid-email",  # Invalid email format
            "first_name": "Invalid",
            "last_name": "User",
            "password1": TEST_SECURE_PASSWORD,
            "password2": TEST_SECURE_PASSWORD,
            "city": "Test City",
            "country": "Test Country"
        }
        
        response = client.post("/api/auth/signup", json=signup_data)
        
        assert response.status_code == 422
        # Should fail validation due to invalid email
    
    def test_signup_missing_required_fields(self, db_session):
        """Test signup with missing required fields fails"""
        signup_data = {
            "email": "missing@example.com",
            # Missing first_name, last_name, passwords
        }
        
        response = client.post("/api/auth/signup", json=signup_data)
        
        assert response.status_code == 422
    
    def test_signup_optional_fields_null(self, db_session):
        """Test signup with optional fields as null succeeds"""
        signup_data = {
            "email": "optional@example.com",
            "first_name": "Optional",
            "last_name": "User",
            "password1": TEST_SECURE_PASSWORD,
            "password2": TEST_SECURE_PASSWORD,
            "city": None,
            "country": None
        }
        
        response = client.post("/api/auth/signup", json=signup_data)
        
        assert response.status_code == 201
        data = response.json()
        
        user_data = data["user"]
        assert user_data["city"] is None
        assert user_data["country"] is None


class TestLoginEndpoint:
    """Tests for POST /api/auth/login"""
    
    def test_login_success(self, db_session, test_user):
        """Test successful user login"""
        login_data = {
            "email": test_user.email,
            "password": TEST_PASSWORD  # This is the raw password used in test_user fixture
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "user" in data
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Check user data
        user_data = data["user"]
        assert user_data["email"] == test_user.email
        assert user_data["first_name"] == test_user.first_name
        assert user_data["last_name"] == test_user.last_name
        assert user_data["id"] == str(test_user.id)
        
        # Check token is present and not empty
        assert data["access_token"]
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_email(self, db_session):
        """Test login with non-existent email fails"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": TEST_GENERIC_PASSWORD
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_invalid_password(self, db_session, test_user):
        """Test login with wrong password fails"""
        login_data = {
            "email": test_user.email,
            "password": TEST_INVALID_PASSWORD
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_empty_email(self, db_session):
        """Test login with empty email fails"""
        login_data = {
            "email": "",
            "password": TEST_SOME_PASSWORD
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 422
    
    def test_login_empty_password(self, db_session, test_user):
        """Test login with empty password fails"""
        login_data = {
            "email": test_user.email,
            "password": ""
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("Password cannot be empty" in str(error) for error in error_detail)
    
    def test_login_whitespace_only_fields(self, db_session):
        """Test login with whitespace-only fields fails"""
        # Test whitespace-only email
        login_data1 = {
            "email": "   ",
            "password": TEST_SOME_PASSWORD
        }
        
        response1 = client.post("/api/auth/login", json=login_data1)
        assert response1.status_code == 422
        
        # Test whitespace-only password
        login_data2 = {
            "email": "test@example.com",
            "password": "   "
        }
        
        response2 = client.post("/api/auth/login", json=login_data2)
        assert response2.status_code == 422
    
    def test_login_invalid_email_format(self, db_session):
        """Test login with invalid email format fails"""
        login_data = {
            "email": "invalid-email-format",
            "password": TEST_SOME_PASSWORD
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 422
        # Should fail validation due to invalid email format
    
    def test_login_missing_fields(self, db_session):
        """Test login with missing fields fails"""
        # Missing password
        response1 = client.post("/api/auth/login", json={"email": "test@example.com"})
        assert response1.status_code == 422
        
        # Missing email
        response2 = client.post("/api/auth/login", json={"password": TEST_SOME_PASSWORD})
        assert response2.status_code == 422
        
        # Empty request body
        response3 = client.post("/api/auth/login", json={})
        assert response3.status_code == 422
    
    def test_login_case_sensitive_email(self, db_session, test_user):
        """Test login with different case email"""
        login_data = {
            "email": test_user.email.upper(),  # Different case
            "password": TEST_PASSWORD
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        # This should fail since email lookup is case-sensitive
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]


class TestAuthEndpointsIntegration:
    """Integration tests for auth endpoints"""
    
    def test_signup_then_login_flow(self, db_session):
        """Test complete signup then login flow"""
        # First, signup a new user
        signup_data = {
            "email": "integration@example.com",
            "first_name": "Integration",
            "last_name": "Test",
            "password1": TEST_INTEGRATION_PASSWORD,
            "password2": TEST_INTEGRATION_PASSWORD,
            "city": "Integration City",
            "country": "Integration Country"
        }
        
        signup_response = client.post("/api/auth/signup", json=signup_data)
        assert signup_response.status_code == 201
        
        signup_data_response = signup_response.json()
        assert "access_token" in signup_data_response
        
        # Then, login with the same credentials
        login_data = {
            "email": "integration@example.com",
            "password": TEST_INTEGRATION_PASSWORD
        }
        
        login_response = client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        login_data_response = login_response.json()
        assert "access_token" in login_data_response
        
        # Both responses should have the same user data
        assert signup_data_response["user"]["email"] == login_data_response["user"]["email"]
        assert signup_data_response["user"]["first_name"] == login_data_response["user"]["first_name"]
        assert signup_data_response["user"]["last_name"] == login_data_response["user"]["last_name"]
    
    def test_multiple_logins_same_user(self, db_session, test_user):
        """Test multiple login attempts for the same user"""
        login_data = {
            "email": test_user.email,
            "password": TEST_PASSWORD
        }
        
        # First login
        response1 = client.post("/api/auth/login", json=login_data)
        assert response1.status_code == 200
        data1 = response1.json()
        assert "access_token" in data1
        assert "user" in data1
        assert data1["token_type"] == "bearer"
        assert len(data1["access_token"]) > 0
        
        # Second login should also succeed
        response2 = client.post("/api/auth/login", json=login_data)
        assert response2.status_code == 200
        data2 = response2.json()
        assert "access_token" in data2
        assert "user" in data2
        assert data2["token_type"] == "bearer"
        assert len(data2["access_token"]) > 0
        
        # Both logins should return the same user data
        assert data1["user"]["email"] == data2["user"]["email"]
        assert data1["user"]["id"] == data2["user"]["id"]
    
    def test_login_tokens_with_time_difference(self, db_session, test_user):
        """Test that tokens are different when created at different times"""
        
        login_data = {
            "email": test_user.email,
            "password": TEST_PASSWORD
        }
        
        # First login
        response1 = client.post("/api/auth/login", json=login_data)
        assert response1.status_code == 200
        token1 = response1.json()["access_token"]
        
        # Wait to ensure different timestamp
        time.sleep(1)
        
        # Second login
        response2 = client.post("/api/auth/login", json=login_data)
        assert response2.status_code == 200
        token2 = response2.json()["access_token"]
        
        # Tokens should be different due to different expiration times
        assert token1 != token2
    
    def test_auth_endpoints_return_consistent_user_data(self, db_session):
        """Test that signup and login return consistent user data format"""
        # Signup
        signup_data = {
            "email": "consistent@example.com",
            "first_name": "Consistent",
            "last_name": "User",
            "password1": TEST_CONSISTENT_PASSWORD,
            "password2": TEST_CONSISTENT_PASSWORD,
            "city": "Consistent City",
            "country": "Consistent Country"
        }
        
        signup_response = client.post("/api/auth/signup", json=signup_data)
        signup_user = signup_response.json()["user"]
        
        # Login
        login_data = {
            "email": "consistent@example.com",
            "password": TEST_CONSISTENT_PASSWORD
        }
        
        login_response = client.post("/api/auth/login", json=login_data)
        login_user = login_response.json()["user"]
        
        # User data structure should be identical
        assert set(signup_user.keys()) == set(login_user.keys())
        
        # User data values should be identical
        for key in signup_user.keys():
            assert signup_user[key] == login_user[key]
