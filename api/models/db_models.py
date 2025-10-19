from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from database import Base
from database_types import UUID

class VideoStatus(enum.Enum):
    uploaded = "uploaded"
    processed = "processed"
    deleted = "deleted"
    published = "published"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Relationships
    videos = relationship("Video", back_populates="user")
    votes = relationship("Vote", back_populates="user")

    def __repr__(self):
        return f"<User(email='{self.email}')>"

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(), ForeignKey('users.id'), nullable=False)
    raw_video_id = Column(UUID(), default=uuid.uuid4, nullable=False)
    processed_video_id = Column(UUID(), nullable=True)
    title = Column(String(200), nullable=False)
    status = Column(SQLEnum(VideoStatus), nullable=False, default=VideoStatus.uploaded)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    original_url = Column(String(500), nullable=False)
    processed_url = Column(String(500), nullable=True)
    votes = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="videos")
    vote_records = relationship("Vote", back_populates="video")

    def __repr__(self):
        status_value = self.status.value if self.status else 'None'
        return f"<Video(id='{self.id}', title='{self.title}', status='{status_value}')>"

class Vote(Base):
    __tablename__ = "votes"
    
    user_id = Column(UUID(), ForeignKey('users.id'), primary_key=True)
    video_id = Column(UUID(), ForeignKey('videos.id'), primary_key=True)
    
    # Relationships
    user = relationship("User", back_populates="votes")
    video = relationship("Video", back_populates="vote_records")

    def __repr__(self):
        return f"<Vote(user_id='{self.user_id}', video_id='{self.video_id}')>"
