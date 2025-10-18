from pydantic import field_validator, ConfigDict, BaseModel, EmailStr, validator, HttpUrl
from typing import Optional
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
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Título debe tener al menos 3 caracteres')
        return v.strip()

class VideoResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    raw_video_id: uuid.UUID
    processed_video_id: Optional[uuid.UUID] = None
    title: str
    status: VideoStatus
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    original_url: str
    processed_url: Optional[str] = None
    votes: int
    model_config = ConfigDict(from_attributes=True)

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[VideoStatus] = None
    processed_at: Optional[datetime] = None
    processed_url: Optional[str] = None
    processed_video_id: Optional[uuid.UUID] = None
    
    @field_validator('title')
    @classmethod
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
    model_config = ConfigDict(from_attributes=True)

# Authentication Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v

class UserSignup(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password1: str
    password2: str
    city: Optional[str] = None
    country: Optional[str] = None
    
    @field_validator('password1')
    @classmethod
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
    
    @field_validator('password2')
    @classmethod
    def passwords_match(cls, v, values, **kwargs):
        print(f"v: {v}")
        print(f"values: {values}")
        print(f"kwargs: {kwargs}")
        if 'password1' in values.data and v != values.data['password1']:
            raise ValueError('Passwords do not match')
        return v

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    city: Optional[str] = None
    country: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

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
