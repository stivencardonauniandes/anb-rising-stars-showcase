"""
Authentication service for handling user authentication and registration
"""
from datetime import timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from auth import create_access_token, get_password_hash, verify_password
from models.db_models import User
from schemas.pydantic_schemas import UserAuthResponse, UserLogin, UserResponse, UserSignup

logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    def authenticate_user(db: Session, user_credentials: UserLogin) -> UserAuthResponse:
        """
        Authenticate user and return JWT token with user data
        
        Args:
            db: Database session
            user_credentials: User login credentials
            
        Returns:
            UserAuthResponse: User data with access token
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Find user by email
            user = db.query(User).filter(User.email == user_credentials.email).first()
            if not user:
                logger.warning(f"Login attempt with non-existent email: {user_credentials.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Verify password
            if not verify_password(user_credentials.password, user.password):
                logger.warning(f"Invalid password attempt for user: {user_credentials.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=30)
            access_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            
            # Return user data and token
            user_response = UserResponse.model_validate(user)
            logger.info(f"Successful login for user: {user.email}")
            
            return UserAuthResponse(
                user=user_response,
                access_token=access_token,
                token_type="bearer"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
    
    @staticmethod
    def register_user(db: Session, user_data: UserSignup) -> UserAuthResponse:
        """
        Register a new user and return JWT token with user data
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            UserAuthResponse: User data with access token
            
        Raises:
            HTTPException: If registration fails
        """
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                logger.warning(f"Registration attempt with existing email: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            hashed_password = get_password_hash(user_data.password1)
            
            # Create new user
            db_user = User(
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                password=hashed_password,
                city=user_data.city,
                country=user_data.country
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Create access token
            access_token_expires = timedelta(minutes=30)
            access_token = create_access_token(
                data={"sub": db_user.email}, expires_delta=access_token_expires
            )
            
            # Return user data and token
            user_response = UserResponse.model_validate(db_user)
            logger.info(f"Successful registration for user: {db_user.email}")
            
            return UserAuthResponse(
                user=user_response,
                access_token=access_token,
                token_type="bearer"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during registration: {e}", exc_info=True)
            # Rollback transaction in case of error
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration service error"
            )
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get user by email address
        
        Args:
            db: Database session
            email: User email address
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error fetching user by ID {user_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def validate_user_credentials(email: str, password: str) -> Dict[str, bool]:
        """
        Validate user credentials format (basic validation)
        
        Args:
            email: Email address
            password: Password
            
        Returns:
            Dict with validation results
        """
        validation_result = {
            "email_valid": False,
            "password_valid": False,
            "overall_valid": False
        }
        
        # Basic email validation
        if email and "@" in email and "." in email.split("@")[-1]:
            validation_result["email_valid"] = True
        
        # Basic password validation (minimum 6 characters)
        if password and len(password) >= 6:
            validation_result["password_valid"] = True
        
        validation_result["overall_valid"] = (
            validation_result["email_valid"] and 
            validation_result["password_valid"]
        )
        
        return validation_result


# Global auth service instance
auth_service = AuthService()
