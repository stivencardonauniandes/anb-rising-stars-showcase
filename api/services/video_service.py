"""
Video service for handling video upload, validation, and processing
"""
import logging
import os
import shutil
import requests
import uuid
from typing import BinaryIO, Dict
from fastapi import HTTPException, UploadFile
from moviepy.editor import VideoFileClip

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
    
    @classmethod
    def process_video_upload(cls, file: UploadFile, title: str) -> VideoUploadResponse:
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
            # Validate video properties
            video_properties = cls.validate_video_properties(temp_filepath)
            
            # Upload to Nextcloud
            with open(temp_filepath, "rb") as video_file:
                remote_path = cls.upload_to_nextcloud(video_file, cleaned_title)
            
            # Generate task ID for tracking (in a real system, this would be from a job queue)
            task_id = str(uuid.uuid4())
            
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


# Create service instance
video_service = VideoService()
