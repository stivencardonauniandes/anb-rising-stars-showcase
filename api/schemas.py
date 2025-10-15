from pydantic import BaseModel, EmailStr, validator, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

# User Type Enum
class UserType(str, Enum):
    player = "player"
    voter = "voter"

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password1: str
    password2: str
    type: UserType
    city: Optional[str] = None
    country: Optional[str] = None
    
    @validator('password2')
    def passwords_match(cls, v, values, **kwargs):
        if 'password1' in values and v != values['password1']:
            raise ValueError('Las contraseñas no coinciden')
        return v
    
    @validator('password1')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('La contraseña debe tener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('La contraseña debe tener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('La contraseña debe tener al menos un número')
        return v

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    type: UserType
    city: Optional[str]
    country: Optional[str]
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    type: Optional[UserType] = None
    city: Optional[str] = None
    country: Optional[str] = None

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
