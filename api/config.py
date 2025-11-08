"""
Application configuration module
Centralizes all environment variable handling and configuration
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Application configuration class
    All environment variables are loaded and validated here
    """
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/anb_showcase")

    # S3 Configuration
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "anb-rising-stars")
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Nextcloud Configuration
    NEXTCLOUD_URL: str = os.getenv("NEXTCLOUD_URL", "http://nextcloud")
    
    # Performance Testing Configuration
    IS_RUNNING_STRESS_TESTING: bool = os.getenv("IS_RUNNING_STRESS_TESTING", "FALSE").upper() == "TRUE"
    NEXTCLOUD_USERNAME: str = os.getenv("NEXTCLOUD_USERNAME", "worker")
    NEXTCLOUD_PASSWORD: str = os.getenv("NEXTCLOUD_PASSWORD", "super-secret")
    
    # Video Processing Configuration
    VIDEO_MIN_DURATION: int = int(os.getenv("VIDEO_MIN_DURATION", "20"))
    VIDEO_MAX_DURATION: int = int(os.getenv("VIDEO_MAX_DURATION", "60"))
    VIDEO_UPLOAD_TIMEOUT: int = int(os.getenv("VIDEO_UPLOAD_TIMEOUT", "300"))
    
    # Application Configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    @classmethod
    def get_nextcloud_url(cls) -> str:
        """
        Get the appropriate Nextcloud URL based on the environment
        Handles Docker vs local development automatically
        """
        base_url = cls.NEXTCLOUD_URL
        
        # Check for explicit local development URL override
        local_url = os.getenv("NEXTCLOUD_LOCAL_URL")
        if local_url:
            return local_url
        
        # Auto-detect environment if using default Docker service name
        if base_url == "http://nextcloud":
            try:
                import socket
                socket.gethostbyname("nextcloud")
                # Can resolve 'nextcloud', likely in Docker network
                return base_url
            except (socket.gaierror, OSError):
                # Can't resolve 'nextcloud' or network error, likely local development
                return "http://localhost:8080"
        
        return base_url
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return cls.ENVIRONMENT.lower() in ["development", "dev", "local"]
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return cls.ENVIRONMENT.lower() in ["production", "prod"]
    
    @classmethod
    def validate_config(cls) -> None:
        """
        Validate critical configuration values
        Raises ValueError if required config is missing or invalid
        """
        if not cls.SECRET_KEY or cls.SECRET_KEY == "your-secret-key-change-in-production":
            if cls.is_production():
                raise ValueError("SECRET_KEY must be set in production environment")
        
        if cls.VIDEO_MIN_DURATION >= cls.VIDEO_MAX_DURATION:
            raise ValueError("VIDEO_MIN_DURATION must be less than VIDEO_MAX_DURATION")
        
        if cls.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")


# Create a global config instance
config = Config()
