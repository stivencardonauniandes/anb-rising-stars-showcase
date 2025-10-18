"""
Video management endpoints for upload and processing
"""
import logging
from fastapi import APIRouter, File, UploadFile
from fastapi.params import Form

from schemas.pydantic_schemas import VideoUploadResponse
from services.video_service import video_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...), title: str = Form(...)):
    """
    Upload a video file for processing
    
    - **Requires video file (mp4, avi, mov, etc.)**
    - **Video must be between 20-60 seconds**
    - **Title is required and cannot be empty**
    
    Returns upload confirmation with task ID for tracking
    """
    logger.info(f"Video upload request received: title='{title}', filename='{file.filename}'")
    
    # Delegate all business logic to the service
    result = video_service.process_video_upload(file, title)
    
    logger.info(f"Video upload completed: task_id='{result.task_id}'")
    return result
