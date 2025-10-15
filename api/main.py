from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from pydantic import BaseModel
from typing import List
import uvicorn

from database import get_db, Base, engine
from models import User, Video, Vote
from schemas import ( UserLogin, UserSignup, UserAuthResponse, Token, 
    UserResponse
)
from auth import get_password_hash, verify_password, create_access_token, verify_token, get_current_user
from datetime import timedelta

# Constants
API_TITLE = "ANB Rising Stars Showcase API"

# Create FastAPI app instance
app = FastAPI(
    title=API_TITLE,
    description="API for the ANB Rising Stars Showcase application",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    message: str
    service: str = API_TITLE

# Health Check Routes
@app.get("/api/health", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="success", 
        message=f"{API_TITLE} is running!",
        service=API_TITLE
    )

# Authentication Routes
@app.post("/api/auth/signup", response_model=UserAuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
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
    return UserAuthResponse(
        user=user_response,
        access_token=access_token,
        token_type="bearer"
    )

@app.post("/api/auth/login", response_model=UserAuthResponse)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Return user data and token
    user_response = UserResponse.model_validate(user)
    return UserAuthResponse(
        user=user_response,
        access_token=access_token,
        token_type="bearer"
    )

# Protected endpoint example
@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(db: Session = Depends(get_db), email: str = Depends(verify_token)):
    """Get current authenticated user information"""
    user = get_current_user(db, email)
    return UserResponse.model_validate(user)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
