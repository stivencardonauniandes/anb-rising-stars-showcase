"""
Video management endpoints for upload and processing
"""
import logging
import uuid

from database import get_db
from dependencies import get_current_user
from models.db_models import User
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.params import Form
from sqlalchemy.orm import Session
from schemas.pydantic_schemas import VideoResponse, VideoUploadResponse
from services.video_service import video_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["videos"])

DELETE_VIDEO_SUCCESS_MESSAGE = "El video ha sido eliminado exitosamente."


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile, title: str = Form(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Upload a video file for processing
    
    - **Requires video file (mp4, avi, mov, etc.)**
    - **Video must be between 20-60 seconds**
    - **Title is required, cannot be empty, and must be at most 200 characters**
    
    Returns upload confirmation with task ID for tracking
    """
    logger.info(f"Video upload request received: title='{title}', filename='{file.filename}'")
    
    # Delegate all business logic to the service
    result = video_service.process_video_upload(file, title, current_user, db)
    
    logger.info(f"Video upload completed: task_id='{result.task_id}'")
    return result


@router.get("/", response_model=list[VideoResponse])
async def list_user_videos(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieve a list of videos uploaded by the authenticated user
    """
    logger.info(f"Fetching videos for user: user='{current_user.id}'")
    
    videos = video_service.get_videos_for_user(current_user, db)

    response_list = []
    for video in videos:
        video_response = VideoResponse(
            video_id=video.id,
            title=video.title,
            status=video.status,
            uploaded_at=video.uploaded_at,
            votes=video.votes,
        )
        if video.processed_at:
            video_response.processed_at = video.processed_at
        if video.processed_url:
            video_response.processed_url = video.processed_url
        response_list.append(video_response)
    
    logger.info(f"Retrieved {len(videos)} videos for user: user='{current_user.id}'")
    return response_list


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video_details(video_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieve details of a specific video by ID for the authenticated user
    """
    logger.info(f"Fetching video details: video_id='{video_id}' for user: user='{current_user.id}'")
    
    video = video_service.get_video_by_id(video_id, current_user, db)
    if not video:
        logger.warning(f"Video not found: video_id='{video_id}'")
        raise HTTPException(status_code=404, detail="Video not found")

    video_response = VideoResponse(
        video_id=video.id,
        title=video.title,
        status=video.status,
        uploaded_at=video.uploaded_at,
        votes=video.votes,
    )
    if video.processed_at:
        video_response.processed_at = video.processed_at
    if video.processed_url:
        video_response.processed_url = video.processed_url

    logger.info(f"Retrieved video details: video_id='{video_id}'")
    return video_response

@router.delete("/{video_id}", status_code=204)
async def delete_video(video_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Delete a specific video by ID for the authenticated user
    """
    logger.info(f"Delete request for video: video_id='{video_id}'")
    
    success = video_service.delete_video(video_id, current_user, db)
    if not success:
        logger.warning(f"Video not found for deletion: video_id='{video_id}'")
        raise HTTPException(status_code=404, detail="Video not found")
    
    logger.info(f"Video deleted successfully: video_id='{video_id}'")
    return {
        "video_id": video_id,
        "message": DELETE_VIDEO_SUCCESS_MESSAGE
    }
