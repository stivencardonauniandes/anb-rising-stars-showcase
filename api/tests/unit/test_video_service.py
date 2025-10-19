"""
Unit tests for VideoService
Tests the video service in isolation with mocked dependencies
"""
import pytest
import os
import uuid
from unittest.mock import patch, mock_open, MagicMock
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from io import BytesIO

from models.db_models import User
from services.video_service import VideoService
from schemas.pydantic_schemas import VideoUploadResponse


class TestVideoServiceValidation:
    """Test video service validation methods"""
    
    def test_validate_title_success(self):
        """Test successful title validation"""
        result = VideoService.validate_title("Valid Title")
        assert result == "Valid Title"
    
    def test_validate_title_with_whitespace(self):
        """Test title validation with leading/trailing whitespace"""
        result = VideoService.validate_title("  Valid Title  ")
        assert result == "Valid Title"
    
    def test_validate_title_empty_raises_exception(self):
        """Test that empty title raises HTTPException"""
        with pytest.raises(HTTPException) as exc_info:
            VideoService.validate_title("")
        
        assert exc_info.value.status_code == 400
        assert "título del video no puede estar vacío" in exc_info.value.detail
    
    def test_validate_title_whitespace_only_raises_exception(self):
        """Test that whitespace-only title raises HTTPException"""
        with pytest.raises(HTTPException) as exc_info:
            VideoService.validate_title("   \t\n   ")
        
        assert exc_info.value.status_code == 400
        assert "título del video no puede estar vacío" in exc_info.value.detail
    
    def test_validate_title_none_raises_exception(self):
        """Test that None title raises HTTPException"""
        with pytest.raises(HTTPException) as exc_info:
            VideoService.validate_title(None)
        
        assert exc_info.value.status_code == 400
    
    def test_validate_file_type_success(self):
        """Test successful file type validation"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "video/mp4"
        
        # Should not raise exception
        VideoService.validate_file_type(mock_file)
    
    def test_validate_file_type_various_video_types(self):
        """Test validation with various video content types"""
        video_types = [
            "video/mp4",
            "video/avi", 
            "video/quicktime",
            "video/x-msvideo",
            "video/x-matroska"
        ]
        
        for content_type in video_types:
            mock_file = MagicMock(spec=UploadFile)
            mock_file.content_type = content_type
            
            # Should not raise exception
            VideoService.validate_file_type(mock_file)
    
    def test_validate_file_type_invalid_raises_exception(self):
        """Test that invalid file type raises HTTPException"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "text/plain"
        
        with pytest.raises(HTTPException) as exc_info:
            VideoService.validate_file_type(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Tipo de archivo inválido" in exc_info.value.detail
    
    def test_validate_file_type_none_content_type_raises_exception(self):
        """Test that None content type raises HTTPException"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = None
        
        with pytest.raises(HTTPException) as exc_info:
            VideoService.validate_file_type(mock_file)
        
        assert exc_info.value.status_code == 400


class TestVideoServiceFileOperations:
    """Test video service file operations"""
    
    @patch('services.video_service.shutil.copyfileobj')
    @patch('builtins.open', new_callable=mock_open)
    @patch('services.video_service.uuid.uuid4')
    def test_save_temp_file_success(self, mock_uuid, mock_file_open, mock_copyfile):
        """Test successful temporary file saving"""
        # Setup mocks
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9012-123456789012')
        mock_upload_file = MagicMock(spec=UploadFile)
        mock_upload_file.filename = "test.mp4"
        mock_upload_file.file = BytesIO(b"fake video data")
        
        # Call method
        result = VideoService.save_temp_file(mock_upload_file)
        
        # Assertions
        expected_filename = "temp_video_12345678-1234-5678-9012-123456789012_test.mp4"
        assert result == expected_filename
        mock_file_open.assert_called_once_with(expected_filename, "wb")
        mock_copyfile.assert_called_once()
    
    @patch('services.video_service.shutil.copyfileobj')
    @patch('builtins.open', side_effect=IOError("File write error"))
    def test_save_temp_file_io_error_raises_exception(self, mock_file_open, mock_copyfile):
        """Test that IO error during file save raises HTTPException"""
        mock_upload_file = MagicMock(spec=UploadFile)
        mock_upload_file.filename = "test.mp4"
        
        with pytest.raises(HTTPException) as exc_info:
            VideoService.save_temp_file(mock_upload_file)
        
        assert exc_info.value.status_code == 500
        assert "Error al procesar el archivo de video" in exc_info.value.detail
    
    @patch('services.video_service.os.path.exists', return_value=True)
    @patch('services.video_service.os.remove')
    def test_cleanup_temp_file_success(self, mock_remove, mock_exists):
        """Test successful temporary file cleanup"""
        VideoService.cleanup_temp_file("test_file.mp4")
        
        mock_exists.assert_called_once_with("test_file.mp4")
        mock_remove.assert_called_once_with("test_file.mp4")
    
    @patch('services.video_service.os.path.exists', return_value=False)
    @patch('services.video_service.os.remove')
    def test_cleanup_temp_file_not_exists(self, mock_remove, mock_exists):
        """Test cleanup when file doesn't exist"""
        VideoService.cleanup_temp_file("nonexistent_file.mp4")
        
        mock_exists.assert_called_once_with("nonexistent_file.mp4")
        mock_remove.assert_not_called()
    
    @patch('services.video_service.os.path.exists', return_value=True)
    @patch('services.video_service.os.remove', side_effect=OSError("Permission denied"))
    def test_cleanup_temp_file_error_handled_gracefully(self, mock_remove, mock_exists):
        """Test that cleanup errors are handled gracefully"""
        # Should not raise exception
        VideoService.cleanup_temp_file("test_file.mp4")
        
        mock_exists.assert_called_once_with("test_file.mp4")
        mock_remove.assert_called_once_with("test_file.mp4")


class TestVideoServiceVideoValidation:
    """Test video property validation"""
    
    @patch('services.video_service.VideoFileClip')
    def test_validate_video_properties_success(self, mock_video_clip):
        """Test successful video validation"""
        # Setup mock
        mock_clip_instance = MagicMock()
        mock_clip_instance.duration = 30.0  # Valid duration
        mock_video_clip.return_value = mock_clip_instance
        
        result = VideoService.validate_video_properties("test_file.mp4")
        
        assert result == {"duration": 30.0}
        mock_video_clip.assert_called_once_with("test_file.mp4")
        mock_clip_instance.close.assert_called_once()
    
    @patch('services.video_service.VideoFileClip')
    def test_validate_video_properties_too_short(self, mock_video_clip):
        """Test video validation with too short duration"""
        # Setup mock
        mock_clip_instance = MagicMock()
        mock_clip_instance.duration = 10.0  # Too short (< 20 seconds)
        mock_video_clip.return_value = mock_clip_instance
        
        with pytest.raises(HTTPException) as exc_info:
            VideoService.validate_video_properties("test_file.mp4")
        
        assert exc_info.value.status_code == 400
        assert "duración entre 20 y 60 segundos" in exc_info.value.detail
        mock_clip_instance.close.assert_called_once()
    
    @patch('services.video_service.VideoFileClip')
    def test_validate_video_properties_too_long(self, mock_video_clip):
        """Test video validation with too long duration"""
        # Setup mock
        mock_clip_instance = MagicMock()
        mock_clip_instance.duration = 90.0  # Too long (> 60 seconds)
        mock_video_clip.return_value = mock_clip_instance
        
        with pytest.raises(HTTPException) as exc_info:
            VideoService.validate_video_properties("test_file.mp4")
        
        assert exc_info.value.status_code == 400
        assert "duración entre 20 y 60 segundos" in exc_info.value.detail
        mock_clip_instance.close.assert_called_once()
    
    @patch('services.video_service.VideoFileClip', side_effect=ValueError("Invalid video file"))
    def test_validate_video_properties_invalid_file(self, mock_video_clip):
        """Test video validation with invalid video file"""
        with pytest.raises(HTTPException) as exc_info:
            VideoService.validate_video_properties("invalid_file.mp4")
        
        assert exc_info.value.status_code == 500
        assert "Error al procesar el archivo de video" in exc_info.value.detail
    
    @patch('services.video_service.VideoFileClip', side_effect=RuntimeError("Codec error"))
    def test_validate_video_properties_runtime_error(self, mock_video_clip):
        """Test video validation with runtime error"""
        with pytest.raises(HTTPException) as exc_info:
            VideoService.validate_video_properties("corrupted_file.mp4")
        
        assert exc_info.value.status_code == 500
        assert "Error al procesar el archivo de video" in exc_info.value.detail


class TestVideoServiceNextcloudUpload:
    """Test Nextcloud upload functionality"""
    
    @patch('services.video_service.requests.put')
    @patch('services.video_service.config')
    def test_upload_to_nextcloud_success(self, mock_config, mock_requests_put):
        """Test successful Nextcloud upload"""
        # Setup mocks
        mock_config.get_nextcloud_url.return_value = "http://localhost:8080"
        mock_config.NEXTCLOUD_USERNAME = "test_user"
        mock_config.NEXTCLOUD_PASSWORD = "test_pass"
        mock_config.VIDEO_UPLOAD_TIMEOUT = 300
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_requests_put.return_value = mock_response
        
        file_data = BytesIO(b"fake video data")
        
        # Call method
        result = VideoService.upload_to_nextcloud(file_data, "test_video.mp4")
        
        # Assertions
        assert result == "/raw/test_video.mp4"
        mock_requests_put.assert_called_once()
        
        # Check the call arguments
        call_args = mock_requests_put.call_args
        expected_url = "http://localhost:8080/remote.php/dav/files/test_user/raw/test_video.mp4"
        # The URL should be the first positional argument
        assert call_args[0][0] == expected_url
        assert call_args[1]['data'] == file_data
        assert call_args[1]['auth'] == ("test_user", "test_pass")
        assert call_args[1]['timeout'] == 300
    
    @patch('services.video_service.requests.put')
    @patch('services.video_service.config')
    def test_upload_to_nextcloud_http_error(self, mock_config, mock_requests_put):
        """Test Nextcloud upload with HTTP error response"""
        # Setup mocks
        mock_config.get_nextcloud_url.return_value = "http://localhost:8080"
        mock_config.NEXTCLOUD_USERNAME = "test_user"
        mock_config.NEXTCLOUD_PASSWORD = "test_pass"
        mock_config.VIDEO_UPLOAD_TIMEOUT = 300
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_requests_put.return_value = mock_response
        
        file_data = BytesIO(b"fake video data")
        
        with pytest.raises(HTTPException) as exc_info:
            VideoService.upload_to_nextcloud(file_data, "test_video.mp4")
        
        assert exc_info.value.status_code == 500
        assert "Failed to upload video to storage service" in exc_info.value.detail
    
    @patch('services.video_service.requests.put', side_effect=ConnectionError("Network error"))
    @patch('services.video_service.config')
    def test_upload_to_nextcloud_network_error(self, mock_config, mock_requests_put):
        """Test Nextcloud upload with network error"""
        # Setup mocks
        mock_config.get_nextcloud_url.return_value = "http://localhost:8080"
        mock_config.NEXTCLOUD_USERNAME = "test_user"
        mock_config.NEXTCLOUD_PASSWORD = "test_pass"
        mock_config.VIDEO_UPLOAD_TIMEOUT = 300
        
        file_data = BytesIO(b"fake video data")
        
        with pytest.raises(HTTPException) as exc_info:
            VideoService.upload_to_nextcloud(file_data, "test_video.mp4")
        
        assert exc_info.value.status_code == 500
        assert "Failed to upload video to storage service" in exc_info.value.detail


class TestVideoServiceIntegration:
    """Test video service integration methods"""
    
    @patch('services.video_service.VideoService.cleanup_temp_file')
    @patch('services.video_service.VideoService.upload_to_nextcloud')
    @patch('services.video_service.VideoService.validate_video_properties')
    @patch('services.video_service.VideoService.save_temp_file')
    @patch('services.video_service.VideoService.validate_file_type')
    @patch('services.video_service.VideoService.validate_title')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_video_upload_success(self, mock_file_open, mock_validate_title, 
                                        mock_validate_file_type, mock_save_temp_file,
                                        mock_validate_properties, mock_upload_nextcloud,
                                        mock_cleanup):
        """Test successful complete video upload process"""
        # Setup mocks
        mock_validate_title.return_value = "Clean Title"
        mock_save_temp_file.return_value = "temp_file.mp4"
        mock_validate_properties.return_value = {"duration": 30.0}
        mock_upload_nextcloud.return_value = "/raw/Clean Title"
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        
        mock_upload_file = MagicMock(spec=UploadFile)
        mock_upload_file.filename = "test.mp4"
        
        # Call method
        result = VideoService.process_video_upload(mock_upload_file, "Test Title", mock_user, mock_db)
        
        # Assertions
        assert isinstance(result, VideoUploadResponse)
        assert result.message == "Video subido correctamente. Procesamiento en curso."
        assert result.task_id is not None
        assert len(result.task_id) == 36  # UUID length
        
        # Verify all methods were called
        mock_validate_title.assert_called_once_with("Test Title")
        mock_validate_file_type.assert_called_once_with(mock_upload_file)
        mock_save_temp_file.assert_called_once_with(mock_upload_file)
        mock_validate_properties.assert_called_once_with("temp_file.mp4")
        mock_upload_nextcloud.assert_called_once()
        mock_cleanup.assert_called_once_with("temp_file.mp4")
    
    @patch('services.video_service.VideoService.cleanup_temp_file')
    @patch('services.video_service.VideoService.save_temp_file')
    @patch('services.video_service.VideoService.validate_file_type')
    @patch('services.video_service.VideoService.validate_title', side_effect=HTTPException(status_code=400, detail="Invalid title"))
    def test_process_video_upload_title_validation_error(self, mock_validate_title,
                                                       mock_validate_file_type, 
                                                       mock_save_temp_file,
                                                       mock_cleanup):
        """Test video upload process with title validation error"""
        mock_upload_file = MagicMock(spec=UploadFile)
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        
        with pytest.raises(HTTPException) as exc_info:
            VideoService.process_video_upload(mock_upload_file, "", mock_user, mock_db)
        
        assert exc_info.value.status_code == 400
        assert "Invalid title" in exc_info.value.detail
        
        # Verify cleanup is not called since temp file was never created
        mock_save_temp_file.assert_not_called()
        mock_cleanup.assert_not_called()
    
    @patch('services.video_service.VideoService.cleanup_temp_file')
    @patch('services.video_service.VideoService.validate_video_properties', side_effect=HTTPException(status_code=400, detail="Invalid video"))
    @patch('services.video_service.VideoService.save_temp_file')
    @patch('services.video_service.VideoService.validate_file_type')
    @patch('services.video_service.VideoService.validate_title')
    def test_process_video_upload_cleanup_on_error(self, mock_validate_title,
                                                  mock_validate_file_type, 
                                                  mock_save_temp_file,
                                                  mock_validate_properties,
                                                  mock_cleanup):
        """Test that cleanup is called even when processing fails"""
        # Setup mocks
        mock_validate_title.return_value = "Clean Title"
        mock_save_temp_file.return_value = "temp_file.mp4"
        
        mock_upload_file = MagicMock(spec=UploadFile)
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        
        with pytest.raises(HTTPException):
            VideoService.process_video_upload(mock_upload_file, "Test Title", mock_user, mock_db)
        
        # Verify cleanup was called even though validation failed
        mock_cleanup.assert_called_once_with("temp_file.mp4")
