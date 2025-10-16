import os
import requests
import shutil
from fastapi import FastAPI, File, HTTPException, Depends, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Form
from moviepy.editor import VideoFileClip
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from pydantic import BaseModel
from typing import List
import logging
import uvicorn

from database import get_db, Base, engine
from models import User, Video, Vote
from schemas import ( UserLogin, UserSignup, UserAuthResponse, Token, 
    UserResponse,
    VideoUploadResponse
)
from auth import get_password_hash, verify_password, create_access_token, verify_token, get_current_user
from datetime import timedelta

# Constants
API_TITLE = "ANB Rising Stars Showcase API"
INVALID_FILE_TYPE = "Tipo de archivo inválido. Se requiere un archivo de video."
INVALID_VIDEO_LENGTH = "El video debe tener una duración entre 20 y 60 segundos."
INVALID_VIDEO_RESOLUTION = "La resolución del video debe ser al menos 1080p."
INVALID_VIDEO_TITLE = "El título del video no puede estar vacío."
FILE_PROCESSING_ERROR = "Error al procesar el archivo de video."
FILE_UPLOAD_SUCCESS = "Video subiddo correctamente. Procesamiento en curso."

# Configure logging
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Endpoint to upload videos
@app.post("/api/videos/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...), title: str = Form(...)):

    # Validate title
    if not title or title.strip() == "":
        raise HTTPException(status_code=400, detail=INVALID_VIDEO_TITLE)
    # Validate file type
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail=INVALID_FILE_TYPE)
    
    # Create a temporary file path
    temp_filepath = f"temp_video_{file.filename}"

    # Save the uploaded file to the temporary path
    with open(temp_filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Validate video length and resolution
        video_clip = VideoFileClip(temp_filepath)
        duration = video_clip.duration  # Duration in seconds
        width = video_clip.w
        height = video_clip.h
        video_clip.close()
        if duration < 20 or duration > 60:  # Duration must be between 20 and 60 seconds
            raise HTTPException(status_code=400, detail=INVALID_VIDEO_LENGTH)
        if width < 1920 or height < 1080:  # Resolution must be at least 1080p
            raise HTTPException(status_code=400, detail=INVALID_VIDEO_RESOLUTION)
        
        # Upload video to Nextcloud
        video_url = upload_video_to_nextcloud(file.file, title)
        return VideoUploadResponse(
            message=FILE_UPLOAD_SUCCESS,
            task_id='1234'
        )
    except (ValueError, BufferError, RuntimeError) as e:
        logger.error(f"Error processing video file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=FILE_PROCESSING_ERROR)
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
    

def upload_video_to_nextcloud(file: File, filename: str) -> str:
        """
        Function to upload video to Nextcloud.
        Return the url of the uploaded video.
        """
        try:
            webdav_url = "http://nextcloud"
            username = "worker"
            password = "super-secret"
            remote_path = f"/raw/{filename}"
            remote_path_url = webdav_url + f"/remote.php/dav/files{remote_path}"
            response = requests.put(
                remote_path_url,
                data=file,
                auth=(username, password)
            )
            if response.status_code not in [200, 201, 204]:
                logger.error(f"Failed to upload video to Nextcloud: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail="Failed to upload video to storage service.")
            return remote_path
        except Exception as e:
            logger.error(f"Failed to upload video to Nextcloud: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to upload video to storage service.")

    # Upload video to Nextcloud (placeholder function)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
