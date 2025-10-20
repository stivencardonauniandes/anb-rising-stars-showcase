"""
Video service for handling video upload, validation, and processing
"""
import logging
import os
import shutil
import redis
import requests
import uuid
from typing import BinaryIO, Dict
from models.db_models import User, Video
from fastapi import HTTPException, UploadFile
from moviepy.editor import VideoFileClip
from sqlalchemy.orm import Session

from schemas.pydantic_schemas import VideoUploadResponse
from config import config

logger = logging.getLogger(__name__)

class VideoService:
    # Constants
    INVALID_FILE_TYPE = "Tipo de archivo inválido. Se requiere un archivo de video."
    INVALID_VIDEO_LENGTH = "El video debe tener una duración entre 20 y 60 segundos."
    INVALID_VIDEO_RESOLUTION = "La resolución del video debe ser al menos 1080p."
    INVALID_VIDEO_TITLE = "El título del video no puede estar vacío."
    FILE_PROCESSING_ERROR = "Error al procesar el archivo de video."
    FILE_UPLOAD_SUCCESS = "Video subido correctamente. Procesamiento en curso."
    REDIS_STREAM_NAME = 'video_tasks'
    
    # Use centralized configuration
    # All configuration now comes from the config module
    
    @staticmethod
    def validate_title(title: str) -> str:
        """
        Validate video title
        
        Args:
            title: Video title to validate
            
        Returns:
            str: Cleaned title
            
        Raises:
            HTTPException: If title is invalid
        """
        if not title or title.strip() == "":
            raise HTTPException(status_code=400, detail=VideoService.INVALID_VIDEO_TITLE)
        return title.strip()
    
    @staticmethod
    def validate_file_type(file: UploadFile) -> None:
        """
        Validate uploaded file type
        
        Args:
            file: Uploaded file to validate
            
        Raises:
            HTTPException: If file type is invalid
        """
        if not file.content_type or not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail=VideoService.INVALID_FILE_TYPE)
    
    @staticmethod
    def validate_video_properties(temp_filepath: str) -> Dict[str, float]:
        """
        Validate video duration and other properties
        
        Args:
            temp_filepath: Path to temporary video file
            
        Returns:
            Dict with video properties (duration, etc.)
            
        Raises:
            HTTPException: If video properties are invalid
        """
        try:
            video_clip = VideoFileClip(temp_filepath)
            duration = video_clip.duration
            video_clip.close()
            
            if duration < config.VIDEO_MIN_DURATION or duration > config.VIDEO_MAX_DURATION:
                raise HTTPException(status_code=400, detail=VideoService.INVALID_VIDEO_LENGTH)
            
            logger.info(f"Video validation passed: duration={duration}s")
            return {"duration": duration}
            
        except (ValueError, BufferError, RuntimeError) as e:
            logger.error(f"Error validating video properties: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=VideoService.FILE_PROCESSING_ERROR)
    
    @staticmethod
    def save_temp_file(file: UploadFile) -> str:
        """
        Save uploaded file to temporary location
        
        Args:
            file: Uploaded file to save
            
        Returns:
            str: Path to temporary file
            
        Raises:
            HTTPException: If file cannot be saved
        """
        try:
            # Generate unique temporary filename
            temp_filename = f"temp_video_{uuid.uuid4()}_{file.filename}"
            
            # Save the uploaded file to the temporary path
            with open(temp_filename, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            logger.info(f"Temporary file saved: {temp_filename}")
            return temp_filename
            
        except Exception as e:
            logger.error(f"Error saving temporary file: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=VideoService.FILE_PROCESSING_ERROR)
    
    @staticmethod
    def cleanup_temp_file(temp_filepath: str) -> None:
        """
        Clean up temporary file
        
        Args:
            temp_filepath: Path to temporary file to remove
        """
        try:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
                logger.info(f"Temporary file cleaned up: {temp_filepath}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {temp_filepath}: {e}")
    
    @staticmethod
    def upload_to_nextcloud(file_data: BinaryIO, filename: str) -> str:
        """
        Upload video file to Nextcloud storage
        
        Args:
            file_data: Binary file data to upload
            filename: Name for the file in storage
            
        Returns:
            str: Remote path of uploaded file
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            remote_path = f"/raw/{filename}"
            nextcloud_url = config.get_nextcloud_url()
            remote_path_url = (
                f"{nextcloud_url}/remote.php/dav/files/"
                f"{config.NEXTCLOUD_USERNAME}{remote_path}"
            )
            
            logger.info(f"Using Nextcloud URL: {nextcloud_url}")
            logger.info(f"Upload URL: {remote_path_url}")
            
            response = requests.put(
                remote_path_url,
                data=file_data,
                auth=(config.NEXTCLOUD_USERNAME, config.NEXTCLOUD_PASSWORD),
                timeout=config.VIDEO_UPLOAD_TIMEOUT
            )
            
            if response.status_code not in [200, 201, 204]:
                logger.error(
                    f"Failed to upload video to Nextcloud: "
                    f"{response.status_code} - {response.text}"
                )
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to upload video to storage service."
                )
            
            logger.info(f"Video uploaded to Nextcloud: {remote_path}")
            return remote_path
            
        except requests.RequestException as e:
            logger.error(f"Network error uploading to Nextcloud: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail="Failed to upload video to storage service."
            )
        except Exception as e:
            logger.error(f"Unexpected error uploading to Nextcloud: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail="Failed to upload video to storage service."
            )
    
    @staticmethod
    def create_db_record(user_id: uuid, raw_video_id: uuid, title:str, original_url: str, db:Session) -> None:
        """
        Create a database record for the uploaded video
        
        Args:
            user_id: ID of the user uploading the video
            raw_video_id: Generated ID for the raw video
            title: Title of the video
            original_url: URL of the uploaded video in storage
        """
        
        new_video = Video(
            user_id=user_id,
            raw_video_id=raw_video_id,
            title=title,
            status="uploaded",
            original_url=original_url
        )
        
        db.add(new_video)
        db.commit()
        
        logger.info(f"Database record created for video: id='{raw_video_id}', title='{title}, original_url='{original_url}'")
        return new_video.id
    
    @classmethod
    def post_message_to_redis_stream(cls, video_id: uuid, task_id: str, source_path: str ) -> None:
        """
        Post a message to Redis stream for video processing
        
        Args:
            task_id: ID of the video processing task
        """
        try:
            
            r = redis.Redis(
                host="redis",
                port="6379",
                db=0,
                password=None,
            )
            
            message = {
                "task_id": task_id,
                "video_id": str(video_id),
                "source_path": source_path}
            r.xadd(cls.REDIS_STREAM_NAME, message)
            
            logger.info(f"Message posted to Redis stream: task_id='{task_id}'")
            
        except Exception as e:
            logger.error(f"Error posting message to Redis stream: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to queue video for processing."
            )
    
    @classmethod
    def process_video_upload(cls, file: UploadFile, title: str, current_user:User, db: Session) -> VideoUploadResponse:
        """
        Process complete video upload workflow
        
        Args:
            file: Uploaded video file
            title: Video title
            
        Returns:
            VideoUploadResponse: Upload result with task ID
            
        Raises:
            HTTPException: If any step of the process fails
        """
        # Validate inputs
        cleaned_title = cls.validate_title(title)
        cls.validate_file_type(file)
        
        # Save temporary file
        temp_filepath = cls.save_temp_file(file)
        
        try:
            # Generate task ID for tracking (in a real system, this would be from a job queue)
            task_id = str(uuid.uuid4())

            # Validate video properties
            video_properties = cls.validate_video_properties(temp_filepath)

            # Get file extension
            _, ext = os.path.splitext(file.filename)

            # Generate filename with extension
            upload_filename = f"{cleaned_title}{task_id}{ext}"
            
            # Upload to Nextcloud
            with open(temp_filepath, "rb") as video_file:
                remote_path = cls.upload_to_nextcloud(video_file, upload_filename)
            
            # Create db record
            record_id = cls.create_db_record(
                user_id=current_user.id,
                raw_video_id=task_id,
                title=cleaned_title,
                original_url=remote_path,
                db=db
            )

            # Post message on redis stream
            cls.post_message_to_redis_stream(
                task_id=task_id,
                video_id=record_id,
                source_path=remote_path
            )

            
            logger.info(
                f"Video upload completed successfully: title='{cleaned_title}', "
                f"duration={video_properties['duration']}s, remote_path='{remote_path}', "
                f"task_id='{task_id}'"
            )
            
            return VideoUploadResponse(
                message=cls.FILE_UPLOAD_SUCCESS,
                task_id=task_id
            )
            
        finally:
            # Always cleanup temporary file
            cls.cleanup_temp_file(temp_filepath)
    
    @classmethod
    def get_videos_for_user(cls, current_user: User, db: Session) -> list[Video]:
        """
        Retrieve videos uploaded by the specified user
        
        Args:
            current_user: Authenticated user
            
        Returns:
            list[Video]: List of videos uploaded by the user
        """
        videos = db.query(Video).filter(Video.user_id == current_user.id, Video.status != 'deleted').all()
        return videos
    
    @classmethod
    def get_video_by_id(cls, video_id: str, current_user: User, db: Session) -> Video:
        """
        Retrieve a specific video by ID for the specified user
        
        Args:
            video_id: ID of the video to retrieve
            current_user: Authenticated user
        Returns:
            Video | None: Video object if found, else None
        Raises:
            403 HTTPException: If the video does not belong to the user
        """
        try:
            ### sanitize video_id
            video_id = uuid.UUID(video_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid video ID format"
            )
        video = db.query(Video).filter(Video.id == video_id, Video.status != 'deleted').first()
        if video and video.user_id != current_user.id:
            logger.warning(f"Unauthorized access attempt: video_id='{video_id}' by user_id='{current_user.id}'")
            raise HTTPException(status_code=403, detail="You do not have permission to access this video.")
        return video
    
    @classmethod
    def delete_video(cls, video_id: str, current_user: User, db: Session) -> None:
        """
        Delete a specific video by ID for the specified user
        
        Args:
            video_id: ID of the video to delete
            current_user: Authenticated user
            
        Raises:
            HTTPException: If the video does not exist or does not belong to the user
        """
        try:
            ### sanitize video_id
            video_id = uuid.UUID(video_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid video ID format"
            )
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.warning(f"Video not found for deletion: video_id='{video_id}' by user_id='{current_user.id}'")
            raise HTTPException(status_code=404, detail="Video not found")
        
        if video.user_id != current_user.id:
            logger.warning(f"Unauthorized delete attempt: video_id='{video_id}' by user_id='{current_user.id}'")
            raise HTTPException(status_code=403, detail="You do not have permission to delete this video.")
        
        if video.status == "published":
            logger.warning(f"Attempt to delete published video: video_id='{video_id}' by user_id='{current_user.id}'")
            raise HTTPException(status_code=400, detail="Published videos cannot be deleted.")
        
        video.status = "deleted"
        db.commit()
        
        logger.info(f"Video deleted: video_id='{video_id}' by user_id='{current_user.id}'")

        return True
    
    @classmethod
    def get_published_videos(cls, db: Session) -> list[Video]:
        """
        Retrieve a list of published videos
        
        Returns:
            list[Video]: List of published videos
        """
        videos = db.query(Video).filter(Video.status == 'published').all()
        logger.info(f"Retrieved {len(videos)} published videos")
        return videos


# Create service instance
video_service = VideoService()
