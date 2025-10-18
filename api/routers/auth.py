from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.pydantic_schemas import UserAuthResponse, UserLogin, UserSignup
from services.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=UserAuthResponse)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    return auth_service.authenticate_user(db, user_credentials)


@router.post("/signup", response_model=UserAuthResponse, status_code=201)
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """Register a new user"""
    return auth_service.register_user(db, user_data)
