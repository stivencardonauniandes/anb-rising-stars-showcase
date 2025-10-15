from pydantic import BaseModel, EmailStr, validator, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

# Video Status Enum
class VideoStatus(str, Enum):
    uploaded = "uploaded"
    processed = "processed"
    deleted = "deleted"

class VideoCreate(BaseModel):
    user_id: uuid.UUID
    title: str
    status: VideoStatus = VideoStatus.uploaded
    original_url: str
    processed_url: Optional[str] = None
    raw_video_id: Optional[uuid.UUID] = None
    processed_video_id: Optional[uuid.UUID] = None
    
    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Título debe tener al menos 3 caracteres')
        return v.strip()

class VideoResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    raw_video_id: uuid.UUID
    processed_video_id: Optional[uuid.UUID]
    title: str
    status: VideoStatus
    uploaded_at: datetime
    processed_at: Optional[datetime]
    original_url: str
    processed_url: Optional[str]
    votes: int
    
    class Config:
        from_attributes = True

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[VideoStatus] = None
    processed_at: Optional[datetime] = None
    processed_url: Optional[str] = None
    processed_video_id: Optional[uuid.UUID] = None
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and len(v.strip()) < 3:
            raise ValueError('Título debe tener al menos 3 caracteres')
        return v.strip() if v else None

# Vote Schemas
class VoteCreate(BaseModel):
    user_id: uuid.UUID
    video_id: uuid.UUID

class VoteResponse(BaseModel):
    user_id: uuid.UUID
    video_id: uuid.UUID
    
    class Config:
        from_attributes = True

# Authentication Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSignup(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password1: str
    password2: str
    city: Optional[str] = None
    country: Optional[str] = None
    
    @validator('password1')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('password2')
    def passwords_match(cls, v, values, **kwargs):
        if 'password1' in values and v != values['password1']:
            raise ValueError('Passwords do not match')
        return v

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    city: Optional[str]
    country: Optional[str]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserAuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str

class VideoUploadResponse(BaseModel):
    message: str
    task_id: Optional[str] = None
