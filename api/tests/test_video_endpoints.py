"""
Tests for video management endpoints
"""
import io
import pytest
import uuid

from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from tests.test_database import client, db_session, test_user, auth_headers
from schemas.pydantic_schemas import VideoUploadResponse


class TestVideoUploadEndpoint:
    """Tests for POST /api/videos/upload"""
    
    def create_test_video_file(self, filename="test_video.mp4", content_type="video/mp4", content=b"fake video content"):
        """Helper to create a test video file"""
        return ("file", (filename, io.BytesIO(content), content_type))
    
    @patch('services.video_service.video_service.process_video_upload')
    def test_upload_video_success(self, mock_process_upload, auth_headers):
        """Test successful video upload"""
        # Mock the service response
        mock_response = VideoUploadResponse(
            message="Video subido correctamente. Procesamiento en curso.",
            task_id="test-task-123"
        )
        mock_process_upload.return_value = mock_response
        
        # Prepare test data
        video_file = self.create_test_video_file()
        form_data = {
            "title": "Test Video Title"
        }
        
        # Make request
        response = client.post(
            "/api/videos/upload",
            files=[video_file],
            headers=auth_headers,
            data=form_data
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "task_id" in data
        assert data["message"] == "Video subido correctamente. Procesamiento en curso."
        assert data["task_id"] == "test-task-123"
        
        # Verify service was called with correct parameters
        mock_process_upload.assert_called_once()
        call_args = mock_process_upload.call_args
        uploaded_file = call_args[0][0]  # First argument (file)
        title = call_args[0][1]  # Second argument (title)
        
        assert title == "Test Video Title"
        assert uploaded_file.filename == "test_video.mp4"
        assert uploaded_file.content_type == "video/mp4"
    
    @patch('services.video_service.video_service.process_video_upload')
    def test_upload_video_with_special_characters_in_title(self, mock_process_upload, auth_headers):
        """Test video upload with special characters in title"""
        mock_response = VideoUploadResponse(
            message="Video subido correctamente. Procesamiento en curso.",
            task_id="test-task-456"
        )
        mock_process_upload.return_value = mock_response
        
        video_file = self.create_test_video_file()
        form_data = {
            "title": "Título con ñ y acentós! @#$%"
        }
        
        response = client.post(
            "/api/videos/upload",
            files=[video_file],
            headers=auth_headers,
            data=form_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-456"
        
        # Verify service received the title correctly
        mock_process_upload.assert_called_once()
        call_args = mock_process_upload.call_args
        title = call_args[0][1]
        assert title == "Título con ñ y acentós! @#$%"
    
    def test_upload_video_missing_file(self, auth_headers):
        """Test upload without file parameter"""
        form_data = {
            "title": "Test Video Title"
        }
        
        response = client.post(
            "/api/videos/upload",
            data=form_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    def test_upload_video_missing_title(self, auth_headers):
        """Test upload without title parameter"""
        video_file = self.create_test_video_file()
        
        response = client.post(
            "/api/videos/upload",
            headers=auth_headers,
            files=[video_file]
        )
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    def test_upload_video_empty_title(self, auth_headers):
        """Test upload with empty title"""
        video_file = self.create_test_video_file()
        form_data = {
            "title": ""
        }
        
        with patch('services.video_service.video_service.process_video_upload') as mock_process:
            mock_process.side_effect = HTTPException(
                status_code=400, 
                detail="El título del video no puede estar vacío."
            )
            
            response = client.post(
                "/api/videos/upload",
                files=[video_file],
                headers=auth_headers,
                data=form_data
            )
            
            # Empty title should trigger service validation, which returns 400
            # But if FastAPI form validation catches it first, it returns 422
            assert response.status_code in [400, 422]
            data = response.json()
            # Check that some validation error occurred
            assert "detail" in data
    
    def test_upload_video_whitespace_only_title(self, auth_headers):
        """Test upload with whitespace-only title"""
        video_file = self.create_test_video_file()
        form_data = {
            "title": "   \t\n   "
        }
        
        with patch('services.video_service.video_service.process_video_upload') as mock_process:
            mock_process.side_effect = HTTPException(
                status_code=400, 
                detail="El título del video no puede estar vacío."
            )
            
            response = client.post(
                "/api/videos/upload",
                files=[video_file],
                headers=auth_headers,
                data=form_data
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["detail"] == "El título del video no puede estar vacío."
    
    def test_upload_invalid_file_type(self, auth_headers):
        """Test upload with non-video file"""
        # Create a text file instead of video
        text_file = ("file", ("document.txt", io.BytesIO(b"not a video"), "text/plain"))
        form_data = {
            "title": "Test Video Title"
        }
        
        with patch('services.video_service.video_service.process_video_upload') as mock_process:
            mock_process.side_effect = HTTPException(
                status_code=400, 
                detail="Tipo de archivo inválido. Se requiere un archivo de video."
            )
            
            response = client.post(
                "/api/videos/upload",
                files=[text_file],
                data=form_data,
                headers=auth_headers
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["detail"] == "Tipo de archivo inválido. Se requiere un archivo de video."
    
    def test_upload_video_too_short(self, auth_headers):
        """Test upload with video shorter than minimum duration"""
        video_file = self.create_test_video_file()
        form_data = {
            "title": "Short Video"
        }
        
        with patch('services.video_service.video_service.process_video_upload') as mock_process:
            mock_process.side_effect = HTTPException(
                status_code=400, 
                detail="El video debe tener una duración entre 20 y 60 segundos."
            )
            
            response = client.post(
                "/api/videos/upload",
                files=[video_file],
                data=form_data,
                headers=auth_headers
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["detail"] == "El video debe tener una duración entre 20 y 60 segundos."
    
    def test_upload_video_too_long(self, auth_headers):
        """Test upload with video longer than maximum duration"""
        video_file = self.create_test_video_file()
        form_data = {
            "title": "Long Video"
        }
        
        with patch('services.video_service.video_service.process_video_upload') as mock_process:
            mock_process.side_effect = HTTPException(
                status_code=400, 
                detail="El video debe tener una duración entre 20 y 60 segundos."
            )
            
            response = client.post(
                "/api/videos/upload",
                files=[video_file],
                headers=auth_headers,
                data=form_data
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["detail"] == "El video debe tener una duración entre 20 y 60 segundos."
    
    def test_upload_video_processing_error(self, auth_headers):
        """Test upload with video processing error"""
        video_file = self.create_test_video_file()
        form_data = {
            "title": "Corrupted Video"
        }
        
        with patch('services.video_service.video_service.process_video_upload') as mock_process:
            mock_process.side_effect = HTTPException(
                status_code=500, 
                detail="Error al procesar el archivo de video."
            )
            
            response = client.post(
                "/api/videos/upload",
                files=[video_file],
                headers=auth_headers,
                data=form_data
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["detail"] == "Error al procesar el archivo de video."
    
    def test_upload_video_nextcloud_error(self, auth_headers):
        """Test upload with Nextcloud storage error"""
        video_file = self.create_test_video_file()
        form_data = {
            "title": "Test Video"
        }
        
        with patch('services.video_service.video_service.process_video_upload') as mock_process:
            mock_process.side_effect = HTTPException(
                status_code=500, 
                detail="Failed to upload video to storage service."
            )
            
            response = client.post(
                "/api/videos/upload",
                files=[video_file],
                headers=auth_headers,
                data=form_data
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["detail"] == "Failed to upload video to storage service."
    
    @patch('services.video_service.video_service.process_video_upload')
    def test_upload_video_different_file_extensions(self, mock_process_upload, auth_headers):
        """Test upload with different video file extensions"""
        mock_response = VideoUploadResponse(
            message="Video subido correctamente. Procesamiento en curso.",
            task_id="test-task-789"
        )
        mock_process_upload.return_value = mock_response
        
        # Test different video file types
        video_files = [
            self.create_test_video_file("test.mp4", "video/mp4"),
            self.create_test_video_file("test.avi", "video/x-msvideo"),
            self.create_test_video_file("test.mov", "video/quicktime"),
            self.create_test_video_file("test.mkv", "video/x-matroska"),
        ]
        
        for video_file in video_files:
            form_data = {"title": f"Test Video {video_file[1][0]}"}
            
            response = client.post(
                "/api/videos/upload",
                files=[video_file],
                headers=auth_headers,
                data=form_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-789"
    
    @patch('services.video_service.video_service.process_video_upload')
    def test_upload_video_large_file(self, mock_process_upload, auth_headers):
        """Test upload with large video file"""
        mock_response = VideoUploadResponse(
            message="Video subido correctamente. Procesamiento en curso.",
            task_id="test-task-large"
        )
        mock_process_upload.return_value = mock_response
        
        # Create a larger fake video file (1MB of fake data)
        large_content = b"fake video data" * 70000  # ~1MB
        video_file = self.create_test_video_file(
            "large_video.mp4", 
            "video/mp4", 
            large_content
        )
        form_data = {
            "title": "Large Video File"
        }
        
        response = client.post(
            "/api/videos/upload",
            files=[video_file],
            headers=auth_headers,
            data=form_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-large"
    
    @patch('services.video_service.video_service.process_video_upload')
    def test_upload_video_unicode_filename(self, mock_process_upload, auth_headers):
        """Test upload with unicode characters in filename"""
        mock_response = VideoUploadResponse(
            message="Video subido correctamente. Procesamiento en curso.",
            task_id="test-task-unicode"
        )
        mock_process_upload.return_value = mock_response
        
        video_file = self.create_test_video_file("vídeo_test_ñ.mp4", "video/mp4")
        form_data = {
            "title": "Unicode Filename Test"
        }
        
        response = client.post(
            "/api/videos/upload",
            files=[video_file],
            headers=auth_headers,
            data=form_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-unicode"
        
        # Verify the filename was handled correctly
        mock_process_upload.assert_called_once()
        call_args = mock_process_upload.call_args
        uploaded_file = call_args[0][0]
        assert uploaded_file.filename == "vídeo_test_ñ.mp4"


class TestVideoEndpointsIntegration:
    """Integration tests for video endpoints"""
    
    @patch('services.video_service.VideoService.post_message_to_sqs')
    @patch('services.video_service.VideoService.upload_to_nextcloud')
    @patch('services.video_service.VideoService.validate_video_properties')
    def test_upload_video_full_flow_mock(self, mock_validate, mock_upload, mock_post_message_to_sqs, auth_headers):
        """Test the full upload flow with mocked external dependencies"""
        # Mock video validation to return valid properties
        mock_validate.return_value = {"duration": 30.0}
        
        # Mock Nextcloud upload to return success
        mock_upload.return_value = "/raw/Test Video Title"
        
        video_file = ("file", ("test_video.mp4", io.BytesIO(b"fake video content"), "video/mp4"))
        form_data = {
            "title": "Integration Test Video"
        }
        
        response = client.post(
            "/api/videos/upload",
            files=[video_file],
            headers=auth_headers,
            data=form_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "task_id" in data
        assert data["message"] == "Video subido correctamente. Procesamiento en curso."
        
        # Verify mocks were called
        mock_validate.assert_called_once()
        mock_upload.assert_called_once()


class TestVideoEndpointsErrorHandling:
    """Tests for error handling in video endpoints"""
    
    def test_upload_video_malformed_request(self, auth_headers):
        """Test upload with malformed request data"""
        # Send invalid multipart data
        headers = auth_headers
        headers["Content-Type"] = "application/json"
        response = client.post(
            "/api/videos/upload",
            headers=headers,
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422
    
    @patch('services.video_service.video_service.process_video_upload')
    def test_upload_video_service_http_exception(self, mock_process_upload, auth_headers):
        """Test handling of HTTP exceptions from service"""
        # Mock an HTTP exception (which should be properly handled)
        mock_process_upload.side_effect = HTTPException(
            status_code=503, 
            detail="Service temporarily unavailable"
        )
        
        video_file = ("file", ("test_video.mp4", io.BytesIO(b"fake video content"), "video/mp4"))
        form_data = {
            "title": "Test Video"
        }
        
        response = client.post(
            "/api/videos/upload",
            files=[video_file],
            headers=auth_headers,
            data=form_data
        )
        
        # HTTP exceptions should be properly handled by FastAPI
        assert response.status_code == 503
        data = response.json()
        assert data["detail"] == "Service temporarily unavailable"
    
    def test_upload_video_empty_file(self, auth_headers):
        """Test upload with empty file"""
        empty_file = ("file", ("empty.mp4", io.BytesIO(b""), "video/mp4"))
        form_data = {
            "title": "Empty File Test"
        }
        
        with patch('services.video_service.video_service.process_video_upload') as mock_process:
            mock_process.side_effect = HTTPException(
                status_code=400, 
                detail="Error al procesar el archivo de video."
            )
            
            response = client.post(
                "/api/videos/upload",
                headers=auth_headers,
                files=[empty_file],
                data=form_data
            )
            
            assert response.status_code == 400


class TestVideoListEndpoint:
    """Tests for GET /api/videos/ - List user videos"""
    
    @patch('services.video_service.video_service.get_videos_for_user')
    def test_list_user_videos_success(self, mock_get_videos, auth_headers):
        """Test successful retrieval of user videos"""
        from datetime import datetime
        import uuid
        
        # Mock video data
        mock_video1 = MagicMock()
        mock_video1.id = uuid.uuid4()
        mock_video1.title = "Video 1"
        mock_video1.status = "processed"
        mock_video1.uploaded_at = datetime.now()
        mock_video1.processed_at = datetime.now()
        mock_video1.processed_url = "https://example.com/processed1.mp4"
        mock_video1.votes = 5
        
        mock_video2 = MagicMock()
        mock_video2.id = uuid.uuid4()
        mock_video2.title = "Video 2"
        mock_video2.status = "uploaded"
        mock_video2.uploaded_at = datetime.now()
        mock_video2.processed_at = None
        mock_video2.processed_url = None
        mock_video2.votes = 0
        
        mock_get_videos.return_value = [mock_video1, mock_video2]
        
        response = client.get("/api/videos/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["title"] == "Video 1"
        assert data[0]["status"] == "processed"
        assert data[0]["votes"] == 5
        assert data[0]["processed_url"] == "https://example.com/processed1.mp4"
        
        assert data[1]["title"] == "Video 2"
        assert data[1]["status"] == "uploaded"
        assert data[1]["votes"] == 0
        
        mock_get_videos.assert_called_once()
    
    @patch('services.video_service.video_service.get_videos_for_user')
    def test_list_user_videos_empty_list(self, mock_get_videos, auth_headers):
        """Test retrieval when user has no videos"""
        mock_get_videos.return_value = []
        
        response = client.get("/api/videos/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
        mock_get_videos.assert_called_once()
    
    def test_list_user_videos_unauthorized(self):
        """Test list videos without authentication"""
        response = client.get("/api/videos/")
        
        assert response.status_code in [401, 403]  # Could be 401 (Unauthorized) or 403 (Forbidden)
        data = response.json()
        assert "detail" in data
    
    @patch('services.video_service.video_service.get_videos_for_user')
    def test_list_user_videos_service_error(self, mock_get_videos, auth_headers):
        """Test list videos with service error"""
        mock_get_videos.side_effect = HTTPException(status_code=500, detail="Database error")
        
        response = client.get("/api/videos/", headers=auth_headers)
        
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Database error"


class TestVideoDetailsEndpoint:
    """Tests for GET /api/videos/{video_id} - Get video details"""
    
    @patch('services.video_service.video_service.get_video_by_id')
    def test_get_video_details_success(self, mock_get_video, auth_headers):
        """Test successful video details retrieval"""
        from datetime import datetime
        import uuid
        
        video_id = str(uuid.uuid4())
        
        mock_video = MagicMock()
        mock_video.id = uuid.UUID(video_id)
        mock_video.title = "Test Video Details"
        mock_video.status = "processed"
        mock_video.uploaded_at = datetime.now()
        mock_video.processed_at = datetime.now()
        mock_video.processed_url = "https://example.com/processed.mp4"
        mock_video.votes = 10
        
        mock_get_video.return_value = mock_video
        
        response = client.get(f"/api/videos/{video_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["video_id"] == video_id
        assert data["title"] == "Test Video Details"
        assert data["status"] == "processed"
        assert data["votes"] == 10
        assert data["processed_url"] == "https://example.com/processed.mp4"
        
        mock_get_video.assert_called_once()
    
    @patch('services.video_service.video_service.get_video_by_id')
    def test_get_video_details_not_found(self, mock_get_video, auth_headers):
        """Test video details when video not found"""
        import uuid
        
        video_id = str(uuid.uuid4())
        mock_get_video.return_value = None
        
        response = client.get(f"/api/videos/{video_id}", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Video not found"
        mock_get_video.assert_called_once()
    
    def test_get_video_details_unauthorized(self):
        """Test get video details without authentication"""
        import uuid
        
        video_id = str(uuid.uuid4())
        response = client.get(f"/api/videos/{video_id}")
        
        assert response.status_code in [401, 403]  # Could be 401 (Unauthorized) or 403 (Forbidden)
        data = response.json()
        assert "detail" in data
    
    def test_get_video_details_invalid_uuid(self, auth_headers):
        """Test get video details with invalid UUID format"""
        invalid_id = "not-a-uuid"
        
        response = client.get(f"/api/videos/{invalid_id}", headers=auth_headers)
        
        # Should either return 422 (validation error) or 404 (not found)
        assert response.status_code in [404, 422, 400]


class TestVideoDeleteEndpoint:
    """Tests for DELETE /api/videos/{video_id} - Delete video"""
    
    @patch('services.video_service.video_service.delete_video')
    def test_delete_video_success(self, mock_delete_video, auth_headers):
        """Test successful video deletion"""
        import uuid
        
        video_id = str(uuid.uuid4())
        mock_delete_video.return_value = True  # Service returns True on success
        
        response = client.delete(f"/api/videos/{video_id}", headers=auth_headers)
        
        assert response.status_code == 204
        mock_delete_video.assert_called_once()
    
    @patch('services.video_service.video_service.delete_video')
    def test_delete_video_not_found(self, mock_delete_video, auth_headers):
        """Test delete video when video not found"""
        import uuid
        
        video_id = str(uuid.uuid4())
        # Service raises HTTPException for not found
        mock_delete_video.side_effect = HTTPException(status_code=404, detail="Video not found")
        
        response = client.delete(f"/api/videos/{video_id}", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Video not found"
        mock_delete_video.assert_called_once()
    
    def test_delete_video_unauthorized(self):
        """Test delete video without authentication"""
        import uuid
        
        video_id = str(uuid.uuid4())
        response = client.delete(f"/api/videos/{video_id}")
        
        assert response.status_code in [401, 403]  # Could be 401 (Unauthorized) or 403 (Forbidden)
        data = response.json()
        assert "detail" in data
    
    def test_delete_video_invalid_uuid(self, auth_headers):
        """Test delete video with invalid UUID format"""
        invalid_id = "not-a-uuid"
        
        response = client.delete(f"/api/videos/{invalid_id}", headers=auth_headers)
        
        # Should either return 422 (validation error) or 404 (not found)
        assert response.status_code in [404, 422, 400]
    
    @patch('services.video_service.video_service.delete_video')
    def test_delete_video_service_error(self, mock_delete_video, auth_headers):
        """Test delete video with service error"""
        import uuid
        
        video_id = str(uuid.uuid4())
        mock_delete_video.side_effect = HTTPException(status_code=403, detail="Cannot delete video")
        
        response = client.delete(f"/api/videos/{video_id}", headers=auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Cannot delete video"

    class TestPublicVideoEndpoint:

        def test_list_public_videos(self):
            """Test retrieval of published videos"""
            with patch('services.video_service.VideoService.get_published_videos') as mock_get_published_videos:
                # Mock published video records
                mock_video_1 = MagicMock()
                mock_video_1.id = uuid.uuid4()
                mock_video_1.title = "Public Video 1"
                mock_video_1.status = "published"
                mock_video_1.uploaded_at = "2024-01-10T12:00:00Z"
                mock_video_1.votes = 20
                
                mock_video_2 = MagicMock()
                mock_video_2.id = uuid.uuid4()
                mock_video_2.title = "Public Video 2"
                mock_video_2.status = "published"
                mock_video_2.uploaded_at = "2024-01-11T12:00:00Z"
                mock_video_2.votes = 30
                
                mock_get_published_videos.return_value = [mock_video_1, mock_video_2]
                
                response = client.get("/api/public/videos")
                
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 2
                
                first_video = data[0]
                assert first_video["video_id"] == str(mock_video_1.id)
                assert first_video["title"] == "Public Video 1"
                assert first_video["status"] == "published"
                assert first_video["uploaded_at"] == "2024-01-10T12:00:00Z"
                assert first_video["votes"] == 20
                
                second_video = data[1]
                assert second_video["video_id"] == str(mock_video_2.id)
                assert second_video["title"] == "Public Video 2"
                assert second_video["status"] == "published"
                assert second_video["uploaded_at"] == "2024-01-11T12:00:00Z"
                assert second_video["votes"] == 30
    
        def test_list_public_videos_case_no_videos(self):
            """Test retrieval when no published videos exist"""
            with patch('services.video_service.VideoService.get_published_videos') as mock_get_published_videos:
                mock_get_published_videos.return_value = []
                
                response = client.get("/api/public/videos")
                
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 0